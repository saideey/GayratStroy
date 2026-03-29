"""
Supplier (Ta'minotchilar) Service.
CRUD + qarz/to'lov hisob-kitobi.
"""

from decimal import Decimal
from datetime import date, datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from database.models.supplier import (
    Supplier, SupplierTransaction, SupplierTransactionType,
    SupplierPayment, PurchaseOrder
)
from database.models import User
from database.base import get_tashkent_now


class SupplierService:

    def __init__(self, db: Session):
        self.db = db

    # ──────────────────────────────────────────────
    # CRUD
    # ──────────────────────────────────────────────

    def get_suppliers(
        self,
        q: Optional[str] = None,
        is_active: Optional[bool] = True,
        has_debt: Optional[bool] = None,
        page: int = 1,
        per_page: int = 20,
    ):
        query = self.db.query(Supplier).filter(Supplier.is_deleted == False)

        if is_active is not None:
            query = query.filter(Supplier.is_active == is_active)
        if q:
            like = f"%{q}%"
            query = query.filter(
                Supplier.name.ilike(like) |
                Supplier.phone.ilike(like) |
                Supplier.company_name.ilike(like)
            )
        if has_debt is True:
            # Qarzdorlar: qarzim bor yoki avansim bor (ikkalasi ham "hisob bor")
            query = query.filter(Supplier.current_debt > 0)
        elif has_debt is False:
            query = query.filter(Supplier.current_debt <= 0)

        total = query.count()
        total_debt = self.db.query(
            func.coalesce(func.sum(Supplier.current_debt), 0)
        ).filter(Supplier.is_deleted == False, Supplier.is_active == True).scalar()

        suppliers = query.order_by(Supplier.name).offset((page - 1) * per_page).limit(per_page).all()
        return suppliers, total, (total + per_page - 1) // per_page, total_debt

    def get_supplier(self, supplier_id: int) -> Optional[Supplier]:
        return self.db.query(Supplier).filter(
            Supplier.id == supplier_id,
            Supplier.is_deleted == False
        ).first()

    def create_supplier(self, data: dict, current_user: User) -> Supplier:
        existing = self.db.query(Supplier).filter(
            Supplier.name == data['name'],
            Supplier.is_deleted == False
        ).first()
        if existing:
            raise ValueError(f"'{data['name']}' nomli ta'minotchi allaqachon mavjud")

        supplier = Supplier(**{k: v for k, v in data.items() if v is not None})
        supplier.current_debt = Decimal('0')
        supplier.advance_balance = Decimal('0')
        self.db.add(supplier)
        self.db.commit()
        self.db.refresh(supplier)
        return supplier

    def update_supplier(self, supplier_id: int, data: dict) -> Supplier:
        supplier = self.get_supplier(supplier_id)
        if not supplier:
            raise ValueError("Ta'minotchi topilmadi")

        for k, v in data.items():
            if v is not None:
                setattr(supplier, k, v)

        self.db.commit()
        self.db.refresh(supplier)
        return supplier

    def delete_supplier(self, supplier_id: int, current_user: User):
        supplier = self.get_supplier(supplier_id)
        if not supplier:
            raise ValueError("Ta'minotchi topilmadi")
        if supplier.current_debt and supplier.current_debt > 0:
            raise ValueError(
                f"Ta'minotchida {supplier.current_debt} qarz mavjud. "
                "Avval qarzni to'lang."
            )
        supplier.is_deleted = True
        supplier.deleted_at = get_tashkent_now()
        self.db.commit()

    # ──────────────────────────────────────────────
    # TRANZAKSIYALAR (QARZ / TO'LOV / QAYTARISH)
    # ──────────────────────────────────────────────

    def add_transaction(
        self,
        supplier_id: int,
        transaction_type: str,   # 'debt' | 'payment' | 'return'
        amount: Decimal,
        currency: str,
        comment: str,
        current_user: User,
        transaction_date: Optional[date] = None,
        usd_rate: Optional[Decimal] = None,
        purchase_order_id: Optional[int] = None,
    ) -> SupplierTransaction:
        supplier = self.get_supplier(supplier_id)
        if not supplier:
            raise ValueError("Ta'minotchi topilmadi")
        if not comment or len(comment.strip()) < 3:
            raise ValueError("Izoh kamida 3 ta belgidan iborat bo'lishi kerak")

        # UZS ekvivalent
        amount_uzs = None
        if currency == 'usd' and usd_rate:
            amount_uzs = amount * usd_rate
        elif currency == 'uzs':
            amount_uzs = amount

        tx = SupplierTransaction(
            supplier_id=supplier_id,
            transaction_type=SupplierTransactionType(transaction_type),
            amount=amount,
            currency=currency,
            usd_rate=usd_rate,
            amount_uzs=amount_uzs,
            transaction_date=transaction_date or date.today(),
            comment=comment.strip(),
            purchase_order_id=purchase_order_id,
            created_by_id=current_user.id,
        )
        self.db.add(tx)

        # ── Balans yangilash (to'liq logika) ─────────────────────────────
        uzs_amount = amount_uzs or amount
        current_debt = supplier.current_debt or Decimal('0')
        current_advance = supplier.advance_balance or Decimal('0')

        if transaction_type == 'debt':
            # Qarz qo'shish:
            # Avval avans bilan qoplaymiz, qolganini qarzga yozamiz
            if current_advance >= uzs_amount:
                # Avans yetarli — qarzni avansdan yopamiz
                supplier.advance_balance = current_advance - uzs_amount
            else:
                # Avans yetarli emas
                remaining_debt = uzs_amount - current_advance
                supplier.advance_balance = Decimal('0')
                supplier.current_debt = current_debt + remaining_debt

        elif transaction_type in ('payment', 'return'):
            # To'lov yoki qaytarish:
            # Avval qarzni kamaytirамiz, ortiqcha summa avansga o'tadi
            if uzs_amount <= current_debt:
                # To'lov qarzdan kam yoki teng
                supplier.current_debt = current_debt - uzs_amount
            else:
                # To'lov qarzdan ko'p — ortiqcha avansga o'tadi
                overpayment = uzs_amount - current_debt
                supplier.current_debt = Decimal('0')
                supplier.advance_balance = current_advance + overpayment

        self.db.commit()
        self.db.refresh(tx)
        return tx

    def delete_transaction(
        self,
        transaction_id: int,
        delete_comment: str,
        current_user: User,
    ):
        tx = self.db.query(SupplierTransaction).filter(
            SupplierTransaction.id == transaction_id,
            SupplierTransaction.is_deleted == False
        ).first()
        if not tx:
            raise ValueError("Tranzaksiya topilmadi")
        if not delete_comment or len(delete_comment.strip()) < 3:
            raise ValueError("O'chirish izohi majburiy (kamida 3 ta belgi)")

        supplier = self.get_supplier(tx.supplier_id)

        # ── Balansni teskari qaytarish ────────────────────────────────────
        uzs_amount = tx.amount_uzs or tx.amount
        current_debt = supplier.current_debt or Decimal('0')
        current_advance = supplier.advance_balance or Decimal('0')

        if tx.transaction_type == SupplierTransactionType.DEBT:
            # Qarz o'chirildi — agar avansdan qoplangan bo'lsa uni qaytaramiz
            # Avans bo'lsa, uni qarzga aylantiramiz (teskari)
            if current_advance > 0:
                restore_to_debt = min(current_advance, uzs_amount)
                supplier.advance_balance = current_advance - restore_to_debt
                supplier.current_debt = current_debt + (uzs_amount - restore_to_debt)
            else:
                supplier.current_debt = current_debt + uzs_amount

        elif tx.transaction_type in (SupplierTransactionType.PAYMENT, SupplierTransactionType.RETURN):
            # To'lov o'chirildi — avans bo'lsa, uni kamaytirамiz
            if current_advance >= uzs_amount:
                supplier.advance_balance = current_advance - uzs_amount
            else:
                # Avansdan ortiq qismi qarzga qaytadi
                remaining = uzs_amount - current_advance
                supplier.advance_balance = Decimal('0')
                supplier.current_debt = current_debt + remaining

        tx.is_deleted = True
        tx.deleted_at = get_tashkent_now()
        tx.deleted_by_id = current_user.id
        tx.delete_comment = delete_comment.strip()

        self.db.commit()

    def get_transactions(
        self,
        supplier_id: int,
        include_deleted: bool = False,
        transaction_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        per_page: int = 30,
    ):
        query = self.db.query(SupplierTransaction).filter(
            SupplierTransaction.supplier_id == supplier_id
        )
        if not include_deleted:
            query = query.filter(SupplierTransaction.is_deleted == False)
        if transaction_type:
            query = query.filter(
                SupplierTransaction.transaction_type == SupplierTransactionType(transaction_type)
            )
        if start_date:
            query = query.filter(SupplierTransaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(SupplierTransaction.transaction_date <= end_date)

        total = query.count()

        # Summary
        debt_sum = self.db.query(
            func.coalesce(func.sum(SupplierTransaction.amount_uzs), 0)
        ).filter(
            SupplierTransaction.supplier_id == supplier_id,
            SupplierTransaction.is_deleted == False,
            SupplierTransaction.transaction_type == SupplierTransactionType.DEBT
        ).scalar() or Decimal('0')

        payment_sum = self.db.query(
            func.coalesce(func.sum(SupplierTransaction.amount_uzs), 0)
        ).filter(
            SupplierTransaction.supplier_id == supplier_id,
            SupplierTransaction.is_deleted == False,
            SupplierTransaction.transaction_type.in_([
                SupplierTransactionType.PAYMENT,
                SupplierTransactionType.RETURN
            ])
        ).scalar() or Decimal('0')

        txs = query.order_by(
            SupplierTransaction.transaction_date.desc(),
            SupplierTransaction.id.desc()
        ).offset((page - 1) * per_page).limit(per_page).all()

        return (
            [self._format_tx(t) for t in txs],
            total,
            (total + per_page - 1) // per_page,
            {"total_debt": debt_sum, "total_paid": payment_sum}
        )

    # ──────────────────────────────────────────────
    # FORMAT HELPERS
    # ──────────────────────────────────────────────

    def format_supplier(self, s: Supplier) -> dict:
        debt = s.current_debt or Decimal('0')
        advance = s.advance_balance or Decimal('0')
        return {
            "id": s.id,
            "name": s.name,
            "company_name": s.company_name,
            "contact_person": s.contact_person,
            "phone": s.phone,
            "phone_secondary": s.phone_secondary,
            "email": s.email,
            "address": s.address,
            "city": s.city,
            "inn": s.inn,
            # Qarz va avans — ikkalasi alohida
            "current_debt": debt,
            "advance_balance": advance,
            # Sof balans: minus = biz ularga qarzlimiz, plus = ular bizga qarzli
            "net_balance": advance - debt,
            "balance_type": "advance" if advance > 0 and debt == 0 else ("debt" if debt > 0 else "zero"),
            "rating": s.rating,
            "is_active": s.is_active,
            "notes": s.notes,
            "created_at": s.created_at,
        }

    def _format_tx(self, t: SupplierTransaction) -> dict:
        return {
            "id": t.id,
            "supplier_id": t.supplier_id,
            "transaction_type": t.transaction_type.value,
            "amount": t.amount,
            "currency": t.currency,
            "usd_rate": t.usd_rate,
            "amount_uzs": t.amount_uzs,
            "transaction_date": t.transaction_date,
            "comment": t.comment,
            "purchase_order_id": t.purchase_order_id,
            "created_by_id": t.created_by_id,
            "created_by_name": (
                f"{t.created_by.first_name} {t.created_by.last_name}"
                if t.created_by else ""
            ),
            "is_deleted": t.is_deleted,
            "deleted_at": t.deleted_at,
            "deleted_by_name": (
                f"{t.deleted_by.first_name} {t.deleted_by.last_name}"
                if t.deleted_by else None
            ),
            "delete_comment": t.delete_comment,
            "created_at": t.created_at,
        }

    def get_supplier_stats(
        self,
        supplier_id: int,
        start_date=None,
        end_date=None,
    ) -> dict:
        """
        Ta'minotchi to'liq statistikasi.
        - start_date/end_date berilsa — o'sha oraliqda
        - Berilmasa — butun umrboqiy
        """
        from database.models.warehouse import StockMovement, MovementType
        from sqlalchemy import or_
        import datetime

        supplier = self.get_supplier(supplier_id)
        if not supplier:
            raise ValueError("Ta'minotchi topilmadi")

        # ── Tranzaksiya filtri ────────────────────────────────────────────────
        tx_query = self.db.query(SupplierTransaction).filter(
            SupplierTransaction.supplier_id == supplier_id,
            SupplierTransaction.is_deleted == False
        )
        if start_date:
            tx_query = tx_query.filter(SupplierTransaction.transaction_date >= start_date)
        if end_date:
            tx_query = tx_query.filter(SupplierTransaction.transaction_date <= end_date)

        all_txs = tx_query.order_by(SupplierTransaction.transaction_date.desc()).all()

        tx_count = len(all_txs)
        total_debt_written = sum(
            float(t.amount_uzs or t.amount) for t in all_txs
            if t.transaction_type == SupplierTransactionType.DEBT
        )
        total_paid = sum(
            float(t.amount_uzs or t.amount) for t in all_txs
            if t.transaction_type in (SupplierTransactionType.PAYMENT, SupplierTransactionType.RETURN)
        )
        last_tx = all_txs[0] if all_txs else None

        # ── Ombor kirimlari ───────────────────────────────────────────────────
        try:
            mv_query = self.db.query(StockMovement).filter(
                StockMovement.movement_type == MovementType.PURCHASE,
                StockMovement.is_deleted == False,
                or_(
                    StockMovement.supplier_id == supplier_id,
                    StockMovement.supplier_name == supplier.name
                )
            )
        except Exception:
            mv_query = self.db.query(StockMovement).filter(
                StockMovement.movement_type == MovementType.PURCHASE,
                StockMovement.is_deleted == False,
                StockMovement.supplier_name == supplier.name
            )

        if start_date:
            mv_query = mv_query.filter(StockMovement.created_at >= datetime.datetime.combine(start_date, datetime.time.min))
        if end_date:
            mv_query = mv_query.filter(StockMovement.created_at <= datetime.datetime.combine(end_date, datetime.time.max))

        movements = mv_query.order_by(StockMovement.created_at.desc()).all()

        # Hujjatlar bo'yicha guruhlash
        purchases_by_doc: dict = {}
        for m in movements:
            doc_key = m.document_number or f"_id_{m.id}"
            if doc_key not in purchases_by_doc:
                mv_date = None
                if m.created_at:
                    mv_date = m.created_at.date() if hasattr(m.created_at, 'date') else m.created_at
                purchases_by_doc[doc_key] = {
                    "document_number": m.document_number or "—",
                    "date": str(mv_date) if mv_date else None,
                    "items": [], "total_amount": 0.0, "items_count": 0.0,
                }
            purchases_by_doc[doc_key]["items"].append({
                "product_name": m.product.name if m.product else f"#{m.product_id}",
                "quantity": float(m.quantity or 0),
                "uom_symbol": m.uom.symbol if m.uom else "dona",
                "unit_cost": float(m.unit_cost or 0),
                "total_cost": float(m.total_cost or 0),
            })
            purchases_by_doc[doc_key]["total_amount"] += float(m.total_cost or 0)
            purchases_by_doc[doc_key]["items_count"] += float(m.quantity or 0)

        purchase_docs = list(purchases_by_doc.values())
        purchase_count = len(purchase_docs)
        total_purchase_amount = sum(d["total_amount"] for d in purchase_docs)
        total_items_received = sum(float(m.quantity or 0) for m in movements)
        unique_products = len(set(m.product_id for m in movements))

        # Top mahsulotlar
        products_map: dict = {}
        for m in movements:
            pid = m.product_id
            if pid not in products_map:
                products_map[pid] = {
                    "product_id": pid,
                    "product_name": m.product.name if m.product else f"#{pid}",
                    "total_quantity": 0.0, "total_amount": 0.0,
                    "uom_symbol": m.uom.symbol if m.uom else "dona",
                    "times_ordered": 0,
                }
            products_map[pid]["total_quantity"] += float(m.quantity or 0)
            products_map[pid]["total_amount"] += float(m.total_cost or 0)
            products_map[pid]["times_ordered"] += 1

        top_products = sorted(products_map.values(), key=lambda x: x["total_amount"], reverse=True)[:15]

        # ── Oylik dinamika (filter bo'yicha YOKI butun umr) ───────────────────
        monthly_map: dict = {}
        for t in all_txs:
            key = (t.transaction_date.year, t.transaction_date.month)
            if key not in monthly_map:
                monthly_map[key] = {"debt": 0.0, "paid": 0.0, "tx_count": 0}
            amt = float(t.amount_uzs or t.amount)
            if t.transaction_type == SupplierTransactionType.DEBT:
                monthly_map[key]["debt"] += amt
            else:
                monthly_map[key]["paid"] += amt
            monthly_map[key]["tx_count"] += 1

        monthly = [
            {"year": y, "month": m, "debt": v["debt"], "paid": v["paid"], "tx_count": v["tx_count"]}
            for (y, m), v in sorted(monthly_map.items())
        ]

        # ── Balans hisoblash (joriy holat) ────────────────────────────────────
        current_debt = float(supplier.current_debt or 0)
        current_advance = float(supplier.advance_balance or 0)

        return {
            # Joriy holat (filter ga bog'liq EMAS)
            "current_debt": current_debt,
            "current_advance": current_advance,
            "net_balance": current_advance - current_debt,
            "balance_type": "advance" if current_advance > 0 and current_debt == 0 else (
                "debt" if current_debt > 0 else "zero"
            ),

            # Filter bo'yicha hisob
            "period_debt_written": total_debt_written,
            "period_paid": total_paid,
            "period_net": total_paid - total_debt_written,
            "transaction_count": tx_count,
            "last_transaction_date": str(last_tx.transaction_date) if last_tx else None,
            "last_transaction_type": last_tx.transaction_type.value if last_tx else None,
            "last_transaction_amount": float(last_tx.amount_uzs or last_tx.amount) if last_tx else 0,

            # Kirimlar (filter bo'yicha)
            "purchase_count": purchase_count,
            "unique_products": unique_products,
            "total_items_received": round(total_items_received, 2),
            "total_purchase_amount": round(total_purchase_amount, 2),
            "purchase_docs": purchase_docs[:30],
            "top_products": top_products,

            # Oylik grafik (filter bo'yicha)
            "monthly": monthly,

            # Filter ma'lumotlari
            "filter_start": str(start_date) if start_date else None,
            "filter_end": str(end_date) if end_date else None,
        }

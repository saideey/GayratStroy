"""
Expense (Chiqimlar) Service.
Barcha biznes logika shu yerda.
"""

from decimal import Decimal
from datetime import date, datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from database.models.expense import (
    Expense, ExpenseCategory, ExpenseEditLog,
    ExpenseCurrencyType, ExpenseEditAction
)
from database.models import User
from database.base import get_tashkent_now
from schemas.expense import (
    ExpenseCreate, ExpenseUpdate, ExpenseCategoryCreate,
    ExpenseCategoryUpdate
)


class ExpenseService:
    """Chiqimlar bilan ishlash uchun service."""

    def __init__(self, db: Session):
        self.db = db

    # ─────────────────────────────────────────
    # KATEGORIYALAR
    # ─────────────────────────────────────────

    def get_categories(self, include_inactive: bool = False) -> List[dict]:
        """Barcha kategoriyalarni qaytaradi."""
        query = self.db.query(ExpenseCategory)
        if not include_inactive:
            query = query.filter(ExpenseCategory.is_active == True)
        categories = query.order_by(ExpenseCategory.name).all()
        return [self._format_category(c) for c in categories]

    def get_category(self, category_id: int) -> Optional[ExpenseCategory]:
        return self.db.query(ExpenseCategory).filter(
            ExpenseCategory.id == category_id
        ).first()

    def create_category(self, data: ExpenseCategoryCreate) -> ExpenseCategory:
        """Yangi kategoriya yaratish."""
        # Nom takrorlanishini tekshirish
        existing = self.db.query(ExpenseCategory).filter(
            func.lower(ExpenseCategory.name) == func.lower(data.name)
        ).first()
        if existing:
            raise ValueError(f"'{data.name}' nomli kategoriya allaqachon mavjud")

        category = ExpenseCategory(
            name=data.name,
            description=data.description,
            color=data.color or '#6366f1',
            icon=data.icon,
        )
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def update_category(
        self, category_id: int, data: ExpenseCategoryUpdate
    ) -> ExpenseCategory:
        """Kategoriyani yangilash."""
        category = self.get_category(category_id)
        if not category:
            raise ValueError("Kategoriya topilmadi")

        # Nom takrorlanishini tekshirish
        if data.name:
            existing = self.db.query(ExpenseCategory).filter(
                func.lower(ExpenseCategory.name) == func.lower(data.name),
                ExpenseCategory.id != category_id
            ).first()
            if existing:
                raise ValueError(f"'{data.name}' nomli kategoriya allaqachon mavjud")

        for field, value in data.model_dump(exclude_none=True).items():
            setattr(category, field, value)

        self.db.commit()
        self.db.refresh(category)
        return category

    def delete_category(self, category_id: int) -> bool:
        """Kategoriyani o'chirish (agar chiqimlari bo'lmasa)."""
        category = self.get_category(category_id)
        if not category:
            raise ValueError("Kategoriya topilmadi")

        # Bog'liq aktiv chiqimlar borligini tekshirish
        count = self.db.query(Expense).filter(
            Expense.category_id == category_id,
            Expense.is_deleted == False
        ).count()
        if count > 0:
            raise ValueError(
                f"Bu kategoriyada {count} ta chiqim mavjud. "
                "Avval ularni boshqa kategoriyaga o'tkazing yoki o'chiring."
            )

        # Kategoriyani deaktiv qilish (haqiqiy o'chirish emas)
        category.is_active = False
        self.db.commit()
        return True

    def _format_category(self, c: ExpenseCategory) -> dict:
        return {
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "color": c.color,
            "icon": c.icon,
            "is_active": c.is_active,
            "created_at": c.created_at,
        }

    # ─────────────────────────────────────────
    # CHIQIMLAR
    # ─────────────────────────────────────────

    def create_expense(self, data: ExpenseCreate, current_user: User) -> dict:
        """Yangi chiqim yaratish."""
        # Kategoriya mavjudligini tekshirish
        category = self.get_category(data.category_id)
        if not category or not category.is_active:
            raise ValueError("Kategoriya topilmadi yoki faol emas")

        # UZS ekvivalentini hisoblash
        amount_uzs = None
        if data.currency == 'usd' and data.usd_rate:
            amount_uzs = data.amount * data.usd_rate
        elif data.currency == 'uzs':
            amount_uzs = data.amount

        expense = Expense(
            title=data.title,
            description=data.description,
            amount=data.amount,
            currency=ExpenseCurrencyType(data.currency),
            usd_rate=data.usd_rate,
            amount_uzs=amount_uzs,
            expense_date=data.expense_date,
            category_id=data.category_id,
            created_by_id=current_user.id,
        )
        self.db.add(expense)
        self.db.flush()

        # Audit log - CREATE
        log = ExpenseEditLog(
            expense_id=expense.id,
            changed_by_id=current_user.id,
            action=ExpenseEditAction.CREATED,
            comment="Chiqim yaratildi",
            new_title=data.title,
            new_amount=data.amount,
            new_currency=data.currency,
            new_category_id=data.category_id,
            new_expense_date=data.expense_date,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(expense)
        return self._format_expense(expense)

    def get_expenses(
        self,
        page: int = 1,
        per_page: int = 20,
        category_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        currency: Optional[str] = None,
        include_deleted: bool = False,
    ) -> Tuple[List[dict], int, dict]:
        """Chiqimlar ro'yxatini filter bilan qaytarish."""
        query = self.db.query(Expense)

        if not include_deleted:
            query = query.filter(Expense.is_deleted == False)

        if category_id:
            query = query.filter(Expense.category_id == category_id)
        if start_date:
            query = query.filter(Expense.expense_date >= start_date)
        if end_date:
            query = query.filter(Expense.expense_date <= end_date)
        if currency:
            query = query.filter(Expense.currency == ExpenseCurrencyType(currency))

        total = query.count()

        # Jami summalar
        summary = self._calculate_summary(query)

        # Sahifalash
        offset = (page - 1) * per_page
        expenses = query.order_by(
            Expense.expense_date.desc(), Expense.id.desc()
        ).offset(offset).limit(per_page).all()

        total_pages = (total + per_page - 1) // per_page

        return (
            [self._format_expense(e) for e in expenses],
            total,
            total_pages,
            summary
        )

    def get_expense(self, expense_id: int) -> Optional[dict]:
        """Bitta chiqimni ID bo'yicha qaytarish."""
        expense = self.db.query(Expense).filter(
            Expense.id == expense_id
        ).first()
        if not expense:
            return None
        return self._format_expense(expense, include_logs=True)

    def update_expense(
        self, expense_id: int, data: ExpenseUpdate, current_user: User
    ) -> dict:
        """Chiqimni yangilash — izoh majburiy."""
        expense = self.db.query(Expense).filter(
            Expense.id == expense_id,
            Expense.is_deleted == False
        ).first()
        if not expense:
            raise ValueError("Chiqim topilmadi yoki o'chirilgan")

        # Yangi kategoriya tekshiruvi
        if data.category_id:
            cat = self.get_category(data.category_id)
            if not cat or not cat.is_active:
                raise ValueError("Kategoriya topilmadi yoki faol emas")

        # Eski qiymatlarni saqlash (audit uchun)
        old = {
            "title": expense.title,
            "description": expense.description,
            "amount": expense.amount,
            "currency": expense.currency.value,
            "category_id": expense.category_id,
            "expense_date": expense.expense_date,
        }

        # Yangilash
        update_data = data.model_dump(exclude={'comment'}, exclude_none=True)
        for field, value in update_data.items():
            if field == 'currency':
                setattr(expense, field, ExpenseCurrencyType(value))
            else:
                setattr(expense, field, value)

        # UZS ekvivalentini qayta hisoblash
        curr = data.currency or expense.currency.value
        amt = data.amount or expense.amount
        rate = data.usd_rate or expense.usd_rate
        if curr == 'usd' and rate:
            expense.amount_uzs = amt * rate
        elif curr == 'uzs':
            expense.amount_uzs = amt

        # Audit log - UPDATE
        log = ExpenseEditLog(
            expense_id=expense.id,
            changed_by_id=current_user.id,
            action=ExpenseEditAction.UPDATED,
            comment=data.comment,
            old_title=old["title"],
            old_amount=old["amount"],
            old_currency=old["currency"],
            old_category_id=old["category_id"],
            old_expense_date=old["expense_date"],
            new_title=expense.title,
            new_amount=expense.amount,
            new_currency=expense.currency.value,
            new_category_id=expense.category_id,
            new_expense_date=expense.expense_date,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(expense)
        return self._format_expense(expense, include_logs=True)

    def delete_expense(
        self, expense_id: int, comment: str, current_user: User
    ) -> dict:
        """Chiqimni soft-delete — izoh majburiy."""
        expense = self.db.query(Expense).filter(
            Expense.id == expense_id,
            Expense.is_deleted == False
        ).first()
        if not expense:
            raise ValueError("Chiqim topilmadi yoki allaqachon o'chirilgan")

        expense.is_deleted = True
        expense.deleted_at = get_tashkent_now()
        expense.deleted_by_id = current_user.id
        expense.delete_comment = comment

        # Audit log - DELETE
        log = ExpenseEditLog(
            expense_id=expense.id,
            changed_by_id=current_user.id,
            action=ExpenseEditAction.DELETED,
            comment=comment,
            old_title=expense.title,
            old_amount=expense.amount,
            old_currency=expense.currency.value,
            old_category_id=expense.category_id,
            old_expense_date=expense.expense_date,
        )
        self.db.add(log)
        self.db.commit()
        return {"message": "Chiqim muvaffaqiyatli o'chirildi"}

    def restore_expense(self, expense_id: int, current_user: User) -> dict:
        """O'chirilgan chiqimni tiklash."""
        expense = self.db.query(Expense).filter(
            Expense.id == expense_id,
            Expense.is_deleted == True
        ).first()
        if not expense:
            raise ValueError("O'chirilgan chiqim topilmadi")

        expense.is_deleted = False
        expense.deleted_at = None
        expense.deleted_by_id = None
        expense.delete_comment = None

        log = ExpenseEditLog(
            expense_id=expense.id,
            changed_by_id=current_user.id,
            action=ExpenseEditAction.RESTORED,
            comment="Chiqim tiklandi",
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(expense)
        return self._format_expense(expense)

    def get_expense_logs(self, expense_id: int) -> List[dict]:
        """Chiqimning to'liq o'zgartirish tarixini qaytarish."""
        logs = self.db.query(ExpenseEditLog).filter(
            ExpenseEditLog.expense_id == expense_id
        ).order_by(ExpenseEditLog.id.desc()).all()
        return [self._format_log(log) for log in logs]

    # ─────────────────────────────────────────
    # FOYDA HISOBI
    # ─────────────────────────────────────────

    def get_profit_summary(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        """
        Sof foyda hisobi:
        Sof foyda = Sotuv daromadi − Chiqimlar (UZS da)
        """
        from database.models.sale import Sale, PaymentStatus

        # Sotuv daromadi
        sale_query = self.db.query(
            func.coalesce(func.sum(Sale.total_amount), 0)
        ).filter(
            Sale.is_cancelled == False,
            Sale.payment_status.in_([
                PaymentStatus.PAID, PaymentStatus.PARTIAL
            ])
        )
        if start_date:
            sale_query = sale_query.filter(
                func.date(Sale.created_at) >= start_date
            )
        if end_date:
            sale_query = sale_query.filter(
                func.date(Sale.created_at) <= end_date
            )
        total_revenue = sale_query.scalar() or Decimal('0')

        # Chiqimlar (faqat UZS ekvivalenti)
        expense_query = self.db.query(
            func.coalesce(func.sum(Expense.amount_uzs), 0)
        ).filter(Expense.is_deleted == False)
        if start_date:
            expense_query = expense_query.filter(
                Expense.expense_date >= start_date
            )
        if end_date:
            expense_query = expense_query.filter(
                Expense.expense_date <= end_date
            )
        total_expenses = expense_query.scalar() or Decimal('0')

        # Kategoriya bo'yicha chiqimlar
        cat_query = self.db.query(
            ExpenseCategory.id,
            ExpenseCategory.name,
            ExpenseCategory.color,
            func.coalesce(func.sum(Expense.amount_uzs), 0).label('total'),
            func.count(Expense.id).label('count')
        ).join(
            Expense, and_(
                Expense.category_id == ExpenseCategory.id,
                Expense.is_deleted == False
            ), isouter=True
        )
        if start_date:
            cat_query = cat_query.filter(
                or_(Expense.expense_date == None, Expense.expense_date >= start_date)
            )
        if end_date:
            cat_query = cat_query.filter(
                or_(Expense.expense_date == None, Expense.expense_date <= end_date)
            )
        cat_query = cat_query.filter(
            ExpenseCategory.is_active == True
        ).group_by(
            ExpenseCategory.id, ExpenseCategory.name, ExpenseCategory.color
        ).order_by(func.sum(Expense.amount_uzs).desc().nullslast())

        by_category = [
            {
                "category_id": row.id,
                "category_name": row.name,
                "category_color": row.color,
                "total_uzs": row.total,
                "count": row.count,
            }
            for row in cat_query.all()
        ]

        net_profit = Decimal(str(total_revenue)) - Decimal(str(total_expenses))

        return {
            "total_revenue": total_revenue,
            "total_expenses": total_expenses,
            "net_profit": net_profit,
            "profit_margin": (
                round((net_profit / Decimal(str(total_revenue))) * 100, 2)
                if total_revenue > 0 else Decimal('0')
            ),
            "by_category": by_category,
        }

    # ─────────────────────────────────────────
    # YORDAMCHI METODLAR
    # ─────────────────────────────────────────

    def _calculate_summary(self, query) -> dict:
        """Filtr bo'yicha jami summalarni hisoblash."""
        uzs_total = self.db.query(
            func.coalesce(func.sum(Expense.amount_uzs), 0)
        ).filter(
            Expense.id.in_(query.with_entities(Expense.id))
        ).scalar() or Decimal('0')

        usd_q = self.db.query(
            func.coalesce(func.sum(Expense.amount), 0)
        ).filter(
            Expense.id.in_(query.with_entities(Expense.id)),
            Expense.currency == ExpenseCurrencyType.USD
        ).scalar() or Decimal('0')

        uzs_q = self.db.query(
            func.coalesce(func.sum(Expense.amount), 0)
        ).filter(
            Expense.id.in_(query.with_entities(Expense.id)),
            Expense.currency == ExpenseCurrencyType.UZS
        ).scalar() or Decimal('0')

        return {
            "total_uzs": uzs_q,
            "total_usd": usd_q,
            "total_uzs_equivalent": uzs_total,
        }

    def _format_expense(self, e: Expense, include_logs: bool = False) -> dict:
        result = {
            "id": e.id,
            "title": e.title,
            "description": e.description,
            "amount": e.amount,
            "currency": e.currency.value,
            "usd_rate": e.usd_rate,
            "amount_uzs": e.amount_uzs,
            "expense_date": e.expense_date,
            "category_id": e.category_id,
            "category_name": e.category.name if e.category else "",
            "category_color": e.category.color if e.category else None,
            "created_by_id": e.created_by_id,
            "created_by_name": (
                f"{e.created_by.first_name} {e.created_by.last_name}"
                if e.created_by else ""
            ),
            "is_deleted": e.is_deleted,
            "deleted_at": e.deleted_at,
            "deleted_by_id": e.deleted_by_id,
            "deleted_by_name": (
                f"{e.deleted_by.first_name} {e.deleted_by.last_name}"
                if e.deleted_by else None
            ),
            "delete_comment": e.delete_comment,
            "created_at": e.created_at,
            "updated_at": e.updated_at,
            "edit_logs": [],
        }
        if include_logs:
            result["edit_logs"] = [self._format_log(log) for log in e.edit_logs]
        return result

    def _format_log(self, log: ExpenseEditLog) -> dict:
        return {
            "id": log.id,
            "action": log.action.value,
            "comment": log.comment,
            "changed_at": log.created_at,
            "changed_by_id": log.changed_by_id,
            "changed_by_name": (
                f"{log.changed_by.first_name} {log.changed_by.last_name}"
                if log.changed_by else ""
            ),
            "old_title": log.old_title,
            "old_amount": log.old_amount,
            "old_currency": log.old_currency,
            "old_category_id": log.old_category_id,
            "old_expense_date": log.old_expense_date,
            "new_title": log.new_title,
            "new_amount": log.new_amount,
            "new_currency": log.new_currency,
            "new_category_id": log.new_category_id,
            "new_expense_date": log.new_expense_date,
        }

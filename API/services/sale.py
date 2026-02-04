"""
Sale management service.
Core business logic for sales with proportional discount distribution.
"""

from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.models import (
    Sale, SaleItem, Payment, SaleReturn, SaleReturnItem,
    Product, Customer, Stock, MovementType,
    PaymentStatus, PaymentType, CustomerType, AuditLog
)
from services.warehouse import StockService
from services.customer import CustomerService
from utils.helpers import NumberGenerator, get_tashkent_now, get_tashkent_today
from services.telegram_notifier import send_purchase_notification_sync


class SaleService:
    """Sale management service with proportional discount."""
    
    def __init__(self, db: Session):
        self.db = db
        self.stock_service = StockService(db)
        self.customer_service = CustomerService(db)
        self.num_gen = NumberGenerator(db)
    
    def get_sale_by_id(self, sale_id: int) -> Optional[Sale]:
        """Get sale by ID with all relationships."""
        return self.db.query(Sale).filter(Sale.id == sale_id).first()
    
    def get_sale_by_number(self, sale_number: str) -> Optional[Sale]:
        """Get sale by sale number."""
        return self.db.query(Sale).filter(Sale.sale_number == sale_number).first()
    
    def get_sales(
        self,
        page: int = 1,
        per_page: int = 20,
        customer_id: int = None,
        seller_id: int = None,
        warehouse_id: int = None,
        payment_status: str = None,
        start_date: date = None,
        end_date: date = None,
        is_cancelled: bool = False
    ) -> Tuple[List[Sale], int, dict]:
        """Get paginated sales list with summary."""
        query = self.db.query(Sale).filter(Sale.is_cancelled == is_cancelled)
        
        if customer_id:
            query = query.filter(Sale.customer_id == customer_id)
        
        if seller_id:
            query = query.filter(Sale.seller_id == seller_id)
        
        if warehouse_id:
            query = query.filter(Sale.warehouse_id == warehouse_id)
        
        if payment_status:
            # String yoki PaymentStatus enum bo'lishi mumkin
            if isinstance(payment_status, str):
                try:
                    payment_status = PaymentStatus(payment_status.lower())
                except ValueError:
                    payment_status = None
            if payment_status:
                query = query.filter(Sale.payment_status == payment_status)
        
        if start_date:
            query = query.filter(Sale.sale_date >= start_date)
        
        if end_date:
            query = query.filter(Sale.sale_date <= end_date)
        
        # Get summary
        summary = {
            "total_amount": query.with_entities(func.sum(Sale.total_amount)).scalar() or Decimal("0"),
            "total_paid": query.with_entities(func.sum(Sale.paid_amount)).scalar() or Decimal("0"),
            "total_debt": query.with_entities(func.sum(Sale.debt_amount)).scalar() or Decimal("0"),
        }
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        sales = query.order_by(Sale.created_at.desc()).offset(offset).limit(per_page).all()
        
        return sales, total, summary
    
    def create_sale(
        self,
        seller_id: int,
        warehouse_id: int,
        items: List[dict],
        customer_id: int = None,
        final_total: Decimal = None,
        payments: List[dict] = None,
        notes: str = None,
        requires_delivery: bool = False,
        delivery_address: str = None,
        delivery_date: date = None,
        delivery_cost: Decimal = Decimal("0")
    ) -> Tuple[Optional[Sale], str]:
        """
        Create new sale with proportional discount distribution.
        
        Key feature: If final_total differs from calculated subtotal,
        discount is distributed proportionally across all items.
        
        Args:
            seller_id: Seller user ID
            warehouse_id: Warehouse ID
            items: List of {product_id, quantity, uom_id, unit_price?}
            customer_id: Optional customer ID
            final_total: Optional final total (triggers proportional discount)
            payments: List of {payment_type, amount}
            notes: Sale notes
        """
        
        payments = payments or []
        
        # Validate customer if provided
        customer = None
        is_vip_sale = False
        if customer_id:
            customer = self.customer_service.get_customer_by_id(customer_id)
            if not customer:
                return None, "Mijoz topilmadi"
            is_vip_sale = customer.customer_type == CustomerType.VIP
        
        # Create sale
        sale = Sale(
            sale_number=self.num_gen.get_next_sale_number(),
            sale_date=get_tashkent_today(),
            customer_id=customer_id,
            seller_id=seller_id,
            warehouse_id=warehouse_id,
            subtotal=Decimal("0"),
            discount_amount=Decimal("0"),
            discount_percent=Decimal("0"),
            total_amount=Decimal("0"),
            paid_amount=Decimal("0"),
            debt_amount=Decimal("0"),
            payment_status=PaymentStatus.PENDING,
            notes=notes,
            requires_delivery=requires_delivery,
            delivery_address=delivery_address,
            delivery_date=delivery_date,
            delivery_cost=delivery_cost,
            is_vip_sale=is_vip_sale,
            is_cancelled=False,
            sms_sent=False
        )
        self.db.add(sale)
        self.db.flush()
        
        # Process items
        subtotal = Decimal("0")
        sale_items = []
        
        for item_data in items:
            product = self.db.query(Product).filter(
                Product.id == item_data["product_id"],
                Product.is_deleted == False
            ).first()
            
            if not product:
                self.db.rollback()
                return None, f"Tovar topilmadi: ID {item_data['product_id']}"
            
            # Check stock availability
            available = self.stock_service.get_available_quantity(
                product.id, warehouse_id
            )
            base_qty = self.stock_service.convert_to_base_uom(
                product.id, Decimal(str(item_data["quantity"])), item_data["uom_id"]
            )

            # Round to 4 decimal places to avoid floating point precision issues
            base_qty = base_qty.quantize(Decimal("0.0001"))

            # Use small tolerance for comparison (0.0001)
            tolerance = Decimal("0.0001")
            if not product.allow_negative_stock and (available + tolerance) < base_qty:
                self.db.rollback()
                return None, f"'{product.name}' uchun yetarli qoldiq yo'q. Mavjud: {available}"

            # Determine price
            if item_data.get("unit_price") is not None:
                unit_price = Decimal(str(item_data["unit_price"]))
            elif is_vip_sale and product.vip_price:
                unit_price = product.vip_price
            else:
                # Get price for specific UOM if exists
                unit_price = self._get_price_for_uom(product, item_data["uom_id"], is_vip_sale)

            original_price = unit_price
            total_price = item_data["quantity"] * unit_price

            # Get stock cost for profit tracking
            stock = self.stock_service.get_stock(product.id, warehouse_id)
            unit_cost = stock.average_cost if stock else product.cost_price

            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=product.id,
                quantity=item_data["quantity"],
                uom_id=item_data["uom_id"],
                base_quantity=base_qty,
                original_price=original_price,
                unit_price=unit_price,
                discount_percent=Decimal("0"),
                discount_amount=Decimal("0"),
                total_price=total_price,
                unit_cost=unit_cost,
                notes=item_data.get("notes")
            )
            self.db.add(sale_item)
            sale_items.append(sale_item)

            subtotal += total_price

        # Apply proportional discount if final_total differs
        sale.subtotal = subtotal

        if final_total is not None and final_total < subtotal:
            self._apply_proportional_discount(sale, sale_items, final_total)
        else:
            sale.total_amount = subtotal + delivery_cost

        # Process payments
        total_paid = Decimal("0")
        payment_types = set()

        for payment_data in payments:
            payment_amount = Decimal(str(payment_data["amount"]))

            # Skip creating payment record if amount is 0 or negative
            if payment_amount <= 0:
                continue

            # Convert to lowercase to match enum values
            payment_type_str = payment_data["payment_type"].lower()
            payment_type = PaymentType(payment_type_str)

            payment = Payment(
                payment_number=self.num_gen.get_next_payment_number(),
                payment_date=get_tashkent_today(),
                sale_id=sale.id,
                customer_id=customer_id,
                payment_type=payment_type,
                amount=payment_amount,
                received_by_id=seller_id,
                is_confirmed=True
            )
            self.db.add(payment)
            total_paid += payment_amount
            payment_types.add(payment_type)

        sale.paid_amount = total_paid
        sale.debt_amount = max(Decimal("0"), sale.total_amount - total_paid)

        # Determine payment status and type
        if sale.debt_amount == 0:
            sale.payment_status = PaymentStatus.PAID
        elif total_paid > 0:
            sale.payment_status = PaymentStatus.PARTIAL
        else:
            sale.payment_status = PaymentStatus.DEBT

        if len(payment_types) > 1:
            sale.payment_type = PaymentType.MIXED
        elif len(payment_types) == 1:
            sale.payment_type = list(payment_types)[0]
        elif sale.debt_amount > 0:
            sale.payment_type = PaymentType.DEBT

        # Handle customer debt
        if customer_id and sale.debt_amount > 0:
            success, msg = self.customer_service.add_debt(
                customer_id, sale.debt_amount,
                "sale", sale.id,
                f"Sotuv #{sale.sale_number}",
                seller_id
            )
            if not success:
                self.db.rollback()
                return None, msg

        # Remove stock
        for sale_item in sale_items:
            stock, movement, msg = self.stock_service.remove_stock(
                product_id=sale_item.product_id,
                warehouse_id=warehouse_id,
                quantity=sale_item.quantity,
                uom_id=sale_item.uom_id,
                movement_type=MovementType.SALE,
                reference_type="sale",
                reference_id=sale.id,
                created_by_id=seller_id
            )
            if not stock:
                self.db.rollback()
                return None, msg

        # Update customer stats
        if customer_id:
            self.customer_service.update_purchase_stats(customer_id, sale.total_amount)

        # Audit log
        self._log_action(seller_id, "create", "sales", sale.id, f"Sotuv yaratildi: {sale.sale_number}")

        self.db.commit()
        self.db.refresh(sale)

        # Send Telegram notification for ALL sales (not just VIP)
        self._send_purchase_notification(sale, customer, sale_items, seller_id)

        return sale, f"Sotuv muvaffaqiyatli yaratildi: {sale.sale_number}"

    def _apply_proportional_discount(
        self,
        sale: Sale,
        items: List[SaleItem],
        final_total: Decimal
    ):
        """
        Apply proportional discount across all items.

        Algorithm:
        1. Calculate total discount = subtotal - final_total
        2. Calculate discount percentage
        3. Apply same percentage to each item
        4. Adjust last item for rounding differences
        """
        subtotal = sale.subtotal

        if final_total >= subtotal:
            sale.total_amount = subtotal + sale.delivery_cost
            return

        total_discount = subtotal - final_total
        discount_percent = (total_discount / subtotal * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        sale.discount_amount = total_discount
        sale.discount_percent = discount_percent
        sale.total_amount = final_total + sale.delivery_cost

        # Apply proportional discount to each item
        applied_discount = Decimal("0")

        for i, item in enumerate(items):
            if i == len(items) - 1:
                # Last item gets remaining discount to avoid rounding issues
                item_discount = total_discount - applied_discount
            else:
                # Proportional discount based on item's share of subtotal
                item_share = item.total_price / subtotal
                item_discount = (total_discount * item_share).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            item.discount_amount = item_discount
            item.discount_percent = discount_percent
            item.unit_price = ((item.total_price - item_discount) / item.quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            item.total_price = item.total_price - item_discount

            applied_discount += item_discount

    def _get_price_for_uom(self, product: Product, uom_id: int, is_vip: bool) -> Decimal:
        """Get price for specific UOM."""
        # If base UOM
        if uom_id == product.base_uom_id:
            return product.vip_price if is_vip and product.vip_price else product.sale_price

        # Check for UOM-specific price
        conversion = self.db.query(ProductUOMConversion).filter(
            ProductUOMConversion.product_id == product.id,
            ProductUOMConversion.uom_id == uom_id
        ).first()

        if conversion:
            if is_vip and conversion.vip_price:
                return conversion.vip_price
            if conversion.sale_price:
                return conversion.sale_price
            # Calculate from base price
            base_price = product.vip_price if is_vip and product.vip_price else product.sale_price
            return base_price * conversion.conversion_factor

        return product.sale_price

    def add_payment(
        self,
        sale_id: int,
        payment_type: str,
        amount: Decimal,
        received_by_id: int,
        transaction_id: str = None,
        notes: str = None
    ) -> Tuple[Optional[Payment], str]:
        """Add payment to existing sale."""
        sale = self.get_sale_by_id(sale_id)
        if not sale:
            return None, "Sotuv topilmadi"

        if sale.is_cancelled:
            return None, "Bekor qilingan sotuvga to'lov qo'shib bo'lmaydi"

        if sale.debt_amount <= 0:
            return None, "Bu sotuvda qarz yo'q"

        payment = Payment(
            payment_number=self.num_gen.get_next_payment_number(),
            payment_date=get_tashkent_today(),
            sale_id=sale_id,
            customer_id=sale.customer_id,
            payment_type=PaymentType(payment_type.lower()),
            amount=amount,
            transaction_id=transaction_id,
            notes=notes,
            received_by_id=received_by_id,
            is_confirmed=True
        )
        self.db.add(payment)

        # Update sale
        sale.paid_amount += amount
        sale.debt_amount = max(Decimal("0"), sale.total_amount - sale.paid_amount)

        if sale.debt_amount == 0:
            sale.payment_status = PaymentStatus.PAID
        else:
            sale.payment_status = PaymentStatus.PARTIAL

        # Update customer debt
        if sale.customer_id:
            self.customer_service.pay_debt(
                sale.customer_id, amount, payment_type,
                f"To'lov #{payment.payment_number}", received_by_id
            )

        self.db.commit()
        self.db.refresh(payment)

        return payment, "To'lov qabul qilindi"

    def cancel_sale(
        self,
        sale_id: int,
        reason: str,
        return_to_stock: bool,
        cancelled_by_id: int
    ) -> Tuple[bool, str]:
        """Cancel sale and optionally return items to stock."""
        sale = self.get_sale_by_id(sale_id)
        if not sale:
            return False, "Sotuv topilmadi"

        if sale.is_cancelled:
            return False, "Bu sotuv allaqachon bekor qilingan"

        # Return items to stock if requested
        if return_to_stock:
            for item in sale.items:
                stock = self.stock_service.get_stock(item.product_id, sale.warehouse_id)
                unit_cost = stock.average_cost if stock else item.unit_cost

                self.stock_service.add_stock(
                    product_id=item.product_id,
                    warehouse_id=sale.warehouse_id,
                    quantity=item.quantity,
                    uom_id=item.uom_id,
                    unit_cost=unit_cost,
                    movement_type=MovementType.RETURN_FROM_CUSTOMER,
                    reference_type="sale_cancel",
                    reference_id=sale.id,
                    notes=f"Bekor qilish: {reason}",
                    created_by_id=cancelled_by_id
                )

        # Reverse customer debt
        if sale.customer_id and sale.debt_amount > 0:
            customer = self.customer_service.get_customer_by_id(sale.customer_id)
            if customer:
                customer.current_debt -= sale.debt_amount
                if customer.current_debt < 0:
                    customer.current_debt = Decimal("0")

        sale.is_cancelled = True
        sale.cancelled_reason = reason
        sale.cancelled_by_id = cancelled_by_id
        sale.cancelled_at = get_tashkent_now().isoformat()
        sale.payment_status = PaymentStatus.CANCELLED

        self._log_action(cancelled_by_id, "cancel", "sales", sale.id, f"Sotuv bekor qilindi: {reason}")

        self.db.commit()
        return True, "Sotuv bekor qilindi"

    def get_daily_summary(self, sale_date: date, warehouse_id: int = None, seller_id: int = None) -> dict:
        """Get daily sales summary."""
        query = self.db.query(Sale).filter(
            Sale.sale_date == sale_date,
            Sale.is_cancelled == False
        )

        if warehouse_id:
            query = query.filter(Sale.warehouse_id == warehouse_id)

        if seller_id:
            query = query.filter(Sale.seller_id == seller_id)

        sales = query.all()

        total_sales = len(sales)
        total_amount = sum(s.total_amount for s in sales)
        total_paid = sum(s.paid_amount for s in sales)
        total_debt = sum(s.debt_amount for s in sales)
        total_discount = sum(s.discount_amount for s in sales)

        # Calculate profit (rough estimate)
        total_cost = Decimal("0")
        for sale in sales:
            for item in sale.items:
                total_cost += item.unit_cost * item.base_quantity

        gross_profit = total_amount - total_cost

        # Payment breakdown - also filter by seller if specified
        payment_query = self.db.query(
            Payment.payment_type,
            func.sum(Payment.amount)
        ).filter(
            Payment.payment_date == sale_date,
            Payment.is_cancelled == False
        )

        if seller_id:
            # Filter payments by sales that belong to this seller
            sale_ids = [s.id for s in sales]
            payment_query = payment_query.filter(Payment.sale_id.in_(sale_ids))

        payments = payment_query.group_by(Payment.payment_type).all()

        payment_breakdown = {pt.value: amount for pt, amount in payments}

        return {
            "date": sale_date.isoformat(),
            "total_sales": total_sales,
            "total_amount": total_amount,
            "total_paid": total_paid,
            "total_debt": total_debt,
            "total_discount": total_discount,
            "gross_profit": gross_profit,
            "payment_breakdown": payment_breakdown
        }

    def get_seller_summary(
        self,
        seller_id: int,
        start_date: date,
        end_date: date
    ) -> dict:
        """Get sales summary for specific seller."""
        query = self.db.query(Sale).filter(
            Sale.seller_id == seller_id,
            Sale.sale_date >= start_date,
            Sale.sale_date <= end_date,
            Sale.is_cancelled == False
        )

        sales = query.all()

        return {
            "seller_id": seller_id,
            "period": f"{start_date} - {end_date}",
            "total_sales": len(sales),
            "total_amount": sum(s.total_amount for s in sales),
            "total_discount": sum(s.discount_amount for s in sales),
            "average_sale": sum(s.total_amount for s in sales) / len(sales) if sales else Decimal("0")
        }

    def _send_purchase_notification(
        self,
        sale: Sale,
        customer: Optional[Customer],
        sale_items: List[SaleItem],
        seller_id: int
    ):
        """Send purchase notification to Telegram for ALL sales."""
        try:
            # Get seller name
            from database.models import User
            seller = self.db.query(User).filter(User.id == seller_id).first()
            operator_name = f"{seller.first_name} {seller.last_name}" if seller else "Kassir"

            # Prepare items data
            items = []
            for item in sale_items:
                product = self.db.query(Product).filter(Product.id == item.product_id).first()
                # Get UOM symbol from relationship
                uom_symbol = "dona"
                if item.uom:
                    uom_symbol = item.uom.symbol
                items.append({
                    "product_name": product.name if product else f"Tovar #{item.product_id}",
                    "quantity": float(item.quantity),
                    "uom_symbol": uom_symbol,
                    "unit_price": float(item.unit_price),
                    "discount_amount": float(item.discount_amount),
                    "total_price": float(item.total_price)
                })

            # Customer info (may be None)
            customer_telegram_id = customer.telegram_id if customer else None
            customer_name = customer.name if customer else "Noma'lum mijoz"
            customer_phone = customer.phone if customer else ""
            customer_type = customer.customer_type.name if customer else "STANDARD"

            # Send notification (fire-and-forget)
            send_purchase_notification_sync(
                customer_telegram_id=customer_telegram_id,
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_type=customer_type,
                sale_number=sale.sale_number,
                sale_date=sale.created_at or get_tashkent_now(),
                items=items,
                total_amount=float(sale.total_amount),
                paid_amount=float(sale.paid_amount),
                debt_amount=float(sale.debt_amount),
                operator_name=operator_name
            )
        except Exception as e:
            # Don't fail the sale if notification fails
            import logging
            logging.error(f"Failed to send purchase notification: {e}")

    def _log_action(self, user_id: int, action: str, table: str, record_id: int, description: str):
        """Log action to audit."""
        log = AuditLog(
            user_id=user_id,
            action=action,
            table_name=table,
            record_id=record_id,
            description=description
        )
        self.db.add(log)


# Import at end to avoid circular imports
from database.models import ProductUOMConversion
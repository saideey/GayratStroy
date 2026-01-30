"""
Customer management service.
Handles customers, debt tracking, and VIP operations.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func

from database.models import Customer, CustomerDebt, CustomerType, AuditLog
from core.security import get_password_hash, verify_password
from schemas.customer import CustomerCreate, CustomerUpdate, CustomerSearchParams
from services.telegram_notifier import send_payment_notification_sync
from utils.helpers import get_tashkent_now, get_tashkent_today


class CustomerService:
    """Customer management service."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_customer_by_id(self, customer_id: int) -> Optional[Customer]:
        """Get customer by ID."""
        return self.db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.is_deleted == False
        ).first()
    
    def get_customer_by_phone(self, phone: str) -> Optional[Customer]:
        """Get customer by phone number."""
        return self.db.query(Customer).filter(
            Customer.phone == phone,
            Customer.is_deleted == False
        ).first()
    
    def get_customer_by_login(self, login: str) -> Optional[Customer]:
        """Get VIP customer by login."""
        return self.db.query(Customer).filter(
            Customer.login == login,
            Customer.is_deleted == False
        ).first()
    
    def get_customers(
        self,
        page: int = 1,
        per_page: int = 20,
        params: CustomerSearchParams = None
    ) -> Tuple[List[Customer], int]:
        """Get paginated customers list."""
        query = self.db.query(Customer).options(
            joinedload(Customer.manager)
        ).filter(Customer.is_deleted == False)
        
        if params:
            # Search by name, phone, company
            if params.q:
                search_term = f"%{params.q}%"
                query = query.filter(
                    or_(
                        Customer.name.ilike(search_term),
                        Customer.phone.ilike(search_term),
                        Customer.company_name.ilike(search_term)
                    )
                )
            
            # Filter by customer type
            if params.customer_type:
                query = query.filter(Customer.customer_type == params.customer_type)
            
            # Filter by debt status
            if params.has_debt is True:
                query = query.filter(Customer.current_debt > 0)
            elif params.has_debt is False:
                query = query.filter(Customer.current_debt == 0)
            
            # Filter by active status
            if params.is_active is not None:
                query = query.filter(Customer.is_active == params.is_active)
            
            # Filter by manager
            if params.manager_id:
                query = query.filter(Customer.manager_id == params.manager_id)
            
            # Sorting
            sort_column = getattr(Customer, params.sort_by, Customer.name)
            if params.sort_order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(Customer.name.asc())
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        customers = query.offset(offset).limit(per_page).all()
        
        return customers, total
    
    def create_customer(
        self,
        data: CustomerCreate,
        created_by_id: int
    ) -> Tuple[Optional[Customer], str]:
        """Create new customer."""
        
        # Check phone uniqueness
        existing = self.get_customer_by_phone(data.phone)
        if existing:
            return None, "Bu telefon raqami allaqachon ro'yxatdan o'tgan"
        
        # Check login uniqueness for VIP
        if data.login:
            existing_login = self.get_customer_by_login(data.login)
            if existing_login:
                return None, "Bu login allaqachon band"
        
        customer = Customer(
            name=data.name,
            company_name=data.company_name,
            phone=data.phone,
            phone_secondary=data.phone_secondary,
            email=data.email,
            address=data.address,
            customer_type=data.customer_type,
            credit_limit=data.credit_limit,
            personal_discount_percent=data.personal_discount_percent,
            inn=data.inn,
            notes=data.notes,
            sms_enabled=data.sms_enabled,
            email_enabled=data.email_enabled,
            manager_id=data.manager_id,
            is_active=True,
            current_debt=Decimal("0"),
            advance_balance=Decimal("0"),
            total_purchases=Decimal("0"),
            total_purchases_count=0
        )
        
        # Set VIP credentials if provided
        if data.login and data.password:
            customer.login = data.login
            customer.password_hash = get_password_hash(data.password)
            customer.customer_type = CustomerType.VIP
        
        self.db.add(customer)
        self.db.flush()
        
        self._log_action(created_by_id, "create", "customers", customer.id, f"Mijoz yaratildi: {customer.name}")
        
        self.db.commit()
        self.db.refresh(customer)
        
        return customer, "Mijoz muvaffaqiyatli yaratildi"
    
    def update_customer(
        self,
        customer_id: int,
        data: CustomerUpdate,
        updated_by_id: int
    ) -> Tuple[Optional[Customer], str]:
        """Update customer."""
        customer = self.get_customer_by_id(customer_id)
        if not customer:
            return None, "Mijoz topilmadi"
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(customer, field):
                setattr(customer, field, value)
        
        self._log_action(updated_by_id, "update", "customers", customer.id, f"Mijoz yangilandi: {customer.name}")
        
        self.db.commit()
        self.db.refresh(customer)
        
        return customer, "Mijoz muvaffaqiyatli yangilandi"
    
    def delete_customer(self, customer_id: int, deleted_by_id: int) -> Tuple[bool, str]:
        """Soft delete customer."""
        customer = self.get_customer_by_id(customer_id)
        if not customer:
            return False, "Mijoz topilmadi"
        
        # Check for outstanding debt
        if customer.current_debt > 0:
            return False, f"Mijozda {customer.current_debt:,.0f} so'm qarz mavjud"
        
        customer.is_deleted = True
        customer.deleted_at = get_tashkent_now()
        customer.is_active = False
        
        self._log_action(deleted_by_id, "delete", "customers", customer.id, f"Mijoz o'chirildi: {customer.name}")
        
        self.db.commit()
        return True, "Mijoz o'chirildi"
    
    def add_debt(
        self,
        customer_id: int,
        amount: Decimal,
        reference_type: str = None,
        reference_id: int = None,
        description: str = None,
        created_by_id: int = None
    ) -> Tuple[bool, str]:
        """Add debt to customer (from sale on credit)."""
        customer = self.get_customer_by_id(customer_id)
        if not customer:
            return False, "Mijoz topilmadi"
        
        # Check credit limit
        new_debt = customer.current_debt + amount
        if customer.credit_limit > 0 and new_debt > customer.credit_limit:
            return False, f"Kredit limiti oshib ketdi. Limit: {customer.credit_limit:,.0f}, Joriy qarz: {customer.current_debt:,.0f}"
        
        balance_before = customer.current_debt
        customer.current_debt = new_debt
        
        # Create debt record
        debt_record = CustomerDebt(
            customer_id=customer_id,
            transaction_type="DEBT_INCREASE",
            amount=amount,
            balance_before=balance_before,
            balance_after=new_debt,
            reference_type=reference_type,
            reference_id=reference_id,
            description=description or "Qarzga sotish",
            created_by_id=created_by_id
        )
        self.db.add(debt_record)
        
        self.db.commit()
        return True, f"Qarz qo'shildi. Joriy qarz: {new_debt:,.0f} so'm"
    
    def pay_debt(
        self,
        customer_id: int,
        amount: Decimal,
        payment_type: str = "CASH",
        description: str = None,
        created_by_id: int = None
    ) -> Tuple[bool, str, Decimal]:
        """
        Pay customer debt.
        Returns: (success, message, change_amount)
        """
        customer = self.get_customer_by_id(customer_id)
        if not customer:
            return False, "Mijoz topilmadi", Decimal("0")
        
        balance_before = customer.current_debt
        
        # If payment is more than debt, add to advance
        if amount > customer.current_debt:
            excess = amount - customer.current_debt
            customer.current_debt = Decimal("0")
            customer.advance_balance += excess
            
            # Create debt payment record
            debt_record = CustomerDebt(
                customer_id=customer_id,
                transaction_type="DEBT_PAYMENT",
                amount=balance_before,
                balance_before=balance_before,
                balance_after=Decimal("0"),
                description=description or f"Qarz to'lovi ({payment_type})",
                created_by_id=created_by_id
            )
            self.db.add(debt_record)
            
            self.db.commit()
            
            # Send Telegram notification for VIP customers
            self._send_payment_notification(
                customer, payment_type, float(balance_before),
                float(balance_before), 0, created_by_id
            )
            
            return True, f"Qarz to'liq to'landi. {excess:,.0f} so'm avansga o'tkazildi", excess
        else:
            customer.current_debt -= amount
            
            debt_record = CustomerDebt(
                customer_id=customer_id,
                transaction_type="DEBT_PAYMENT",
                amount=amount,
                balance_before=balance_before,
                balance_after=customer.current_debt,
                description=description or f"Qarz to'lovi ({payment_type})",
                created_by_id=created_by_id
            )
            self.db.add(debt_record)
            
            self.db.commit()
            
            # Send Telegram notification for VIP customers
            self._send_payment_notification(
                customer, payment_type, float(amount),
                float(balance_before), float(customer.current_debt), created_by_id
            )
            
            return True, f"To'lov qabul qilindi. Qoldiq qarz: {customer.current_debt:,.0f} so'm", Decimal("0")
    
    def add_advance(
        self,
        customer_id: int,
        amount: Decimal,
        payment_type: str = "CASH",
        description: str = None,
        created_by_id: int = None
    ) -> Tuple[bool, str]:
        """Add advance payment from customer."""
        customer = self.get_customer_by_id(customer_id)
        if not customer:
            return False, "Mijoz topilmadi"
        
        # First pay off any existing debt
        if customer.current_debt > 0:
            if amount >= customer.current_debt:
                remaining = amount - customer.current_debt
                self.pay_debt(customer_id, customer.current_debt, payment_type, "Avansdan qarz to'lovi", created_by_id)
                if remaining > 0:
                    customer.advance_balance += remaining
            else:
                self.pay_debt(customer_id, amount, payment_type, "Avansdan qarz to'lovi", created_by_id)
                return True, f"To'lov qarzga ishlatildi. Qoldiq qarz: {customer.current_debt:,.0f} so'm"
        else:
            customer.advance_balance += amount
        
        self.db.commit()
        return True, f"Avans qo'shildi. Balans: {customer.advance_balance:,.0f} so'm"
    
    def use_advance(
        self,
        customer_id: int,
        amount: Decimal,
        reference_type: str = None,
        reference_id: int = None,
        description: str = None,
        created_by_id: int = None
    ) -> Tuple[bool, str]:
        """Use customer advance for payment."""
        customer = self.get_customer_by_id(customer_id)
        if not customer:
            return False, "Mijoz topilmadi"
        
        if customer.advance_balance < amount:
            return False, f"Avans yetarli emas. Balans: {customer.advance_balance:,.0f} so'm"
        
        customer.advance_balance -= amount
        
        debt_record = CustomerDebt(
            customer_id=customer_id,
            transaction_type="ADVANCE_USE",
            amount=amount,
            balance_before=customer.advance_balance + amount,
            balance_after=customer.advance_balance,
            reference_type=reference_type,
            reference_id=reference_id,
            description=description or "Avansdan foydalanish",
            created_by_id=created_by_id
        )
        self.db.add(debt_record)
        
        self.db.commit()
        return True, f"Avansdan {amount:,.0f} so'm ishlatildi"
    
    def get_debt_history(
        self,
        customer_id: int,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[CustomerDebt], int]:
        """Get customer debt history."""
        query = self.db.query(CustomerDebt).filter(
            CustomerDebt.customer_id == customer_id
        ).order_by(CustomerDebt.created_at.desc())
        
        total = query.count()
        offset = (page - 1) * per_page
        records = query.offset(offset).limit(per_page).all()
        
        return records, total
    
    def get_debtors(self, min_debt: Decimal = None, manager_id: int = None) -> List[Customer]:
        """Get all customers with debt."""
        query = self.db.query(Customer).filter(
            Customer.is_deleted == False,
            Customer.current_debt > 0
        )
        
        if min_debt:
            query = query.filter(Customer.current_debt >= min_debt)
        
        if manager_id:
            query = query.filter(Customer.manager_id == manager_id)
        
        return query.order_by(Customer.current_debt.desc()).all()
    
    def get_total_debt(self, manager_id: int = None) -> Decimal:
        """Get total debt from all customers."""
        query = self.db.query(func.sum(Customer.current_debt)).filter(
            Customer.is_deleted == False
        )
        
        if manager_id:
            query = query.filter(Customer.manager_id == manager_id)
        
        result = query.scalar()
        return result or Decimal("0")
    
    # VIP Customer methods
    def authenticate_vip(self, login: str, password: str) -> Optional[Customer]:
        """Authenticate VIP customer."""
        customer = self.get_customer_by_login(login)
        if not customer:
            return None
        
        if not customer.password_hash:
            return None
        
        if not verify_password(password, customer.password_hash):
            return None
        
        return customer
    
    def set_vip_credentials(
        self,
        customer_id: int,
        login: str,
        password: str,
        updated_by_id: int
    ) -> Tuple[bool, str]:
        """Set VIP credentials for customer."""
        customer = self.get_customer_by_id(customer_id)
        if not customer:
            return False, "Mijoz topilmadi"
        
        # Check login uniqueness
        existing = self.db.query(Customer).filter(
            Customer.login == login,
            Customer.id != customer_id
        ).first()
        if existing:
            return False, "Bu login allaqachon band"
        
        customer.login = login
        customer.password_hash = get_password_hash(password)
        customer.customer_type = CustomerType.VIP
        
        self._log_action(updated_by_id, "update", "customers", customer.id, "VIP credentials yaratildi")
        
        self.db.commit()
        return True, "VIP hisob yaratildi"
    
    def update_purchase_stats(
        self,
        customer_id: int,
        sale_amount: Decimal
    ):
        """Update customer purchase statistics after sale."""
        customer = self.get_customer_by_id(customer_id)
        if customer:
            customer.total_purchases += sale_amount
            customer.total_purchases_count += 1
            customer.last_purchase_date = get_tashkent_today()
            self.db.commit()
    
    def _send_payment_notification(
        self,
        customer: Customer,
        payment_type: str,
        payment_amount: float,
        previous_debt: float,
        current_debt: float,
        created_by_id: int = None
    ):
        """Send payment notification to VIP customer via Telegram."""
        # Only send for VIP customers
        if customer.customer_type != CustomerType.VIP:
            return
        
        try:
            # Get operator name
            from database.models import User
            operator_name = "Kassir"
            if created_by_id:
                user = self.db.query(User).filter(User.id == created_by_id).first()
                if user:
                    operator_name = f"{user.first_name} {user.last_name}"
            
            # Send notification (fire-and-forget)
            send_payment_notification_sync(
                customer_telegram_id=customer.telegram_id,
                customer_name=customer.name,
                customer_phone=customer.phone,
                customer_type=customer.customer_type.name,
                payment_date=get_tashkent_now(),
                payment_amount=payment_amount,
                payment_type=payment_type,
                previous_debt=previous_debt,
                current_debt=current_debt,
                operator_name=operator_name
            )
        except Exception as e:
            # Don't fail the payment if notification fails
            import logging
            logging.error(f"Failed to send payment notification: {e}")
    
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

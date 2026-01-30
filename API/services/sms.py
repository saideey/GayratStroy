"""
SMS Service.
Handles SMS sending via Eskiz.uz API (or test mode with logging).

Test mode: SMS messages are logged to console instead of being sent.
Production mode: SMS sent via Eskiz.uz API.
"""

import re
import requests
from datetime import datetime
from decimal import Decimal
from typing import Optional, Tuple, List
from loguru import logger
from sqlalchemy.orm import Session

from core.config import get_settings
from database.models import Customer, Sale, SMSTemplate, SMSLog
from utils.helpers import get_tashkent_now


class SMSService:
    """
    SMS sending service.
    
    Supports:
    - Eskiz.uz API integration
    - Test mode (logging only)
    - SMS templates with placeholders
    - SMS logging
    """
    
    # Eskiz.uz API endpoints
    ESKIZ_AUTH_URL = "https://notify.eskiz.uz/api/auth/login"
    ESKIZ_SEND_URL = "https://notify.eskiz.uz/api/message/sms/send"
    ESKIZ_BALANCE_URL = "https://notify.eskiz.uz/api/user/get-limit"
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.token = None
        self.token_expires = None
    
    @property
    def is_test_mode(self) -> bool:
        """Check if SMS is in test mode."""
        return not self.settings.sms_enabled or not self.settings.eskiz_email
    
    def _authenticate(self) -> bool:
        """Authenticate with Eskiz.uz API."""
        if self.is_test_mode:
            return True
        
        try:
            response = requests.post(
                self.ESKIZ_AUTH_URL,
                data={
                    "email": self.settings.eskiz_email,
                    "password": self.settings.eskiz_password
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("data", {}).get("token")
                logger.info("Eskiz.uz autentifikatsiya muvaffaqiyatli")
                return True
            else:
                logger.error(f"Eskiz.uz autentifikatsiya xatosi: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Eskiz.uz ulanish xatosi: {str(e)}")
            return False
    
    def _format_phone(self, phone: str) -> str:
        """Format phone number for Eskiz.uz (998XXXXXXXXX)."""
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Remove leading + if present
        if digits.startswith('998'):
            return digits
        elif digits.startswith('8') and len(digits) == 10:
            return '998' + digits[1:]
        elif len(digits) == 9:
            return '998' + digits
        
        return digits
    
    def send_sms(
        self,
        phone: str,
        message: str,
        reference_type: str = None,
        reference_id: int = None
    ) -> Tuple[bool, str]:
        """
        Send SMS message.
        
        Args:
            phone: Recipient phone number
            message: SMS text
            reference_type: Type of reference (sale, debt_reminder, etc.)
            reference_id: ID of referenced record
            
        Returns:
            (success, message)
        """
        formatted_phone = self._format_phone(phone)
        
        # Log SMS
        sms_log = SMSLog(
            phone_number=formatted_phone,
            message=message,
            reference_type=reference_type,
            reference_id=reference_id,
            status="pending"
        )
        self.db.add(sms_log)
        self.db.flush()
        
        # Test mode - just log
        if self.is_test_mode:
            logger.info("=" * 50)
            logger.info("📱 SMS YUBORILDI (TEST MODE)")
            logger.info(f"📞 Telefon: {formatted_phone}")
            logger.info(f"📝 Xabar: {message}")
            logger.info(f"📌 Reference: {reference_type}:{reference_id}")
            logger.info("=" * 50)
            
            sms_log.status = "sent"
            sms_log.sent_at = get_tashkent_now().isoformat()
            self.db.commit()
            
            return True, "SMS yuborildi (test mode)"
        
        # Production mode - send via Eskiz
        try:
            # Authenticate if needed
            if not self.token:
                if not self._authenticate():
                    sms_log.status = "failed"
                    sms_log.error_message = "Autentifikatsiya xatosi"
                    self.db.commit()
                    return False, "SMS xizmati mavjud emas"
            
            # Send SMS
            response = requests.post(
                self.ESKIZ_SEND_URL,
                headers={"Authorization": f"Bearer {self.token}"},
                data={
                    "mobile_phone": formatted_phone,
                    "message": message,
                    "from": "4546"  # Eskiz sender ID
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                sms_log.status = "sent"
                sms_log.sent_at = get_tashkent_now().isoformat()
                sms_log.provider_message_id = str(data.get("id", ""))
                self.db.commit()
                
                logger.info(f"SMS yuborildi: {formatted_phone}")
                return True, "SMS muvaffaqiyatli yuborildi"
            else:
                error_msg = response.json().get("message", "Unknown error")
                sms_log.status = "failed"
                sms_log.error_message = error_msg
                self.db.commit()
                
                logger.error(f"SMS yuborish xatosi: {error_msg}")
                return False, f"SMS yuborib bo'lmadi: {error_msg}"
                
        except Exception as e:
            sms_log.status = "failed"
            sms_log.error_message = str(e)
            self.db.commit()
            
            logger.error(f"SMS yuborish xatosi: {str(e)}")
            return False, f"SMS yuborish xatosi: {str(e)}"
    
    def send_sale_notification(self, sale: Sale) -> Tuple[bool, str]:
        """
        Send sale notification SMS to customer.
        
        Template placeholders:
        - {customer_name}
        - {sale_number}
        - {total_amount}
        - {paid_amount}
        - {debt_amount}
        """
        if not sale.customer or not sale.customer.sms_enabled:
            return False, "Mijozda SMS yoqilmagan"
        
        if not sale.customer.phone:
            return False, "Mijoz telefon raqami yo'q"
        
        # Get template
        template = self.db.query(SMSTemplate).filter(
            SMSTemplate.code == "SALE_NOTIFICATION",
            SMSTemplate.is_active == True
        ).first()
        
        if template:
            message = template.template_text
        else:
            message = "Xurmatli {customer_name}! Xaridingiz #{sale_number} uchun rahmat. Jami: {total_amount} so'm."
        
        # Replace placeholders
        message = message.format(
            customer_name=sale.customer.name,
            sale_number=sale.sale_number,
            total_amount=f"{sale.total_amount:,.0f}",
            paid_amount=f"{sale.paid_amount:,.0f}",
            debt_amount=f"{sale.debt_amount:,.0f}"
        )
        
        return self.send_sms(
            phone=sale.customer.phone,
            message=message,
            reference_type="sale",
            reference_id=sale.id
        )
    
    def send_debt_reminder(self, customer: Customer) -> Tuple[bool, str]:
        """
        Send debt reminder SMS to customer.
        """
        if not customer.sms_enabled:
            return False, "Mijozda SMS yoqilmagan"
        
        if not customer.phone:
            return False, "Mijoz telefon raqami yo'q"
        
        if customer.current_debt <= 0:
            return False, "Mijozda qarz yo'q"
        
        # Get template
        template = self.db.query(SMSTemplate).filter(
            SMSTemplate.code == "DEBT_REMINDER",
            SMSTemplate.is_active == True
        ).first()
        
        if template:
            message = template.template_text
        else:
            message = "Xurmatli {customer_name}! Sizda {debt_amount} so'm qarz mavjud. Iltimos, to'lovni amalga oshiring."
        
        message = message.format(
            customer_name=customer.name,
            debt_amount=f"{customer.current_debt:,.0f}"
        )
        
        return self.send_sms(
            phone=customer.phone,
            message=message,
            reference_type="debt_reminder",
            reference_id=customer.id
        )
    
    def send_payment_confirmation(
        self,
        customer: Customer,
        payment_amount: Decimal,
        remaining_debt: Decimal
    ) -> Tuple[bool, str]:
        """Send payment confirmation SMS."""
        if not customer.sms_enabled or not customer.phone:
            return False, "SMS yuborib bo'lmadi"
        
        template = self.db.query(SMSTemplate).filter(
            SMSTemplate.code == "PAYMENT_CONFIRMATION",
            SMSTemplate.is_active == True
        ).first()
        
        if template:
            message = template.template_text
        else:
            message = "Xurmatli {customer_name}! {payment_amount} so'm to'lov qabul qilindi. Qoldiq qarz: {remaining_debt} so'm."
        
        message = message.format(
            customer_name=customer.name,
            payment_amount=f"{payment_amount:,.0f}",
            remaining_debt=f"{remaining_debt:,.0f}"
        )
        
        return self.send_sms(
            phone=customer.phone,
            message=message,
            reference_type="payment",
            reference_id=customer.id
        )
    
    def send_bulk_sms(
        self,
        customers: List[Customer],
        message: str
    ) -> Tuple[int, int]:
        """
        Send bulk SMS to multiple customers.
        
        Returns: (success_count, failed_count)
        """
        success_count = 0
        failed_count = 0
        
        for customer in customers:
            if customer.sms_enabled and customer.phone:
                success, _ = self.send_sms(
                    phone=customer.phone,
                    message=message.format(customer_name=customer.name),
                    reference_type="bulk",
                    reference_id=None
                )
                if success:
                    success_count += 1
                else:
                    failed_count += 1
            else:
                failed_count += 1
        
        return success_count, failed_count
    
    def get_balance(self) -> Optional[int]:
        """Get SMS balance from Eskiz.uz."""
        if self.is_test_mode:
            logger.info("SMS balans: TEST MODE (cheksiz)")
            return 99999
        
        try:
            if not self.token:
                if not self._authenticate():
                    return None
            
            response = requests.get(
                self.ESKIZ_BALANCE_URL,
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("balance", 0)
            
            return None
        except Exception as e:
            logger.error(f"Balans tekshirish xatosi: {str(e)}")
            return None
    
    def get_sms_logs(
        self,
        phone: str = None,
        status: str = None,
        limit: int = 50
    ) -> List[SMSLog]:
        """Get SMS logs with filters."""
        query = self.db.query(SMSLog)
        
        if phone:
            query = query.filter(SMSLog.phone_number.contains(phone))
        
        if status:
            query = query.filter(SMSLog.status == status)
        
        return query.order_by(SMSLog.created_at.desc()).limit(limit).all()

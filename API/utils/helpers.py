"""
Utility functions.
"""

import re
import random
import string
from datetime import datetime, timezone, timedelta
from typing import Optional
from decimal import Decimal, ROUND_HALF_UP

# Tashkent timezone (UTC+5)
TASHKENT_TZ = timezone(timedelta(hours=5))


def get_tashkent_now() -> datetime:
    """Get current datetime in Tashkent timezone (naive datetime)."""
    return datetime.now(TASHKENT_TZ).replace(tzinfo=None)


def get_tashkent_today():
    """Get current date in Tashkent timezone."""
    return datetime.now(TASHKENT_TZ).date()


def get_tashkent_time_str() -> str:
    """Get current time as string in Tashkent timezone (HH:MM)."""
    return datetime.now(TASHKENT_TZ).strftime('%H:%M')


def get_tashkent_datetime_str() -> str:
    """Get current datetime as string in Tashkent timezone (DD.MM.YYYY HH:MM)."""
    return datetime.now(TASHKENT_TZ).strftime('%d.%m.%Y %H:%M')


def get_tashkent_date_str() -> str:
    """Get current date as string in Tashkent timezone (DD.MM.YYYY)."""
    return datetime.now(TASHKENT_TZ).strftime('%d.%m.%Y')


def generate_slug(text: str) -> str:
    """
    Generate URL-safe slug from text.
    
    Args:
        text: Input text
        
    Returns:
        URL-safe slug
    """
    # Convert to lowercase
    slug = text.lower()
    
    # Replace Cyrillic characters
    cyrillic_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'ў': "o'", 'қ': 'q', 'ғ': "g'", 'ҳ': 'h'
    }
    
    for cyr, lat in cyrillic_map.items():
        slug = slug.replace(cyr, lat)
    
    # Replace spaces and special characters with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    return slug


def generate_number(prefix: str, last_number: Optional[int] = None) -> str:
    """
    Generate document number with prefix.
    
    Example: generate_number("SAL", 123) -> "SAL-000124"
    
    Args:
        prefix: Document prefix (e.g., "SAL", "PO", "INV")
        last_number: Last used number
        
    Returns:
        Generated document number
    """
    next_number = (last_number or 0) + 1
    return f"{prefix}-{next_number:06d}"


def generate_random_string(length: int = 8) -> str:
    """Generate random alphanumeric string."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def round_decimal(value: Decimal, places: int = 2) -> Decimal:
    """
    Round decimal to specified places.
    
    Args:
        value: Decimal value
        places: Number of decimal places
        
    Returns:
        Rounded decimal
    """
    quantize_str = '0.' + '0' * places
    return Decimal(str(value)).quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)


def format_phone(phone: str) -> str:
    """
    Format phone number to standard format.
    
    Args:
        phone: Raw phone number
        
    Returns:
        Formatted phone number (+998XXXXXXXXX)
    """
    # Remove all non-digits
    digits = re.sub(r'\D', '', phone)
    
    # Handle Uzbekistan numbers
    if len(digits) == 9:
        return f"+998{digits}"
    elif len(digits) == 12 and digits.startswith('998'):
        return f"+{digits}"
    elif len(digits) == 13 and digits.startswith('998'):
        return f"+{digits[1:]}"
    
    return f"+{digits}"


def format_currency(amount: Decimal, currency: str = "so'm") -> str:
    """
    Format amount as currency string.
    
    Args:
        amount: Decimal amount
        currency: Currency suffix
        
    Returns:
        Formatted currency string (e.g., "1 234 567 so'm")
    """
    # Format with thousand separators
    formatted = f"{amount:,.0f}".replace(",", " ")
    return f"{formatted} {currency}"


def calculate_percentage(part: Decimal, whole: Decimal) -> Decimal:
    """
    Calculate percentage.
    
    Args:
        part: Part value
        whole: Whole value
        
    Returns:
        Percentage as decimal
    """
    if whole == 0:
        return Decimal(0)
    return round_decimal((part / whole) * 100, 2)


def parse_date_range(
    start_date: Optional[str],
    end_date: Optional[str]
) -> tuple:
    """
    Parse date range strings.
    
    Args:
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
        
    Returns:
        Tuple of (start_datetime, end_datetime)
    """
    start = None
    end = None
    
    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
    
    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d")
        # Include the entire end day
        end = end.replace(hour=23, minute=59, second=59)
    
    return start, end


class NumberGenerator:
    """
    Document number generator with database tracking.
    """
    
    def __init__(self, db_session):
        self.db = db_session
    
    def get_next_sale_number(self) -> str:
        """Generate next sale number."""
        from database.models import Sale
        
        today = datetime.now(TASHKENT_TZ).strftime("%Y%m%d")
        prefix = f"SAL-{today}"
        
        # Find last sale number for today
        last_sale = self.db.query(Sale).filter(
            Sale.sale_number.like(f"{prefix}%")
        ).order_by(Sale.id.desc()).first()
        
        if last_sale:
            last_num = int(last_sale.sale_number.split("-")[-1])
            return f"{prefix}-{last_num + 1:04d}"
        
        return f"{prefix}-0001"
    
    def get_next_payment_number(self) -> str:
        """Generate next payment number."""
        from database.models import Payment
        
        today = datetime.now(TASHKENT_TZ).strftime("%Y%m%d")
        prefix = f"PAY-{today}"
        
        last_payment = self.db.query(Payment).filter(
            Payment.payment_number.like(f"{prefix}%")
        ).order_by(Payment.id.desc()).first()
        
        if last_payment:
            last_num = int(last_payment.payment_number.split("-")[-1])
            return f"{prefix}-{last_num + 1:04d}"
        
        return f"{prefix}-0001"
    
    def get_next_purchase_order_number(self) -> str:
        """Generate next purchase order number."""
        from database.models import PurchaseOrder
        
        today = datetime.now(TASHKENT_TZ).strftime("%Y%m%d")
        prefix = f"PO-{today}"
        
        last_po = self.db.query(PurchaseOrder).filter(
            PurchaseOrder.order_number.like(f"{prefix}%")
        ).order_by(PurchaseOrder.id.desc()).first()
        
        if last_po:
            last_num = int(last_po.order_number.split("-")[-1])
            return f"{prefix}-{last_num + 1:04d}"
        
        return f"{prefix}-0001"
    
    def get_next_transfer_number(self) -> str:
        """Generate next stock transfer number."""
        from database.models import StockTransfer
        
        today = datetime.now(TASHKENT_TZ).strftime("%Y%m%d")
        prefix = f"TRF-{today}"
        
        last_transfer = self.db.query(StockTransfer).filter(
            StockTransfer.transfer_number.like(f"{prefix}%")
        ).order_by(StockTransfer.id.desc()).first()
        
        if last_transfer:
            last_num = int(last_transfer.transfer_number.split("-")[-1])
            return f"{prefix}-{last_num + 1:04d}"
        
        return f"{prefix}-0001"
    
    def get_next_inventory_check_number(self) -> str:
        """Generate next inventory check number."""
        from database.models import InventoryCheck
        
        today = datetime.now(TASHKENT_TZ).strftime("%Y%m%d")
        prefix = f"INV-{today}"
        
        last_check = self.db.query(InventoryCheck).filter(
            InventoryCheck.check_number.like(f"{prefix}%")
        ).order_by(InventoryCheck.id.desc()).first()
        
        if last_check:
            last_num = int(last_check.check_number.split("-")[-1])
            return f"{prefix}-{last_num + 1:04d}"
        
        return f"{prefix}-0001"

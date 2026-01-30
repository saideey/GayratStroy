"""
Telegram Notification Client for API
Sends notifications to the Telegram Bot service via HTTP.
Fetches director IDs from database settings.
"""
import os
import logging
import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Telegram bot service URL
TELEGRAM_BOT_URL = os.getenv("TELEGRAM_BOT_URL", "http://telegram_bot:8081")


def get_director_ids_from_db() -> List[str]:
    """
    Fetch director Telegram IDs from database settings.
    Returns list of director IDs.
    """
    try:
        from database.connection import SessionLocal
        from database.models import SystemSetting
        
        db = SessionLocal()
        try:
            setting = db.query(SystemSetting).filter(
                SystemSetting.key == "director_telegram_ids"
            ).first()
            
            if setting and setting.value:
                return [id.strip() for id in setting.value.split(",") if id.strip()]
            return []
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error fetching director IDs from database: {e}")
        return []


class TelegramNotifier:
    """Client for sending notifications to Telegram Bot service."""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or TELEGRAM_BOT_URL
        self.timeout = 30.0
    
    async def send_purchase_notification(
        self,
        customer_telegram_id: Optional[str],
        customer_name: str,
        customer_phone: str,
        customer_type: str,
        sale_number: str,
        sale_date: datetime,
        items: List[Dict[str, Any]],
        total_amount: float,
        paid_amount: float,
        debt_amount: float,
        operator_name: str = "Kassir",
        director_ids: List[str] = None
    ) -> Dict[str, Any]:
        """
        Send purchase notification to Telegram Bot service.
        
        Returns:
            Dict with notification result
        """
        # Only send for VIP customers
        if customer_type.upper() != "VIP":
            logger.debug(f"Skipping notification - customer {customer_name} is not VIP")
            return {"success": True, "skipped": True, "reason": "Not VIP"}
        
        payload = {
            "customer_telegram_id": customer_telegram_id,
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "customer_type": customer_type,
            "sale_number": sale_number,
            "sale_date": sale_date.isoformat() if isinstance(sale_date, datetime) else str(sale_date),
            "items": items,
            "total_amount": float(total_amount),
            "paid_amount": float(paid_amount),
            "debt_amount": float(debt_amount),
            "operator_name": operator_name,
            "director_ids": director_ids or []
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/notify/purchase",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Purchase notification sent for {customer_name}: {result}")
                    return result
                else:
                    logger.error(f"Failed to send purchase notification: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }
                    
        except httpx.ConnectError:
            logger.warning("Telegram Bot service not available - notification skipped")
            return {"success": False, "error": "Telegram Bot service not available"}
        except Exception as e:
            logger.error(f"Error sending purchase notification: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_payment_notification(
        self,
        customer_telegram_id: Optional[str],
        customer_name: str,
        customer_phone: str,
        customer_type: str,
        payment_date: datetime,
        payment_amount: float,
        payment_type: str,
        previous_debt: float,
        current_debt: float,
        operator_name: str = "Kassir",
        director_ids: List[str] = None
    ) -> Dict[str, Any]:
        """
        Send payment notification to Telegram Bot service.
        
        Returns:
            Dict with notification result
        """
        # Only send for VIP customers
        if customer_type.upper() != "VIP":
            logger.debug(f"Skipping notification - customer {customer_name} is not VIP")
            return {"success": True, "skipped": True, "reason": "Not VIP"}
        
        payload = {
            "customer_telegram_id": customer_telegram_id,
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "customer_type": customer_type,
            "payment_date": payment_date.isoformat() if isinstance(payment_date, datetime) else str(payment_date),
            "payment_amount": float(payment_amount),
            "payment_type": payment_type,
            "previous_debt": float(previous_debt),
            "current_debt": float(current_debt),
            "operator_name": operator_name,
            "director_ids": director_ids or []
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/notify/payment",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Payment notification sent for {customer_name}: {result}")
                    return result
                else:
                    logger.error(f"Failed to send payment notification: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }
                    
        except httpx.ConnectError:
            logger.warning("Telegram Bot service not available - notification skipped")
            return {"success": False, "error": "Telegram Bot service not available"}
        except Exception as e:
            logger.error(f"Error sending payment notification: {e}")
            return {"success": False, "error": str(e)}
    
    async def health_check(self) -> bool:
        """Check if Telegram Bot service is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False


# Global instance
telegram_notifier = TelegramNotifier()


# Synchronous wrapper for use in non-async context
def send_purchase_notification_sync(
    customer_telegram_id: Optional[str],
    customer_name: str,
    customer_phone: str,
    customer_type: str,
    sale_number: str,
    sale_date: datetime,
    items: List[Dict[str, Any]],
    total_amount: float,
    paid_amount: float,
    debt_amount: float,
    operator_name: str = "Kassir"
) -> None:
    """
    Fire-and-forget purchase notification (runs in background).
    Fetches director IDs from database.
    Use this from synchronous code - it will not block.
    """
    import asyncio
    import threading
    
    # Get director IDs from database
    director_ids = get_director_ids_from_db()
    
    def run_async():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                telegram_notifier.send_purchase_notification(
                    customer_telegram_id=customer_telegram_id,
                    customer_name=customer_name,
                    customer_phone=customer_phone,
                    customer_type=customer_type,
                    sale_number=sale_number,
                    sale_date=sale_date,
                    items=items,
                    total_amount=total_amount,
                    paid_amount=paid_amount,
                    debt_amount=debt_amount,
                    operator_name=operator_name,
                    director_ids=director_ids
                )
            )
        finally:
            loop.close()
    
    # Run in background thread to not block
    thread = threading.Thread(target=run_async, daemon=True)
    thread.start()


def send_payment_notification_sync(
    customer_telegram_id: Optional[str],
    customer_name: str,
    customer_phone: str,
    customer_type: str,
    payment_date: datetime,
    payment_amount: float,
    payment_type: str,
    previous_debt: float,
    current_debt: float,
    operator_name: str = "Kassir"
) -> None:
    """
    Fire-and-forget payment notification (runs in background).
    Fetches director IDs from database.
    Use this from synchronous code - it will not block.
    """
    import asyncio
    import threading
    
    # Get director IDs from database
    director_ids = get_director_ids_from_db()
    
    def run_async():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                telegram_notifier.send_payment_notification(
                    customer_telegram_id=customer_telegram_id,
                    customer_name=customer_name,
                    customer_phone=customer_phone,
                    customer_type=customer_type,
                    payment_date=payment_date,
                    payment_amount=payment_amount,
                    payment_type=payment_type,
                    previous_debt=previous_debt,
                    current_debt=current_debt,
                    operator_name=operator_name,
                    director_ids=director_ids
                )
            )
        finally:
            loop.close()
    
    # Run in background thread to not block
    thread = threading.Thread(target=run_async, daemon=True)
    thread.start()

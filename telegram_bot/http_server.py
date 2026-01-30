"""
HTTP Server for receiving notifications from main API.
This provides a REST API that the main backend can call to trigger notifications.
"""
import logging
from datetime import datetime
from typing import Optional
from aiohttp import web

from notification_service import NotificationService

logger = logging.getLogger(__name__)


class HTTPServer:
    """HTTP server for receiving notification requests from main API."""
    
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        self.app = web.Application()
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup HTTP routes."""
        self.app.router.add_post('/notify/purchase', self.handle_purchase_notification)
        self.app.router.add_post('/notify/payment', self.handle_payment_notification)
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_post('/test', self.test_notification)
        self.app.router.add_post('/send-daily-report', self.send_daily_report)
        self.app.router.add_post('/send-daily-report-excel', self.send_daily_report_with_excel)
    
    async def health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint."""
        return web.json_response({
            "status": "ok",
            "service": "telegram-bot",
            "timestamp": datetime.now().isoformat()
        })
    
    async def test_notification(self, request: web.Request) -> web.Response:
        """Test notification endpoint."""
        try:
            data = await request.json()
            chat_id = data.get('chat_id')
            message = data.get('message', 'Test message from Metall Baza Bot')
            
            if not chat_id:
                return web.json_response({
                    "success": False,
                    "error": "chat_id is required"
                }, status=400)
            
            success = await self.notification_service.send_test_message(chat_id, message)
            
            return web.json_response({
                "success": success,
                "message": "Test message sent" if success else "Failed to send"
            })
        except Exception as e:
            logger.error(f"Test notification error: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def handle_purchase_notification(self, request: web.Request) -> web.Response:
        """
        Handle purchase notification request.
        
        Expected JSON body:
        {
            "customer_telegram_id": "123456789",
            "customer_name": "Jamshid Karimov",
            "customer_phone": "+998901234567",
            "customer_type": "VIP",
            "sale_number": "S-001234",
            "sale_date": "2026-01-19T14:30:00",
            "items": [
                {
                    "product_name": "Armatura 12mm",
                    "quantity": 10,
                    "uom_symbol": "tonna",
                    "unit_price": 15000000,
                    "discount_amount": 0,
                    "total_price": 150000000
                }
            ],
            "total_amount": 150000000,
            "paid_amount": 100000000,
            "debt_amount": 50000000,
            "operator_name": "Admin"
        }
        """
        try:
            data = await request.json()
            
            # Validate required fields
            required_fields = ['customer_name', 'sale_number', 'items', 'total_amount']
            for field in required_fields:
                if field not in data:
                    return web.json_response({
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }, status=400)
            
            # Check if customer is VIP
            customer_type = data.get('customer_type', '').upper()
            if customer_type != 'VIP':
                return web.json_response({
                    "success": True,
                    "message": "Notification skipped - customer is not VIP",
                    "customer_notified": False,
                    "director_notified": False
                })
            
            # Parse sale date
            sale_date = data.get('sale_date')
            if isinstance(sale_date, str):
                try:
                    sale_date = datetime.fromisoformat(sale_date.replace('Z', '+00:00'))
                except ValueError:
                    sale_date = datetime.now()
            else:
                sale_date = datetime.now()
            
            # Send notification
            result = await self.notification_service.send_purchase_notification(
                customer_telegram_id=data.get('customer_telegram_id'),
                customer_name=data['customer_name'],
                customer_phone=data.get('customer_phone', ''),
                sale_number=data['sale_number'],
                sale_date=sale_date,
                items=data['items'],
                total_amount=float(data['total_amount']),
                paid_amount=float(data.get('paid_amount', 0)),
                debt_amount=float(data.get('debt_amount', 0)),
                operator_name=data.get('operator_name', 'Kassir'),
                director_ids=data.get('director_ids', [])
            )
            
            logger.info(f"Purchase notification processed: {result}")
            
            return web.json_response(result)
            
        except Exception as e:
            logger.error(f"Purchase notification error: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def handle_payment_notification(self, request: web.Request) -> web.Response:
        """
        Handle payment notification request.
        
        Expected JSON body:
        {
            "customer_telegram_id": "123456789",
            "customer_name": "Jamshid Karimov",
            "customer_phone": "+998901234567",
            "customer_type": "VIP",
            "payment_date": "2026-01-19T14:30:00",
            "payment_amount": 50000000,
            "payment_type": "CASH",
            "previous_debt": 100000000,
            "current_debt": 50000000,
            "operator_name": "Admin"
        }
        """
        try:
            data = await request.json()
            
            # Validate required fields
            required_fields = ['customer_name', 'payment_amount']
            for field in required_fields:
                if field not in data:
                    return web.json_response({
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }, status=400)
            
            # Check if customer is VIP
            customer_type = data.get('customer_type', '').upper()
            if customer_type != 'VIP':
                return web.json_response({
                    "success": True,
                    "message": "Notification skipped - customer is not VIP",
                    "customer_notified": False,
                    "director_notified": False
                })
            
            # Parse payment date
            payment_date = data.get('payment_date')
            if isinstance(payment_date, str):
                try:
                    payment_date = datetime.fromisoformat(payment_date.replace('Z', '+00:00'))
                except ValueError:
                    payment_date = datetime.now()
            else:
                payment_date = datetime.now()
            
            # Send notification
            result = await self.notification_service.send_payment_notification(
                customer_telegram_id=data.get('customer_telegram_id'),
                customer_name=data['customer_name'],
                customer_phone=data.get('customer_phone', ''),
                payment_date=payment_date,
                payment_amount=float(data['payment_amount']),
                payment_type=data.get('payment_type', 'CASH'),
                previous_debt=float(data.get('previous_debt', 0)),
                current_debt=float(data.get('current_debt', 0)),
                operator_name=data.get('operator_name', 'Kassir'),
                director_ids=data.get('director_ids', [])
            )
            
            logger.info(f"Payment notification processed: {result}")
            
            return web.json_response(result)
            
        except Exception as e:
            logger.error(f"Payment notification error: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    def get_app(self) -> web.Application:
        """Get the aiohttp application."""
        return self.app
    
    async def send_daily_report(self, request: web.Request) -> web.Response:
        """
        Send daily report to Telegram group.
        
        Expected JSON body:
        {
            "chat_id": "-1001234567890",
            "message": "Report message in HTML format"
        }
        """
        try:
            data = await request.json()
            chat_id = data.get('chat_id')
            message = data.get('message')
            
            if not chat_id:
                return web.json_response({
                    "success": False,
                    "error": "chat_id is required"
                }, status=400)
            
            if not message:
                return web.json_response({
                    "success": False,
                    "error": "message is required"
                }, status=400)
            
            success = await self.notification_service.send_daily_report(chat_id, message)
            
            return web.json_response({
                "success": success,
                "message": "Daily report sent" if success else "Failed to send report"
            })
        except Exception as e:
            logger.error(f"Daily report error: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def send_daily_report_with_excel(self, request: web.Request) -> web.Response:
        """
        Send daily report with Excel file to Telegram group.
        
        Expected JSON body:
        {
            "chat_id": "-1001234567890",
            "report_data": { ... all report data ... }
        }
        """
        try:
            data = await request.json()
            chat_id = data.get('chat_id')
            report_data = data.get('report_data', {})
            
            if not chat_id:
                return web.json_response({
                    "success": False,
                    "error": "chat_id is required"
                }, status=400)
            
            success = await self.notification_service.send_daily_report_with_excel(chat_id, report_data)
            
            return web.json_response({
                "success": success,
                "message": "Daily report with Excel sent" if success else "Failed to send report"
            })
        except Exception as e:
            logger.error(f"Daily report with Excel error: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

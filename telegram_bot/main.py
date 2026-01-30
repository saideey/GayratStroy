"""
Metall Baza Telegram Bot
Main entry point - starts HTTP server for receiving notifications from API.

Architecture:
- HTTP Server (aiohttp) listens for notification requests from main API
- When a request comes in, it sends Telegram message to customer and director
- Also sends Excel file with detailed information
- Scheduler checks daily and sends reports at configured time

API Endpoints:
- POST /notify/purchase - Send purchase notification
- POST /notify/payment - Send payment notification  
- GET /health - Health check
- POST /test - Test notification
- POST /send-daily-report - Send daily report to group

Communication Flow:
Main API -> HTTP POST to /notify/* -> Telegram Bot -> Customer + Director
"""
import asyncio
import logging
import sys
import httpx
from datetime import datetime, time
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import config
from notification_service import NotificationService
from http_server import HTTPServer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DailyReportScheduler:
    """Scheduler for sending daily reports at configured time."""
    
    def __init__(self, notification_service, api_url: str = "http://api:8000"):
        self.api_url = api_url
        self.notification_service = notification_service
        self.last_sent_date = None
        self.running = True
    
    async def get_settings(self) -> dict:
        """Fetch report settings from API."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.api_url}/api/v1/settings/telegram/group-settings")
                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", {})
        except Exception as e:
            logger.error(f"Failed to fetch settings: {e}")
        return {}
    
    async def get_daily_report_data(self) -> dict:
        """Fetch daily report data from API."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.api_url}/api/v1/settings/telegram/daily-report-data")
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch report data: {e}")
        return {}
    
    async def run(self):
        """Run the scheduler loop."""
        logger.info("📅 Daily report scheduler started")
        
        while self.running:
            try:
                settings = await self.get_settings()
                is_enabled = settings.get("is_enabled", False)
                report_time_str = settings.get("report_time", "19:00")
                group_chat_id = settings.get("group_chat_id", "")
                
                now = datetime.now()
                current_time = now.time()
                today = now.date()
                
                # Parse configured time (24-hour format)
                try:
                    hour, minute = map(int, report_time_str.split(":"))
                except:
                    hour, minute = 19, 0
                
                # Log status every 5 minutes (when minute is 0 or 30)
                if current_time.minute % 5 == 0 and current_time.second < 30:
                    logger.info(f"⏰ Scheduler check: enabled={is_enabled}, time={report_time_str}, "
                               f"current={current_time.strftime('%H:%M')}, last_sent={self.last_sent_date}")
                
                # Check if it's time to send report
                if (is_enabled and 
                    group_chat_id and
                    current_time.hour == hour and 
                    current_time.minute == minute and
                    self.last_sent_date != today):
                    
                    logger.info(f"⏰ Time to send daily report! ({report_time_str})")
                    
                    # Get report data from API
                    report_data = await self.get_daily_report_data()
                    
                    if report_data.get("success"):
                        # Send via notification service
                        success = await self.notification_service.send_daily_report_with_excel(
                            chat_id=group_chat_id,
                            report_data=report_data.get("data", {})
                        )
                        
                        if success:
                            self.last_sent_date = today
                            logger.info("✅ Daily report sent successfully via scheduler")
                        else:
                            logger.error("❌ Failed to send daily report")
                    else:
                        logger.error(f"❌ Failed to get report data: {report_data.get('message')}")
                
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
            
            # Check every 30 seconds
            await asyncio.sleep(30)
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False


async def main():
    """Main entry point."""
    
    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.info("Please set TELEGRAM_BOT_TOKEN and DIRECTOR_TELEGRAM_ID in .env file")
        # Don't exit - run in mock mode for development
        logger.warning("Running in MOCK mode - notifications will be logged but not sent")
    
    # Initialize bot
    if config.BOT_TOKEN:
        bot = Bot(
            token=config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        logger.info("Telegram Bot initialized")
    else:
        # Create mock bot for development
        bot = None
        logger.warning("No BOT_TOKEN - running without Telegram connection")
    
    # Initialize services
    notification_service = NotificationService(bot) if bot else MockNotificationService()
    http_server = HTTPServer(notification_service)
    
    # Initialize scheduler with notification service
    scheduler = DailyReportScheduler(notification_service)
    
    # Start HTTP server
    runner = web.AppRunner(http_server.get_app())
    await runner.setup()
    
    site = web.TCPSite(runner, config.HTTP_HOST, config.HTTP_PORT)
    await site.start()
    
    logger.info(f"🚀 Telegram Bot HTTP Server started on {config.HTTP_HOST}:{config.HTTP_PORT}")
    logger.info("Endpoints:")
    logger.info(f"  POST http://{config.HTTP_HOST}:{config.HTTP_PORT}/notify/purchase")
    logger.info(f"  POST http://{config.HTTP_HOST}:{config.HTTP_PORT}/notify/payment")
    logger.info(f"  POST http://{config.HTTP_HOST}:{config.HTTP_PORT}/send-daily-report")
    logger.info(f"  GET  http://{config.HTTP_HOST}:{config.HTTP_PORT}/health")
    
    # Send startup notification to all directors
    director_ids = config.get_director_ids()
    if director_ids and bot:
        for director_id in director_ids:
            try:
                await bot.send_message(
                    chat_id=director_id,
                    text=f"🤖 <b>{config.COMPANY_NAME} Bot ishga tushdi!</b>\n\n"
                         f"📅 Sana: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                         f"✅ VIP mijozlarga habar yuborish tayyor\n"
                         f"📊 Kunlik hisobot scheduler faol"
                )
                logger.info(f"Startup notification sent to director {director_id}")
            except Exception as e:
                logger.error(f"Failed to send startup notification to {director_id}: {e}")
    
    # Start scheduler
    scheduler_task = asyncio.create_task(scheduler.run())
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(3600)  # Sleep for 1 hour
    except asyncio.CancelledError:
        pass
    finally:
        scheduler.stop()
        scheduler_task.cancel()
        if bot:
            await bot.session.close()
        await runner.cleanup()
        logger.info("Bot stopped")


class MockNotificationService:
    """Mock notification service for development without Telegram token."""
    
    async def send_purchase_notification(self, **kwargs):
        logger.info(f"[MOCK] Purchase notification: {kwargs.get('customer_name')} - {kwargs.get('sale_number')}")
        return {"success": True, "customer_notified": False, "director_notified": False, "mock": True}
    
    async def send_payment_notification(self, **kwargs):
        logger.info(f"[MOCK] Payment notification: {kwargs.get('customer_name')} - {kwargs.get('payment_amount')}")
        return {"success": True, "customer_notified": False, "director_notified": False, "mock": True}
    
    async def send_test_message(self, chat_id: str, message: str):
        logger.info(f"[MOCK] Test message to {chat_id}: {message}")
        return True
    
    async def send_daily_report(self, chat_id: str, message: str):
        logger.info(f"[MOCK] Daily report to {chat_id}:\n{message}")
        return True
    
    async def send_daily_report_with_excel(self, chat_id: str, report_data: dict):
        logger.info(f"[MOCK] Daily report with Excel to {chat_id}")
        logger.info(f"[MOCK] Data: sales={report_data.get('total_sales_count')}, amount={report_data.get('total_amount')}")
        return True


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        sys.exit(1)

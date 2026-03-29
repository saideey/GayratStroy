"""
G'ayrat Stroy House Telegram Bot
Main entry point - starts HTTP server for receiving notifications from API.

Architecture:
- Aiogram Dispatcher handles /start, phone registration, personal cabinet
- HTTP Server (aiohttp) listens for notification requests from main API
- Scheduler checks daily and sends reports at configured time

Bot Flow:
  User /start → Phone request → API link-phone → Personal Cabinet Menu

API Endpoints (HTTP Server):
- POST /notify/purchase - Send purchase notification
- POST /notify/payment - Send payment notification
- GET /health - Health check
- POST /test - Test notification
- POST /send-daily-report - Send daily report to group
"""
import asyncio
import logging
import sys
import httpx
from datetime import datetime
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from config import config
from notification_service import NotificationService
from http_server import HTTPServer
from handlers import start as start_handler, menu as menu_handler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
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
        logger.warning("Running in MOCK mode - notifications will be logged but not sent")

    # Initialize bot
    if config.BOT_TOKEN:
        bot = Bot(
            token=config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        logger.info("Telegram Bot initialized")
    else:
        bot = None
        logger.warning("No BOT_TOKEN - running without Telegram connection")

    # ── Aiogram Dispatcher ──
    dp = None
    if bot:
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        dp.include_router(start_handler.router)
        dp.include_router(menu_handler.router)
        logger.info("✅ Handlers registered: start, menu")

    # ── Services ──
    notification_service = NotificationService(bot) if bot else MockNotificationService()
    http_server = HTTPServer(notification_service)
    scheduler = DailyReportScheduler(notification_service)

    # ── aiohttp HTTP server ──
    runner = web.AppRunner(http_server.get_app())
    await runner.setup()
    site = web.TCPSite(runner, config.HTTP_HOST, config.HTTP_PORT)
    await site.start()

    logger.info(f"🚀 HTTP Server started on {config.HTTP_HOST}:{config.HTTP_PORT}")
    logger.info(f"  POST /notify/purchase  — sotuv bildirishnomasi")
    logger.info(f"  POST /notify/payment   — to'lov bildirishnomasi")
    logger.info(f"  POST /send-daily-report — kunlik hisobot")
    logger.info(f"  GET  /health           — holat tekshirish")

    if config.WEBAPP_URL:
        logger.info(f"🌐 WebApp URL: {config.WEBAPP_URL}")
    else:
        logger.info("ℹ️  WEBAPP_URL yo'q — bot komandalar rejimida ishlaydi")

    # ── Startup notification ──
    director_ids = config.get_director_ids()
    if director_ids and bot:
        for director_id in director_ids:
            try:
                await bot.send_message(
                    chat_id=director_id,
                    text=f"🤖 <b>{config.COMPANY_NAME} Bot ishga tushdi!</b>\n\n"
                         f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                         f"✅ Mijoz shaxsiy kabineti faol\n"
                         f"✅ Bildirishnomalar tayyor\n"
                         f"📊 Kunlik hisobot scheduler faol"
                )
            except Exception as e:
                logger.error(f"Startup notification error ({director_id}): {e}")

    # ── Barcha tasklar birgalikda ──
    # gather() barchasi bitta event loop da to'g'ri ishlaydi
    tasks = [asyncio.create_task(scheduler.run())]

    if bot and dp:
        async def run_polling():
            logger.info("🤖 Bot polling started")
            try:
                # drop_pending_updates=True — restart da eski xabarlarni o'tkazib yuborish
                await dp.start_polling(
                    bot,
                    allowed_updates=["message", "callback_query"],
                    drop_pending_updates=True,
                )
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(f"Polling error: {e}")

        tasks.append(asyncio.create_task(run_polling()))

    try:
        # Barcha tasklar birga ishlaydi, biri to'xtaganda qolganlar ham to'xtaydi
        await asyncio.gather(*tasks, return_exceptions=True)
    except asyncio.CancelledError:
        pass
    finally:
        scheduler.stop()
        for t in tasks:
            t.cancel()
        # Tasklar to'xtashini kutish
        await asyncio.gather(*tasks, return_exceptions=True)
        if bot:
            await bot.session.close()
        await runner.cleanup()
        logger.info("Bot stopped cleanly")


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

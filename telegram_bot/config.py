"""
Telegram Bot Configuration
"""
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Bot configuration from environment variables."""
    
    # Telegram Bot
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # Multiple director IDs (comma-separated)
    _DIRECTOR_IDS_STR = os.getenv("DIRECTOR_TELEGRAM_IDS", "")
    
    # HTTP Server for receiving notifications from API
    HTTP_HOST = os.getenv("BOT_HTTP_HOST", "0.0.0.0")
    HTTP_PORT = int(os.getenv("BOT_HTTP_PORT", "8081"))
    
    # API URL (for fetching additional data if needed)
    API_URL = os.getenv("API_URL", "http://api:8000/api/v1")
    
    # Company info for messages
    COMPANY_NAME = os.getenv("COMPANY_NAME", "Metall Baza")
    COMPANY_PHONE = os.getenv("COMPANY_PHONE", "+998 90 123 45 67")
    
    @classmethod
    def get_director_ids(cls) -> List[str]:
        """Get list of director Telegram IDs."""
        if not cls._DIRECTOR_IDS_STR:
            return []
        # Split by comma, strip whitespace, filter empty
        return [id.strip() for id in cls._DIRECTOR_IDS_STR.split(",") if id.strip()]
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        errors = []
        
        if not cls.BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is required")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True


config = Config()

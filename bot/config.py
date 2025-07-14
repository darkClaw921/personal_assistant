import os
import json
from typing import List
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

class Config:
    """Конфигурация бота"""
    
    # Telegram settings
    TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
    TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
    TELEGRAM_PHONE = os.getenv("TELEGRAM_PHONE", "")
    
    # Monitored chats
    MONITORED_CHATS = json.loads(os.getenv("MONITORED_CHATS", "[]"))
    
    # Google Calendar settings
    GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    GOOGLE_TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", "token.json")
    
    # Meeting settings
    MEETING_DURATION_MINUTES = int(os.getenv("MEETING_DURATION_MINUTES", "30"))
    WORKING_HOURS_START = int(os.getenv("WORKING_HOURS_START", "9"))
    WORKING_HOURS_END = int(os.getenv("WORKING_HOURS_END", "18"))
    TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")
    MEETING_PLATFORM = os.getenv("MEETING_PLATFORM", "google_meet")
    
    # Keywords to trigger meeting suggestion
    TRIGGER_KEYWORDS = ["встреча", "созвон", "наберу"]
    
    @classmethod
    def validate(cls) -> bool:
        """Проверка корректности конфигурации"""
        if not cls.TELEGRAM_API_ID or not cls.TELEGRAM_API_HASH:
            logger.error("Telegram API credentials not configured")
            return False
            
        if not cls.MONITORED_CHATS:
            logger.warning("No monitored chats configured")
            
        if not os.path.exists(cls.GOOGLE_CREDENTIALS_PATH):
            logger.error(f"Google credentials file not found: {cls.GOOGLE_CREDENTIALS_PATH}")
            return False
            
        return True 
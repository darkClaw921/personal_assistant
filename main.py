import asyncio
from telethon import TelegramClient
from loguru import logger

from bot.config import Config
from bot.handlers import BotHandlers

# Настройка логирования
logger.add("bot.log", rotation="1 MB", retention="7 days", level="INFO")

async def main():
    """Основная функция запуска бота"""
    logger.info("Starting Telegram bot...")
    
    # Проверяем конфигурацию
    if not Config.validate():
        logger.error("Configuration validation failed")
        return
    
    # Создаем клиент Telethon
    client = TelegramClient(
        'bot_session',
        Config.TELEGRAM_API_ID,
        Config.TELEGRAM_API_HASH
    )
    
    try:
        # Запускаем клиент
        await client.start(phone=Config.TELEGRAM_PHONE)
        logger.info("Telegram client started successfully")
        
        # Инициализируем обработчики
        handlers = BotHandlers(client)
        handlers.register_handlers()
        
        logger.info(f"Bot is monitoring {len(Config.MONITORED_CHATS)} chats")
        logger.info(f"Trigger keywords: {', '.join(Config.TRIGGER_KEYWORDS)}")
        
        # Запускаем бот
        await client.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"Error running bot: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())

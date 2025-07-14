import re
from typing import Dict, List
from telethon import events
from telethon.tl.types import User
from loguru import logger

from .config import Config
from .calendar_integration import GoogleCalendarIntegration

class BotHandlers:
    """Обработчики сообщений бота"""
    
    def __init__(self, client):
        self.client = client
        self.calendar = GoogleCalendarIntegration()
        self.pending_bookings: Dict[int, List] = {}  # user_id -> available_slots
    
    def register_handlers(self):
        """Регистрация всех обработчиков"""
        self.client.add_event_handler(self.handle_message, events.NewMessage)
    
    async def handle_message(self, event):
        """Основной обработчик сообщений"""
        try:
            # Проверяем, что сообщение из отслеживаемых чатов
            chat_id = str(event.chat_id)
            if chat_id not in Config.MONITORED_CHATS:
                return
            
            message_text = event.message.text.lower() if event.message.text else ""
            sender = await event.get_sender()
            
            # Игнорируем сообщения от ботов
            if isinstance(sender, User) and sender.bot:
                return
            
            logger.info(f"Processing message from {sender.id}: {message_text[:50]}...")
            
            # Проверяем на выбор слота (цифра в начале сообщения)
            slot_match = re.match(r'^(\d+)', message_text.strip())
            if slot_match and sender.id in self.pending_bookings:
                await self.handle_slot_selection(event, sender, int(slot_match.group(1)))
                return
            
            # Проверяем на ключевые слова для предложения встречи
            if any(keyword in message_text for keyword in Config.TRIGGER_KEYWORDS):
                await self.suggest_meeting_slots(event, sender)
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def suggest_meeting_slots(self, event, sender):
        """Предложение свободных слотов для встречи"""
        try:
            # Получаем свободные слоты
            free_slots = self.calendar.get_free_slots()
            
            if not free_slots:
                await event.reply("К сожалению, свободных слотов на ближайшие дни нет. Попробуйте позже.")
                return
            
            # Сохраняем слоты для пользователя
            self.pending_bookings[sender.id] = free_slots
            
            # Формируем сообщение с доступными слотами
            response = "Есть свободные слоты на:\n"
            for i, slot in enumerate(free_slots, 1):
                response += f"{i}. {slot['display']}\n"
            
            response += "\nНапишите номер слота для бронирования встречи."
            
            await event.reply(response)
            logger.info(f"Suggested {len(free_slots)} slots to user {sender.id}")
            
        except Exception as e:
            logger.error(f"Error suggesting meeting slots: {e}")
            await event.reply("Произошла ошибка при поиске свободных слотов. Попробуйте позже.")
    
    async def handle_slot_selection(self, event, sender, slot_number: int):
        """Обработка выбора временного слота"""
        try:
            user_slots = self.pending_bookings.get(sender.id, [])
            
            if not user_slots or slot_number < 1 or slot_number > len(user_slots):
                await event.reply("Неверный номер слота. Пожалуйста, выберите номер из предложенного списка.")
                return
            
            selected_slot = user_slots[slot_number - 1]
            
            # Получаем информацию о пользователе для создания встречи
            user_info = await self.client.get_entity(sender.id)
            meeting_title = f"Встреча с {user_info.first_name or 'пользователем'}"
            
            # Создаем встречу в календаре без добавления участника
            # (username не является валидным email адресом)
            meeting_link = self.calendar.create_meeting(
                start_time_str=selected_slot['start'],
                title=meeting_title,
                attendee_email=None  # Не добавляем участника, так как email неизвестен
            )
            
            if meeting_link:
                response = f"✅ Встреча создана на {selected_slot['display']}!\n"
                response += f"Ссылка на встречу: {meeting_link}"
            else:
                response = f"✅ Встреча создана на {selected_slot['display']}!\n"
                response += "Ссылка на встречу будет отправлена дополнительно."
            
            await event.reply(response)
            
            # Удаляем слоты пользователя после бронирования
            if sender.id in self.pending_bookings:
                del self.pending_bookings[sender.id]
            
            logger.info(f"Meeting booked for user {sender.id} at {selected_slot['start']}")
            
        except Exception as e:
            logger.error(f"Error handling slot selection: {e}")
            await event.reply("Произошла ошибка при создании встречи. Попробуйте позже.")
    
    async def cleanup_expired_bookings(self):
        """Очистка устаревших бронирований (вызывается периодически)"""
        # В реальном приложении здесь была бы логика очистки старых записей
        # На основе времени их создания
        pass 
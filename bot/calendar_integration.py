import os
import pickle
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pytz
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from loguru import logger

from .config import Config

SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarIntegration:
    """Интеграция с Google Calendar"""
    
    def __init__(self):
        self.service = None
        self.timezone = pytz.timezone(Config.TIMEZONE)
        self._authenticate()

    def _is_valid_email(self, email: str) -> bool:
        """Проверка валидности email адреса"""
        if not email:
            return False
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))
    
    def _authenticate(self):
        """Аутентификация в Google Calendar API"""
        creds = None
        
        # Загружаем существующий токен
        if os.path.exists(Config.GOOGLE_TOKEN_PATH):
            with open(Config.GOOGLE_TOKEN_PATH, 'rb') as token:
                creds = pickle.load(token)
        
        # Если нет валидных credentials, запускаем flow аутентификации
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    Config.GOOGLE_CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=5051, open_browser=False)
            
            # Сохраняем credentials для следующих запусков
            with open(Config.GOOGLE_TOKEN_PATH, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('calendar', 'v3', credentials=creds)
        logger.info("Google Calendar API authenticated successfully")
    
    def get_free_slots(self, date: datetime = None, days_ahead: int = 7) -> List[Dict[str, str]]:
        """Получение свободных временных слотов"""
        if not date:
            date = datetime.now(self.timezone)
        
        # Начинаем поиск с завтрашнего дня
        start_date = date.replace(hour=Config.WORKING_HOURS_START, minute=0, second=0, microsecond=0)
        if start_date <= datetime.now(self.timezone):
            start_date += timedelta(days=1)
        
        end_date = start_date + timedelta(days=days_ahead)
        
        # Получаем существующие события
        events_result = self.service.events().list(
            calendarId='primary',
            # calendarId='igorgerasimovsid',
            timeMin=start_date.isoformat(),
            timeMax=end_date.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Создаем список свободных слотов
        free_slots = []
        current_date = start_date.date()
        
        while current_date <= end_date.date():
            # Пропускаем выходные
            if current_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                current_date += timedelta(days=1)
                continue
            
            daily_slots = self._get_daily_free_slots(current_date, events)
            free_slots.extend(daily_slots)
            current_date += timedelta(days=1)
        
        # Возвращаем первые 5 слотов
        return free_slots[:5]
    
    def _get_daily_free_slots(self, date: datetime.date, events: List) -> List[Dict[str, str]]:
        """Получение свободных слотов на конкретный день"""
        slots = []
        start_hour = Config.WORKING_HOURS_START
        end_hour = Config.WORKING_HOURS_END
        
        # Создаем временные слоты по 30 минут
        current_time = datetime.combine(date, datetime.min.time().replace(hour=start_hour))
        current_time = self.timezone.localize(current_time)
        
        while current_time.hour < end_hour:
            slot_end = current_time + timedelta(minutes=Config.MEETING_DURATION_MINUTES)
            
            # Проверяем, свободен ли слот
            if self._is_slot_free(current_time, slot_end, events):
                slots.append({
                    'start': current_time.strftime('%Y-%m-%d %H:%M'),
                    'end': slot_end.strftime('%Y-%m-%d %H:%M'),
                    'display': current_time.strftime('%d.%m в %H:%M')
                })
            
            current_time += timedelta(minutes=30)
        
        return slots
    
    def _is_slot_free(self, start_time: datetime, end_time: datetime, events: List) -> bool:
        """Проверка, свободен ли временной слот"""
        for event in events:
            event_start = datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date')))
            event_end = datetime.fromisoformat(event['end'].get('dateTime', event['end'].get('date')))
            
            # Проверяем пересечение
            if (start_time < event_end and end_time > event_start):
                return False
        
        return True
    
    def create_meeting(self, start_time_str: str, title: str = "Встреча", 
                      attendee_email: str = None) -> Optional[str]:
        """Создание встречи в календаре"""
        try:
            start_time = datetime.fromisoformat(start_time_str)
            if start_time.tzinfo is None:
                start_time = self.timezone.localize(start_time)
            
            end_time = start_time + timedelta(minutes=Config.MEETING_DURATION_MINUTES)
            
            event = {
                'summary': title,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': Config.TIMEZONE,
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': Config.TIMEZONE,
                },
                'conferenceData': {
                    'createRequest': {
                        'requestId': f"meeting_{start_time.strftime('%Y%m%d_%H%M')}",
                        'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                    }
                }
            }
            
            # Проверяем валидность email перед добавлением участника
            if attendee_email:
                if self._is_valid_email(attendee_email):
                    event['attendees'] = [{'email': attendee_email}]
                    logger.info(f"Added attendee: {attendee_email}")
                else:
                    logger.warning(f"Invalid email provided, creating meeting without attendees: {attendee_email}")
            else:
                logger.info("No attendee email provided, creating meeting without attendees")
            
            # Создаем событие
            created_event = self.service.events().insert(
                calendarId='primary',
                body=event,
                conferenceDataVersion=1
            ).execute()
            
            # Получаем ссылку на встречу
            meet_link = None
            if 'conferenceData' in created_event and 'entryPoints' in created_event['conferenceData']:
                for entry_point in created_event['conferenceData']['entryPoints']:
                    if entry_point['entryPointType'] == 'video':
                        meet_link = entry_point['uri']
                        break
            
            logger.info(f"Meeting created: {created_event.get('htmlLink')}")
            return meet_link or created_event.get('htmlLink')
            
        except Exception as e:
            logger.error(f"Error creating meeting: {e}")
            return None 
# Telegram Personal Assistant Bot

Телеграм бот для автоматического планирования встреч с интеграцией Google Calendar.

## Функционал

- Мониторинг сообщений в определенных чатах
- Автоматическое предложение свободных временных слотов при упоминании ключевых слов (встреча, созвон, наберу)
- Создание встреч в Google Calendar
- Генерация ссылок на видеовстречи Google Meet

## Установка

1. Клонируйте репозиторий и установите зависимости:

```bash
uv sync
```

2. Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

## Настройка Telegram API

1. Перейдите на [my.telegram.org](https://my.telegram.org)
2. Войдите в свой аккаунт Telegram
3. Перейдите в раздел "API development tools"
4. Создайте новое приложение:
   - App title: Personal Assistant Bot
   - Short name: personal-assistant
   - Platform: Desktop
5. Скопируйте `api_id` и `api_hash` в файл `.env`

## Настройка Google Calendar API

### 1. Создание проекта в Google Cloud Console

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или выберите существующий
3. Включите Google Calendar API:
   - Перейдите в "APIs & Services" → "Library"
   - Найдите "Google Calendar API"
   - Нажмите "Enable"

### 2. Создание учетных данных

1. Перейдите в "APIs & Services" → "Credentials"
2. Нажмите "Create Credentials" → "OAuth 2.0 Client IDs"
3. Если появится предупреждение о настройке экрана согласия:
   - Перейдите в "OAuth consent screen"
   - Выберите "External" (если нет организации)
   - Заполните обязательные поля:
     - App name: Personal Assistant Bot
     - User support email: ваш email
     - Developer contact information: ваш email
   - Сохраните и продолжите
   - В разделе "Scopes" добавьте: `https://www.googleapis.com/auth/calendar`
   - Добавьте тестовых пользователей (ваш email)

4. Вернитесь к созданию OAuth 2.0 Client:
   - Application type: "Desktop application"
   - Name: Personal Assistant Bot
   - Нажмите "Create"

5. Скачайте JSON файл с учетными данными
6. Переименуйте файл в `credentials.json` и поместите в корень проекта

### 3. Получение ID чатов

Для получения ID чатов в Telegram:

1. Добавьте бота [@userinfobot](https://t.me/userinfobot) в нужные чаты
2. Отправьте команду `/start` в чате
3. Бот покажет ID чата (Chat ID)
4. Добавьте эти ID в массив `MONITORED_CHATS` в файле `.env`

Пример:
```
MONITORED_CHATS=["−1001234567890", "−1009876543210"]
```

## Конфигурация

Настройте файл `.env`:

```env
# Telegram настройки
TELEGRAM_API_ID=your_api_id_from_telegram
TELEGRAM_API_HASH=your_api_hash_from_telegram  
TELEGRAM_PHONE=+1234567890

# ID чатов для мониторинга
MONITORED_CHATS=["chat_id_1", "chat_id_2"]

# Google Calendar настройки
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_TOKEN_PATH=token.json

# Настройки встреч
MEETING_DURATION_MINUTES=30
WORKING_HOURS_START=9
WORKING_HOURS_END=18
TIMEZONE=Europe/Moscow
MEETING_PLATFORM=google_meet
```

## Запуск

```bash
uv run main.py
```

При первом запуске:
1. Бот попросит ввести код подтверждения из Telegram
2. Откроется браузер для авторизации в Google Calendar
3. После успешной авторизации бот начнет работу

## Использование

1. Напишите в отслеживаемом чате сообщение с ключевыми словами: "встреча", "созвон" или "наберу"
2. Бот ответит списком доступных временных слотов
3. Ответьте номером выбранного слота (например, "1")
4. Бот создаст встречу в календаре и отправит ссылку

Пример диалога:
```
Пользователь: Давайте организуем встречу на этой неделе
Бот: Есть свободные слоты на:
1. 25.12 в 10:00
2. 25.12 в 14:30
3. 26.12 в 09:00

Напишите номер слота для бронирования встречи.

Пользователь: 2
Бот: ✅ Встреча создана на 25.12 в 14:30!
Ссылка на встречу: https://meet.google.com/xxx-xxxx-xxx
```

## Структура проекта

```
personal_assistant/
├── bot/
│   ├── __init__.py
│   ├── config.py           # Конфигурация бота
│   ├── handlers.py         # Обработчики сообщений
│   └── calendar_integration.py  # Интеграция с Google Calendar
├── main.py                 # Точка входа
├── pyproject.toml          # Зависимости
├── .env.example            # Пример конфигурации
├── credentials.json        # Google API credentials (создается вручную)
├── token.json              # Google API токен (создается автоматически)
└── README.md               # Документация
```

## Логирование

Бот записывает логи в файл `bot.log` с ротацией по размеру (1 МБ) и хранением за 7 дней.

## Безопасность

- Используйте переменные окружения в продакшене
- Ограничьте область доступа OAuth только Calendar API

## Возможные проблемы

1. **Ошибка аутентификации Telegram**: Проверьте правильность API_ID, API_HASH и номера телефона
2. **Ошибка Google Calendar**: Убедитесь, что включен Calendar API и правильно настроены credentials
3. **Бот не отвечает**: Проверьте, что ID чатов указаны правильно в MONITORED_CHATS

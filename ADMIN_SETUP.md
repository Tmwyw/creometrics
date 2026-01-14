# Настройка Администратора

## Получение Telegram ID

1. Открой [@userinfobot](https://t.me/userinfobot)
2. Нажми `/start`
3. Бот отправит твой ID (число типа 123456789)

## Добавление в .env

Скопируй свой ID и добавь в `.env`:

```env
ADMIN_USER_IDS=YOUR_TELEGRAM_ID_HERE
```

Например:
```env
ADMIN_USER_IDS=123456789
```

Для нескольких админов:
```env
ADMIN_USER_IDS=123456789,987654321,555666777
```

## Или через скрипт

После первого запуска бота:

```bash
# Получи свой ID из логов бота или через @userinfobot
python scripts/create_admin.py YOUR_TELEGRAM_ID LazyEntrepreneur
```

## Проверка

После настройки:
1. Запусти бота: `python main.py`
2. Отправь `/start` боту
3. В логах должно появиться: "New user registered: YOUR_ID (@LazyEntrepreneur)"
4. Добавь этот ID в `.env` как `ADMIN_USER_IDS`
5. Перезапусти бота

## Получение ID канала

Для `REQUIRED_CHANNEL_ID` и `ADMIN_CHAT_ID`:

1. Переслать любое сообщение из канала боту [@username_to_id_bot](https://t.me/username_to_id_bot)
2. Скопировать ID (будет отрицательным, типа -1001234567890)
3. Добавить в `.env`

Текущий канал: @creometric
ID уже добавлен: `-1002484700092`

Если нужен отдельный админ-чат для логов:
1. Создай приватную группу
2. Добавь бота как админа
3. Получи ID группы
4. Обнови `ADMIN_CHAT_ID` в `.env`

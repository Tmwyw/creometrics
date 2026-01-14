# Быстрый старт CreoMetrics Bot

## Шаг 1: Установка зависимостей

```bash
# Установить Python 3.11
# https://www.python.org/downloads/

# Установить FFmpeg
# Windows: скачать с https://ffmpeg.org/ и добавить в PATH
# Linux: sudo apt-get install ffmpeg
# macOS: brew install ffmpeg

# Установить Python зависимости
pip install -r requirements.txt
```

## Шаг 2: Настройка PostgreSQL

### Локально

```bash
# Установить PostgreSQL
# Windows: https://www.postgresql.org/download/windows/
# Linux: sudo apt-get install postgresql
# macOS: brew install postgresql

# Создать базу данных
createdb creo_bot

# Или через psql
psql -U postgres
CREATE DATABASE creo_bot;
\q
```

### Railway (для продакшна)

1. Зарегистрироваться на [Railway.app](https://railway.app)
2. Создать новый проект
3. Добавить PostgreSQL сервис
4. Скопировать DATABASE_URL

## Шаг 3: Настройка Redis

### Локально

```bash
# Установить Redis
# Windows: https://redis.io/docs/getting-started/installation/install-redis-on-windows/
# Linux: sudo apt-get install redis-server
# macOS: brew install redis

# Запустить Redis
redis-server
```

### Railway (для продакшна)

1. В Railway проекте добавить Redis сервис
2. Скопировать REDIS_URL

## Шаг 4: Создать Telegram бота

1. Открыть [@BotFather](https://t.me/BotFather) в Telegram
2. Отправить `/newbot`
3. Следовать инструкциям
4. Скопировать токен бота

## Шаг 5: Настроить канал

1. Создать Telegram канал (или использовать существующий @creometric)
2. Добавить бота как администратора канала
3. Получить ID канала:
   - Перейти на https://t.me/username_to_id_bot
   - Переслать любое сообщение из канала
   - Скопировать ID (будет отрицательным, например -1001234567890)

## Шаг 6: Создать админ-чат для логов

1. Создать приватную группу в Telegram
2. Добавить бота в группу как администратора
3. Получить ID группы (аналогично п.5)

## Шаг 7: Настроить .env

```bash
# Скопировать пример
cp .env.example .env

# Отредактировать .env
nano .env
```

Заполнить:

```env
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
BOT_USERNAME=@YourBotUsername

REQUIRED_CHANNEL=@creometric
REQUIRED_CHANNEL_ID=-1001234567890

ADMIN_CHAT_ID=-1001234567890
ADMIN_USER_IDS=123456789

DATABASE_URL=postgresql://user:password@localhost:5432/creo_bot
REDIS_URL=redis://localhost:6379/0
```

## Шаг 8: Инициализировать базу данных

```bash
# Создать таблицы
python -c "from database import init_db; init_db()"

# Создать пресеты по умолчанию
python scripts/init_presets.py

# Создать админа (замените на ваш Telegram ID)
python scripts/create_admin.py 123456789 your_username
```

## Шаг 9: Запустить бота

### Терминал 1: Redis (если локально)
```bash
redis-server
```

### Терминал 2: Celery Worker
```bash
celery -A workers.celery_app worker --loglevel=info --concurrency=2
```

### Терминал 3: Bot
```bash
python main.py
```

## Шаг 10: Протестировать

1. Открыть бота в Telegram
2. Отправить `/start`
3. Подписаться на канал (если попросит)
4. Попробовать уникализировать фото:
   - Нажать "📸 Уникализировать фото"
   - Отправить фото
   - Выбрать количество копий
   - Дождаться результата

## Деплой на Railway

### 1. Подготовка

```bash
git init
git add .
git commit -m "Initial commit"
```

Создать репозиторий на GitHub и запушить код.

### 2. Railway

1. Открыть [Railway.app](https://railway.app)
2. New Project → Deploy from GitHub repo
3. Выбрать ваш репозиторий
4. Railway автоматически определит Python проект

### 3. Добавить сервисы

В Railway проекте:
- Add PostgreSQL
- Add Redis

### 4. Настроить переменные окружения

В Railway → Variables, добавить все переменные из `.env`.

Railway автоматически добавит:
- `DATABASE_URL` (из PostgreSQL сервиса)
- `REDIS_URL` (из Redis сервиса)

Нужно добавить вручную:
- `BOT_TOKEN`
- `ADMIN_USER_IDS`
- `REQUIRED_CHANNEL_ID`
- `ADMIN_CHAT_ID`
- и др.

### 5. Деплой

Railway автоматически задеплоит после push в GitHub.

### 6. Инициализация на Railway

Через Railway CLI или Web Terminal:

```bash
python scripts/init_presets.py
python scripts/create_admin.py YOUR_TELEGRAM_ID
```

## Решение проблем

### Бот не отвечает

```bash
# Проверить логи
tail -f logs/bot.log

# Проверить что бот запущен
ps aux | grep python

# Проверить подключение к БД
python -c "from database import SessionLocal; db = SessionLocal(); print('OK')"
```

### Celery задачи не выполняются

```bash
# Проверить что Redis запущен
redis-cli ping

# Проверить Celery worker
celery -A workers.celery_app inspect active
```

### FFmpeg ошибки

```bash
# Проверить установку FFmpeg
ffmpeg -version

# Проверить ffprobe
ffprobe -version
```

### Проблемы с памятью

Уменьшить `worker_concurrency`:

```bash
celery -A workers.celery_app worker --concurrency=1
```

## Следующие шаги

После успешного запуска:

1. Прочитать `TODO.md` - список оставшихся задач
2. Изучить `ARCHITECTURE.md` - архитектура проекта
3. Прочитать `DEVELOPMENT.md` - руководство разработчика
4. Завершить handlers для всех функций (см. TODO.md)
5. Добавить изображения в `assets/placeholders/`
6. Протестировать все функции
7. Настроить мониторинг (Sentry)

## Полезные команды

```bash
# Проверка статуса Celery
celery -A workers.celery_app status

# Мониторинг Celery (Flower)
pip install flower
celery -A workers.celery_app flower
# Открыть http://localhost:5555

# Бэкап БД
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Просмотр логов бота
tail -f logs/bot.log

# Очистка temp файлов
rm -rf temp/*

# Проверка кода
flake8 .
black .
mypy .
```

## Контакты

По вопросам: @creometric

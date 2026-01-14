# Архитектура проекта CreoMetrics Bot

## Общая схема

```
┌─────────────┐
│  Telegram   │
│   Users     │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│     Telegram Bot (main.py)      │
│  ┌──────────────────────────┐   │
│  │   Handlers & Keyboards   │   │
│  │   Middlewares & Filters  │   │
│  └────────────┬─────────────┘   │
└───────────────┼─────────────────┘
                │
        ┌───────┴───────┐
        │               │
        ▼               ▼
┌──────────────┐  ┌──────────────┐
│  PostgreSQL  │  │    Redis     │
│   Database   │  │  (Celery)    │
└──────────────┘  └───────┬──────┘
                          │
                          ▼
                  ┌──────────────┐
                  │    Celery    │
                  │   Workers    │
                  └───────┬──────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│Uniquification│  │  Conversion  │  │  Download    │
│   Workers    │  │   Workers    │  │   Workers    │
└──────────────┘  └──────────────┘  └──────────────┘
```

## Компоненты

### 1. Telegram Bot Layer

**Файлы**: `bot/`, `main.py`

**Ответственность**:
- Прием сообщений от пользователей
- Валидация и проверки (подписка, размер файлов)
- Отправка задач в очередь
- Отображение результатов

**Компоненты**:
- `handlers/` - обработчики команд и сообщений
- `keyboards/` - клавиатуры для интерфейса
- `middlewares/` - проверка подписки, логирование
- `filters/` - фильтры для сообщений

### 2. Database Layer

**Файлы**: `database/`

**Ответственность**:
- Хранение пользователей
- Логирование действий
- Пресеты уникализации
- Настройки бота

**Модели**:
- `User` - пользователи
- `ActionLog` - журнал действий
- `UniquificationPreset` - пресеты для уникализации
- `BroadcastMessage` - рассылки
- `BotSettings` - настройки бота

### 3. Task Queue (Celery + Redis)

**Файлы**: `workers/celery_app.py`, `workers/tasks/`

**Ответственность**:
- Асинхронная обработка тяжелых задач
- Масштабирование нагрузки
- Мониторинг задач

**Задачи**:
- `uniquify_photo_task`
- `uniquify_video_task`
- `convert_mp3_to_voice_task`
- `convert_video_to_circle_task`
- `compress_video_task`
- `transcribe_video_task`
- `download_video_task`

### 4. Workers Layer

**Файлы**: `workers/`

**Ответственность**:
- Фактическая обработка медиа
- Применение эффектов
- Конвертация форматов

**Модули**:

#### `uniquification/`
- `methods.py` - методы (шумы, блики, звездочки)
- `photo_uniquifier.py` - обработка фото
- `video_uniquifier.py` - обработка видео

#### `conversion/`
- `audio_converter.py` - MP3 → voice
- `video_converter.py` - video → circle

#### `compression/`
- `video_compressor.py` - сжатие видео

#### `transcription/`
- `transcriber.py` - распознавание речи + перевод

#### `download/`
- `video_downloader.py` - yt-dlp обертка

### 5. Utilities Layer

**Файлы**: `utils/`

**Ответственность**:
- Вспомогательные функции
- Логирование в админ-чат
- Работа с файлами

**Модули**:
- `file_helpers.py` - работа с файлами
- `admin_logger.py` - логирование в админ-чат

### 6. Configuration

**Файлы**: `config/`

**Ответственность**:
- Настройки приложения
- Переменные окружения
- Константы

## Поток данных

### Пример: Уникализация фото

```
1. Пользователь отправляет фото
   ↓
2. Bot Handler получает фото
   ↓
3. Проверка подписки (middleware)
   ↓
4. Валидация размера файла
   ↓
5. Сохранение файла в temp/
   ↓
6. Создание записи в ActionLog (БД)
   ↓
7. Отправка задачи в Celery
   ↓
8. Celery Worker получает задачу
   ↓
9. PhotoUniquifier обрабатывает фото
   ↓
10. Применение методов из пресета
    - add_noise()
    - add_sparkles()
    - add_lens_flare()
    - и т.д.
    ↓
11. Сохранение результатов
    ↓
12. Обновление ActionLog (статус=COMPLETED)
    ↓
13. Bot отправляет результаты пользователю
    ↓
14. Логирование в админ-чат
    ↓
15. Очистка временных файлов
```

## Масштабирование

### Горизонтальное

- Можно запустить несколько Celery Workers
- Redis обеспечивает распределение задач
- PostgreSQL поддерживает пул соединений

### Вертикальное

- Увеличить `worker_concurrency` в Celery
- Больше памяти для обработки видео
- Использовать GPU для Whisper (если доступно)

## Безопасность

### Проверки

1. **Подписка на канал** - middleware перед каждым действием
2. **Размер файлов** - проверка перед обработкой
3. **Форматы файлов** - валидация
4. **Rate limiting** - TODO (добавить через Redis)

### Изоляция

- Временные файлы в отдельной директории
- Автоматическая очистка после обработки
- Sandboxing для FFmpeg (через subprocess)

## Мониторинг

### Логирование

1. **Application logs** - `logs/bot.log`
2. **Database logs** - таблица `action_logs`
3. **Admin chat logs** - Telegram чат
4. **Celery logs** - stdout/файл

### Метрики

- Количество пользователей
- Количество действий (по типам)
- Время обработки
- Ошибки и исключения

### Алерты

- Sentry для критичных ошибок
- Telegram уведомления админам
- Логи в файл для анализа

## Deployment (Railway)

### Services

1. **Web** - Telegram Bot (`main.py`)
2. **Worker** - Celery Workers
3. **PostgreSQL** - База данных (managed)
4. **Redis** - Очередь задач (managed)

### Environment

- Python 3.11
- System packages: ffmpeg, libopus
- Nixpacks builder

### Process

```
git push → GitHub → Railway → Build → Deploy
```

## Конфигурация для разных окружений

### Development
```env
DEBUG=True
DATABASE_URL=postgresql://localhost/creo_bot_dev
REDIS_URL=redis://localhost:6379/0
```

### Production
```env
DEBUG=False
DATABASE_URL=<Railway PostgreSQL>
REDIS_URL=<Railway Redis>
SENTRY_DSN=<Sentry DSN>
```

## Расширяемость

### Добавление нового метода уникализации

1. Создать функцию в `methods.py`
2. Добавить в `METHOD_REGISTRY`
3. Обновить пресет в БД
4. Готово! Бот автоматически применит

### Добавление новой функции

1. Создать worker в `workers/`
2. Создать Celery task в `workers/tasks/`
3. Создать handler в `bot/handlers/`
4. Добавить кнопку в клавиатуру
5. Зарегистрировать handler в `main.py`

### Интеграция новых сервисов

Пример: добавление GPT

1. Создать `workers/gpt/`
2. Создать `workers/tasks/gpt_tasks.py`
3. Создать `bot/handlers/gpt.py`
4. Добавить API ключи в `.env`
5. Интегрировать

## Производительность

### Bottlenecks

1. **FFmpeg операции** - самые медленные (видео)
2. **Whisper транскрибация** - требует много CPU
3. **Database queries** - оптимизировать индексами

### Оптимизации

1. **Кеширование** - проверка подписки (Redis)
2. **Пулы соединений** - БД
3. **Async where possible** - Telegram API
4. **Batch processing** - несколько файлов одновременно
5. **CDN** - для статических ресурсов (если нужно)

## Тестирование

### Unit Tests
- Workers (uniquification, conversion)
- Utils (file helpers)

### Integration Tests
- Celery tasks end-to-end
- Database operations

### E2E Tests
- Bot handlers с моками Telegram API

## Backup & Recovery

### Database Backup
```bash
pg_dump $DATABASE_URL > backup.sql
```

### Restore
```bash
psql $DATABASE_URL < backup.sql
```

### Критичные данные
- Пользователи
- Пресеты уникализации
- История действий (для статистики)

## Maintenance

### Регулярные задачи

1. **Очистка temp/** - ежедневно
2. **Backup БД** - ежедневно
3. **Анализ логов** - еженедельно
4. **Обновление зависимостей** - ежемесячно
5. **Проверка дискового пространства** - автоматически

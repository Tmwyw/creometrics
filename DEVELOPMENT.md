# Руководство разработчика

## Добавление новых методов уникализации

### Для фото

1. Создайте функцию в `workers/uniquification/methods.py`:

```python
def add_new_effect(image: Image.Image, param1: Tuple[int, int]) -> Image.Image:
    """Add new effect to image."""
    # Your implementation
    return modified_image
```

2. Добавьте метод в `METHOD_REGISTRY` в том же файле:

```python
METHOD_REGISTRY = {
    # ...
    'new_effect': add_new_effect,
}
```

3. Создайте/обновите пресет в БД с новым методом:

```json
{
  "name": "new_effect",
  "enabled": true,
  "param1": [min, max]
}
```

### Для видео

Аналогично, но в `workers/uniquification/video_uniquifier.py`

## Добавление новых handlers

1. Создайте файл в `bot/handlers/`:

```python
# bot/handlers/new_feature.py
from telegram import Update
from telegram.ext import ContextTypes

async def new_feature_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Implementation
    pass
```

2. Зарегистрируйте в `main.py`:

```python
from bot.handlers.new_feature import new_feature_handler

application.add_handler(CallbackQueryHandler(new_feature_handler, pattern="^menu_new_feature$"))
```

3. Добавьте кнопку в клавиатуру (`bot/keyboards/main_keyboards.py`)

## Работа с БД

### Добавление новых моделей

1. Создайте модель в `database/models.py`:

```python
class NewModel(Base):
    __tablename__ = 'new_models'

    id = Column(Integer, primary_key=True)
    # ...
```

2. Создайте миграцию:

```bash
# Установите alembic если еще не установлен
pip install alembic

# Инициализация (один раз)
alembic init migrations

# Создание миграции
alembic revision --autogenerate -m "Add new model"

# Применение миграции
alembic upgrade head
```

## Celery задачи

### Создание новой задачи

1. Создайте файл в `workers/tasks/` или добавьте в существующий:

```python
@celery_app.task(bind=True, name='tasks.new_task')
def new_task(self, action_log_id: int, param1: str) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        # Implementation
        return {'success': True}
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
    finally:
        db.close()
```

2. Добавьте в `workers/celery_app.py` в `include`:

```python
include=[
    # ...
    'workers.tasks.new_tasks',
]
```

## Тестирование

### Локальное тестирование

```bash
# Тест уникализации фото
python -c "
from pathlib import Path
from workers.uniquification import PhotoUniquifier
from workers.uniquification.photo_uniquifier import create_default_photo_preset

uniquifier = PhotoUniquifier(create_default_photo_preset())
results = uniquifier.uniquify(Path('test.jpg'), Path('output'), count=3)
print(f'Generated: {results}')
"
```

### Тест Celery задачи

```bash
# Запустите Celery worker
celery -A workers.celery_app worker --loglevel=debug

# В другом терминале
python -c "
from workers.tasks.uniquification_tasks import uniquify_photo_task
result = uniquify_photo_task.delay(1, '/path/to/photo.jpg', 5, 1)
print(result.get())
"
```

## Мониторинг

### Celery Flower

Для мониторинга Celery воркеров:

```bash
pip install flower
celery -A workers.celery_app flower
```

Откройте http://localhost:5555

### Логи

```bash
# Просмотр логов бота
tail -f logs/bot.log

# Просмотр логов Celery
tail -f logs/celery.log
```

## Production чеклист

- [ ] Обновлены все переменные окружения в `.env`
- [ ] Настроены бэкапы PostgreSQL
- [ ] Настроен мониторинг (Sentry DSN)
- [ ] Протестированы все основные функции
- [ ] Добавлены брендированные изображения в `assets/placeholders/`
- [ ] Настроен админ-чат для логов
- [ ] Проверена проверка подписки на канал
- [ ] Настроены права администраторов
- [ ] Проверена работа очередей Celery
- [ ] Настроены лимиты на размеры файлов

## Известные ограничения

1. **Размер файлов**: Telegram ограничивает размер файлов до 2GB для ботов, но рекомендуется держать в пределах 50MB
2. **Скорость обработки**: Видео-уникализация может занимать много времени на больших файлах
3. **Память**: Обработка больших видео требует много RAM, настройте `worker_max_tasks_per_child` в Celery
4. **FFmpeg**: Требует установки на сервере
5. **Whisper модели**: Большие модели (large) требуют GPU, используйте base/small на CPU

## Оптимизация

### Для Railway

```python
# В config/settings.py увеличьте timeouts
CELERY_TASK_TIME_LIMIT = 7200  # 2 часа
```

### Для уменьшения использования памяти

```python
# В workers/celery_app.py
celery_app.conf.update(
    worker_max_tasks_per_child=10,  # Уменьшите если много утечек памяти
    worker_prefetch_multiplier=1,   # Не берем задачи заранее
)
```

## FAQ

**Q: Бот не отвечает на команды**
A: Проверьте логи, убедитесь что БД доступна и токен бота правильный

**Q: Celery задачи не выполняются**
A: Убедитесь что Redis запущен и Celery worker работает

**Q: Ошибка "FFmpeg not found"**
A: Установите FFmpeg и добавьте в PATH

**Q: Транскрибация работает медленно**
A: Используйте faster-whisper и модель 'base' вместо 'large'

**Q: Как добавить нового администратора?**
A: Добавьте Telegram ID в переменную окружения `ADMIN_USER_IDS`

**Q: Как изменить настройки уникализации?**
A: Через админ-панель бота или напрямую в БД таблица `uniquification_presets`

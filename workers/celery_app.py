"""Celery application configuration."""

from celery import Celery
from config.settings import settings

# Create Celery app
celery_app = Celery(
    'creo_bot',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        'workers.tasks.uniquification_tasks',
        'workers.tasks.conversion_tasks',
        'workers.tasks.compression_tasks',
        'workers.tasks.transcription_tasks',
        'workers.tasks.download_tasks',
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3000,  # 50 minutes soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
)

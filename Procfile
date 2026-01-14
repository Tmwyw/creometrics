# Railway Procfile for Creo Bot
# Start both bot and Celery worker in one service

web: python main.py & celery -A workers.celery_app worker --loglevel=info --concurrency=2

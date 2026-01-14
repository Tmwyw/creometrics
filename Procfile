# Railway Procfile for Creo Bot

# Start bot
web: python main.py

# Start Celery worker
worker: celery -A workers.celery_app worker --loglevel=info --concurrency=2

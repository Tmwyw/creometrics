#!/bin/bash
set -e

echo "=== Railway Start Script ==="
echo "Testing bot imports..."
python -c "import main; print('[START] Imports OK')" || { echo "[START] Import failed!"; exit 1; }

echo "[START] Starting bot in background..."
python -u main.py 2>&1 &
BOT_PID=$!
echo "[START] Bot PID: $BOT_PID"

# Give bot time to initialize
sleep 3

echo "[START] Starting Celery worker..."
celery -A workers.celery_app worker --loglevel=info --concurrency=2 2>&1 &
CELERY_PID=$!
echo "[START] Celery PID: $CELERY_PID"

echo "[START] Both processes started. Waiting..."
wait -n
EXIT_CODE=$?
echo "[START] Process exited with code $EXIT_CODE"
exit $EXIT_CODE

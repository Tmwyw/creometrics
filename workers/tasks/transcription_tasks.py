"""Celery tasks for transcription."""

import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from workers.celery_app import celery_app
from workers.transcription import transcribe_video
from database import SessionLocal, ActionLog, ActionStatus

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name='tasks.transcribe_video')
def transcribe_video_task(
    self,
    action_log_id: int,
    input_file_path: str
) -> Dict[str, Any]:
    """Transcribe video."""
    db = SessionLocal()
    start_time = datetime.utcnow()

    try:
        action_log = db.query(ActionLog).filter(ActionLog.id == action_log_id).first()
        if action_log:
            action_log.status = ActionStatus.PROCESSING
            action_log.started_at = start_time
            db.commit()

        input_path = Path(input_file_path)
        result = transcribe_video(input_path, translate_to_russian=True)

        processing_time = (datetime.utcnow() - start_time).total_seconds()
        if action_log:
            action_log.status = ActionStatus.COMPLETED
            action_log.completed_at = datetime.utcnow()
            action_log.processing_time = processing_time
            action_log.result_count = 1
            db.commit()

        return {
            'success': True,
            'transcription': result,
            'processing_time': processing_time
        }

    except Exception as e:
        logger.error(f"Error in transcribe_video_task: {e}")
        if action_log:
            action_log.status = ActionStatus.FAILED
            action_log.error_message = str(e)
            action_log.completed_at = datetime.utcnow()
            db.commit()
        raise
    finally:
        db.close()

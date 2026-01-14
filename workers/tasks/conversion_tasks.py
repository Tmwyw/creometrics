"""Celery tasks for media conversion."""

import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from workers.celery_app import celery_app
from workers.conversion import convert_mp3_to_voice, convert_video_to_circle
from database import SessionLocal, ActionLog, ActionStatus
from config.settings import settings

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name='tasks.convert_mp3_to_voice')
def convert_mp3_to_voice_task(
    self,
    action_log_id: int,
    input_file_path: str
) -> Dict[str, Any]:
    """Convert MP3 to voice message."""
    db = SessionLocal()
    start_time = datetime.utcnow()

    try:
        action_log = db.query(ActionLog).filter(ActionLog.id == action_log_id).first()
        if action_log:
            action_log.status = ActionStatus.PROCESSING
            action_log.started_at = start_time
            db.commit()

        input_path = Path(input_file_path)
        output_path = convert_mp3_to_voice(input_path)

        processing_time = (datetime.utcnow() - start_time).total_seconds()
        if action_log:
            action_log.status = ActionStatus.COMPLETED
            action_log.completed_at = datetime.utcnow()
            action_log.processing_time = processing_time
            action_log.result_count = 1
            db.commit()

        return {
            'success': True,
            'output_path': str(output_path),
            'processing_time': processing_time
        }

    except Exception as e:
        logger.error(f"Error in convert_mp3_to_voice_task: {e}")
        if action_log:
            action_log.status = ActionStatus.FAILED
            action_log.error_message = str(e)
            action_log.completed_at = datetime.utcnow()
            db.commit()
        raise
    finally:
        db.close()


@celery_app.task(bind=True, name='tasks.convert_video_to_circle')
def convert_video_to_circle_task(
    self,
    action_log_id: int,
    input_file_path: str
) -> Dict[str, Any]:
    """Convert video to video message (circle)."""
    db = SessionLocal()
    start_time = datetime.utcnow()

    try:
        action_log = db.query(ActionLog).filter(ActionLog.id == action_log_id).first()
        if action_log:
            action_log.status = ActionStatus.PROCESSING
            action_log.started_at = start_time
            db.commit()

        input_path = Path(input_file_path)
        output_path = convert_video_to_circle(
            input_path,
            max_duration=settings.MAX_VIDEO_CIRCLE_DURATION
        )

        processing_time = (datetime.utcnow() - start_time).total_seconds()
        if action_log:
            action_log.status = ActionStatus.COMPLETED
            action_log.completed_at = datetime.utcnow()
            action_log.processing_time = processing_time
            action_log.result_count = 1
            db.commit()

        return {
            'success': True,
            'output_path': str(output_path),
            'processing_time': processing_time
        }

    except Exception as e:
        logger.error(f"Error in convert_video_to_circle_task: {e}")
        if action_log:
            action_log.status = ActionStatus.FAILED
            action_log.error_message = str(e)
            action_log.completed_at = datetime.utcnow()
            db.commit()
        raise
    finally:
        db.close()

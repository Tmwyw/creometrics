"""Celery tasks for uniquification."""

import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from workers.celery_app import celery_app
from workers.uniquification import PhotoUniquifier, VideoUniquifier
from database import SessionLocal, ActionLog, ActionStatus, UniquificationPreset, MediaType
from config.settings import settings

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name='tasks.uniquify_photo')
def uniquify_photo_task(
    self,
    action_log_id: int,
    input_file_path: str,
    copies_count: int,
    preset_id: int,
    file_format: str = 'jpeg',
    flip_horizontal: bool = False,
    overlay_text: str = None,
    overlay_photo_path: str = None,
    overlay_position: str = None,
    overlay_opacity: int = None
) -> Dict[str, Any]:
    """Task to uniquify photo.

    Args:
        self: Task instance
        action_log_id: Action log ID
        input_file_path: Path to input photo
        copies_count: Number of copies to generate
        preset_id: Preset ID to use
        file_format: Output file format (jpeg, png, webp)
        flip_horizontal: Whether to flip horizontally
        overlay_text: Text to overlay on image
        overlay_photo_path: Path to photo to overlay
        overlay_position: Position of overlay (top_left, top_right, etc.)
        overlay_opacity: Opacity of overlay (0-100)

    Returns:
        Dictionary with result paths
    """
    db = SessionLocal()
    start_time = datetime.utcnow()

    try:
        # Update action log status
        action_log = db.query(ActionLog).filter(ActionLog.id == action_log_id).first()
        if action_log:
            action_log.status = ActionStatus.PROCESSING
            action_log.started_at = start_time
            db.commit()

        # Get preset
        preset = db.query(UniquificationPreset).filter(
            UniquificationPreset.id == preset_id,
            UniquificationPreset.media_type == MediaType.PHOTO
        ).first()

        if not preset:
            raise ValueError(f"Preset {preset_id} not found")

        # Create uniquifier with additional options
        config = preset.config.copy()
        config['file_format'] = file_format
        config['flip_horizontal'] = flip_horizontal
        if overlay_text:
            config['overlay_text'] = overlay_text
        if overlay_photo_path:
            config['overlay_photo_path'] = overlay_photo_path
            config['overlay_position'] = overlay_position
            config['overlay_opacity'] = overlay_opacity

        uniquifier = PhotoUniquifier(config)

        # Process
        input_path = Path(input_file_path)
        output_dir = settings.TEMP_DIR / f"photo_{action_log_id}"
        output_paths = uniquifier.uniquify(input_path, output_dir, copies_count)

        # Update action log
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        if action_log:
            action_log.status = ActionStatus.COMPLETED
            action_log.completed_at = datetime.utcnow()
            action_log.processing_time = processing_time
            action_log.result_count = len(output_paths)
            db.commit()

        return {
            'success': True,
            'output_paths': [str(p) for p in output_paths],
            'count': len(output_paths),
            'processing_time': processing_time
        }

    except Exception as e:
        logger.error(f"Error in uniquify_photo_task: {e}")

        # Update action log
        if action_log:
            action_log.status = ActionStatus.FAILED
            action_log.error_message = str(e)
            action_log.completed_at = datetime.utcnow()
            db.commit()

        raise

    finally:
        db.close()


@celery_app.task(bind=True, name='tasks.uniquify_video')
def uniquify_video_task(
    self,
    action_log_id: int,
    input_file_path: str,
    copies_count: int,
    preset_id: int
) -> Dict[str, Any]:
    """Task to uniquify video.

    Args:
        self: Task instance
        action_log_id: Action log ID
        input_file_path: Path to input video
        copies_count: Number of copies to generate
        preset_id: Preset ID to use

    Returns:
        Dictionary with result paths
    """
    db = SessionLocal()
    start_time = datetime.utcnow()

    try:
        # Update action log status
        action_log = db.query(ActionLog).filter(ActionLog.id == action_log_id).first()
        if action_log:
            action_log.status = ActionStatus.PROCESSING
            action_log.started_at = start_time
            db.commit()

        # Get preset
        preset = db.query(UniquificationPreset).filter(
            UniquificationPreset.id == preset_id,
            UniquificationPreset.media_type == MediaType.VIDEO
        ).first()

        if not preset:
            raise ValueError(f"Preset {preset_id} not found")

        # Create uniquifier
        uniquifier = VideoUniquifier(preset.config)

        # Process
        input_path = Path(input_file_path)
        output_dir = settings.TEMP_DIR / f"video_{action_log_id}"
        output_paths = uniquifier.uniquify(input_path, output_dir, copies_count)

        # Update action log
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        if action_log:
            action_log.status = ActionStatus.COMPLETED
            action_log.completed_at = datetime.utcnow()
            action_log.processing_time = processing_time
            action_log.result_count = len(output_paths)
            db.commit()

        return {
            'success': True,
            'output_paths': [str(p) for p in output_paths],
            'count': len(output_paths),
            'processing_time': processing_time
        }

    except Exception as e:
        logger.error(f"Error in uniquify_video_task: {e}")

        # Update action log
        if action_log:
            action_log.status = ActionStatus.FAILED
            action_log.error_message = str(e)
            action_log.completed_at = datetime.utcnow()
            db.commit()

        raise

    finally:
        db.close()

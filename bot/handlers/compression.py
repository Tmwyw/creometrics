"""Handler for video compression."""

import logging
import asyncio
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from database import SessionLocal, User, ActionLog, ActionType, ActionStatus
from bot.keyboards import get_back_to_menu_keyboard
from bot.middlewares import subscription_required
from config.settings import settings
from workers.tasks.compression_tasks import compress_video_task
from utils.task_manager import TaskManager
from utils.admin_logger import AdminLogger

logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_VIDEO_TO_COMPRESS = 1


async def compress_video_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start video compression."""
    query = update.callback_query
    await query.answer()

    if not await subscription_required(update, context):
        return ConversationHandler.END

    text = (
        "🗜️ Сжатие видео\n\n"
        "Отправьте видео для сжатия.\n\n"
        f"Минимальный размер: 20 MB\n"
        f"Максимальный размер: {settings.MAX_VIDEO_SIZE_MB} MB\n"
        f"Целевой размер: {settings.COMPRESSED_VIDEO_TARGET_MB} MB\n\n"
        "Видео будет автоматически сжато с оптимальным битрейтом."
    )

    await query.edit_message_text(
        text=text,
        reply_markup=get_back_to_menu_keyboard()
    )

    return WAITING_FOR_VIDEO_TO_COMPRESS


async def receive_video_to_compress(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive video for compression."""
    if not await subscription_required(update, context):
        return ConversationHandler.END

    video = update.message.video
    file_size = video.file_size
    duration = video.duration

    # Check if file needs compression
    if file_size < 20 * 1024 * 1024:  # 20 MB
        await update.message.reply_text(
            f"❌ Файл слишком маленький ({file_size / (1024*1024):.1f} MB).\n"
            "Сжатие имеет смысл только для файлов больше 20 MB."
        )
        return WAITING_FOR_VIDEO_TO_COMPRESS

    if file_size > settings.MAX_VIDEO_SIZE_BYTES:
        await update.message.reply_text(
            f"❌ Файл слишком большой ({file_size / (1024*1024):.1f} MB).\n"
            f"Максимальный размер: {settings.MAX_VIDEO_SIZE_MB} MB"
        )
        return WAITING_FOR_VIDEO_TO_COMPRESS

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()

        progress_msg = await update.message.reply_text("⏳ Загрузка видео...")

        file = await context.bot.get_file(video.file_id)
        file_path = settings.TEMP_DIR / f"compress_{update.effective_user.id}_{video.file_id}.mp4"
        await file.download_to_drive(file_path)

        action_log = ActionLog(
            user_id=user.id,
            action_type=ActionType.COMPRESS_VIDEO,
            status=ActionStatus.PENDING,
            file_size=file_size,
            file_duration=duration
        )
        db.add(action_log)
        db.commit()
        db.refresh(action_log)

        admin_logger = AdminLogger(context.bot)
        await admin_logger.log_video_action(
            user_id=update.effective_user.id,
            username=update.effective_user.username,
            file_path=file_path,
            action_type="Сжатие видео",
            parameters={'target_size_mb': settings.COMPRESSED_VIDEO_TARGET_MB},
            file_size=file_size,
            duration=duration
        )

        await progress_msg.edit_text(
            f"⏳ Сжимаю видео до {settings.COMPRESSED_VIDEO_TARGET_MB} MB...\n"
            "Это может занять несколько минут."
        )

        task = compress_video_task.delay(
            action_log_id=action_log.id,
            input_file_path=str(file_path)
        )

        task_manager = TaskManager(context.bot)
        asyncio.create_task(
            task_manager.poll_and_send_results(
                task_id=task.id,
                chat_id=update.effective_chat.id,
                message_id=progress_msg.message_id,
                action_type="compress_video",
                progress_message="⏳ Сжимаю видео..."
            )
        )

    except Exception as e:
        logger.error(f"Error in receive_video_to_compress: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке. Попробуйте позже."
        )
    finally:
        db.close()

    return ConversationHandler.END

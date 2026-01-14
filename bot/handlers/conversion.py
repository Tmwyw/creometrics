"""Handlers for media conversion (MP3→voice, video→circle)."""

import logging
import asyncio
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from database import SessionLocal, User, ActionLog, ActionType, ActionStatus
from bot.keyboards import get_back_to_menu_keyboard
from bot.middlewares import subscription_required
from config.settings import settings
from workers.tasks.conversion_tasks import convert_mp3_to_voice_task, convert_video_to_circle_task
from utils.task_manager import TaskManager
from utils.admin_logger import AdminLogger

logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_MP3 = 1
WAITING_FOR_VIDEO_FOR_CIRCLE = 2


# ============== MP3 TO VOICE ==============

async def mp3_to_voice_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start MP3 to voice conversion."""
    query = update.callback_query
    await query.answer()

    if not await subscription_required(update, context):
        return ConversationHandler.END

    text = (
        "💿 Конвертация MP3 в голосовое сообщение\n\n"
        "Отправьте MP3 файл для конвертации.\n\n"
        f"Максимальный размер: {settings.MAX_AUDIO_SIZE_MB} MB"
    )

    
    # Delete menu message
    try:
        await query.message.delete()
    except Exception as e:
        logger.warning(f"Failed to delete menu message: {e}")

    await query.message.reply_text(
        text=text,
        reply_markup=get_back_to_menu_keyboard()
    )

    return WAITING_FOR_MP3


async def receive_mp3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive MP3 file from user."""
    if not await subscription_required(update, context):
        return ConversationHandler.END

    # Get audio file
    audio = update.message.audio or update.message.document

    if not audio:
        await update.message.reply_text("❌ Пожалуйста, отправьте аудио файл.")
        return WAITING_FOR_MP3

    file_size = audio.file_size

    if file_size > settings.MAX_AUDIO_SIZE_BYTES:
        await update.message.reply_text(
            f"❌ Файл слишком большой ({file_size / (1024*1024):.1f} MB).\n"
            f"Максимальный размер: {settings.MAX_AUDIO_SIZE_MB} MB"
        )
        return WAITING_FOR_MP3

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()

        # Download file
        progress_msg = await update.message.reply_text("⏳ Загрузка файла...")

        file = await context.bot.get_file(audio.file_id)
        file_path = settings.TEMP_DIR / f"mp3_{update.effective_user.id}_{audio.file_id}.mp3"
        await file.download_to_drive(file_path)

        # Create action log
        action_log = ActionLog(
            user_id=user.id,
            action_type=ActionType.MP3_TO_VOICE,
            status=ActionStatus.PENDING,
            file_size=file_size
        )
        db.add(action_log)
        db.commit()
        db.refresh(action_log)

        # Log to admin chat
        admin_logger = AdminLogger(context.bot)
        await admin_logger.log_audio_action(
            user_id=update.effective_user.id,
            username=update.effective_user.username,
            file_path=file_path,
            action_type="MP3 → Voice",
            file_size=file_size
        )

        # Send to Celery
        await progress_msg.edit_text("⏳ Конвертирую в голосовое сообщение...")

        task = convert_mp3_to_voice_task.delay(
            action_log_id=action_log.id,
            input_file_path=str(file_path)
        )

        # Poll task in background
        task_manager = TaskManager(context.bot)
        asyncio.create_task(
            task_manager.poll_and_send_results(
                task_id=task.id,
                chat_id=update.effective_chat.id,
                message_id=progress_msg.message_id,
                action_type="mp3_to_voice",
                progress_message="⏳ Конвертирую MP3 в голосовое..."
            )
        )

    except Exception as e:
        logger.error(f"Error in receive_mp3: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке. Попробуйте позже."
        )
    finally:
        db.close()

    return ConversationHandler.END


# ============== VIDEO TO CIRCLE ==============

async def video_to_circle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start video to circle conversion."""
    query = update.callback_query
    await query.answer()

    if not await subscription_required(update, context):
        return ConversationHandler.END

    text = (
        "🔵 Конвертация видео в видеосообщение (кружок)\n\n"
        "Отправьте видео для конвертации.\n\n"
        f"Максимальная длительность: {settings.MAX_VIDEO_CIRCLE_DURATION} секунд\n"
        f"Максимальный размер: {settings.MAX_VIDEO_SIZE_MB} MB\n\n"
        "Видео будет автоматически обрезано до квадрата."
    )

    
    # Delete menu message
    try:
        await query.message.delete()
    except Exception as e:
        logger.warning(f"Failed to delete menu message: {e}")

    await query.message.reply_text(
        text=text,
        reply_markup=get_back_to_menu_keyboard()
    )

    return WAITING_FOR_VIDEO_FOR_CIRCLE


async def receive_video_for_circle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive video for circle conversion."""
    if not await subscription_required(update, context):
        return ConversationHandler.END

    video = update.message.video
    file_size = video.file_size
    duration = video.duration

    if file_size > settings.MAX_VIDEO_SIZE_BYTES:
        await update.message.reply_text(
            f"❌ Файл слишком большой ({file_size / (1024*1024):.1f} MB).\n"
            f"Максимальный размер: {settings.MAX_VIDEO_SIZE_MB} MB"
        )
        return WAITING_FOR_VIDEO_FOR_CIRCLE

    if duration > settings.MAX_VIDEO_CIRCLE_DURATION * 2:  # Allow some margin
        await update.message.reply_text(
            f"⚠️ Видео слишком длинное ({duration}s). Будет обрезано до {settings.MAX_VIDEO_CIRCLE_DURATION} секунд."
        )

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()

        progress_msg = await update.message.reply_text("⏳ Загрузка видео...")

        file = await context.bot.get_file(video.file_id)
        file_path = settings.TEMP_DIR / f"video_circle_{update.effective_user.id}_{video.file_id}.mp4"
        await file.download_to_drive(file_path)

        action_log = ActionLog(
            user_id=user.id,
            action_type=ActionType.VIDEO_TO_CIRCLE,
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
            action_type="Video → Circle",
            parameters={},
            file_size=file_size,
            duration=duration
        )

        await progress_msg.edit_text("⏳ Конвертирую в видеосообщение...")

        task = convert_video_to_circle_task.delay(
            action_log_id=action_log.id,
            input_file_path=str(file_path)
        )

        task_manager = TaskManager(context.bot)
        asyncio.create_task(
            task_manager.poll_and_send_results(
                task_id=task.id,
                chat_id=update.effective_chat.id,
                message_id=progress_msg.message_id,
                action_type="video_to_circle",
                progress_message="⏳ Конвертирую видео в кружок..."
            )
        )

    except Exception as e:
        logger.error(f"Error in receive_video_for_circle: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке. Попробуйте позже."
        )
    finally:
        db.close()

    return ConversationHandler.END

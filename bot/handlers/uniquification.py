"""Handlers for photo and video uniquification."""

import logging
import asyncio
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from database import SessionLocal, User, ActionLog, ActionType, ActionStatus, UniquificationPreset, MediaType
from bot.keyboards import get_copies_count_keyboard, get_back_to_menu_keyboard
from bot.middlewares import subscription_required
from config.settings import settings
from workers.tasks.uniquification_tasks import uniquify_photo_task, uniquify_video_task
from utils.task_manager import TaskManager
from utils.admin_logger import AdminLogger

logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_PHOTO = 1
WAITING_FOR_PHOTO_COPIES = 2
WAITING_FOR_VIDEO = 3
WAITING_FOR_VIDEO_COPIES = 4


async def unique_photo_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start photo uniquification process."""
    query = update.callback_query
    await query.answer()

    # Check subscription
    if not await subscription_required(update, context):
        return ConversationHandler.END

    # Delete menu message
    try:
        await query.message.delete()
    except Exception as e:
        logger.warning(f"Failed to delete menu message: {e}")

    text = (
        "📸 Уникализация фото\n\n"
        "Отправьте фото, которое нужно уникализировать.\n"
        "Поддерживаются форматы: JPG, PNG, WEBP"
    )

    # Send new message
    await query.message.reply_text(
        text=text,
        reply_markup=get_back_to_menu_keyboard()
    )

    return WAITING_FOR_PHOTO


async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive photo from user."""
    # Check subscription
    if not await subscription_required(update, context):
        return ConversationHandler.END

    # Get photo
    photo = update.message.photo[-1]  # Get largest size

    # Check file size
    file_size = photo.file_size
    if file_size > settings.MAX_PHOTO_SIZE_BYTES:
        await update.message.reply_text(
            f"❌ Файл слишком большой. Максимальный размер: {settings.MAX_PHOTO_SIZE_MB}MB"
        )
        return WAITING_FOR_PHOTO

    # Store file info in context
    context.user_data['photo_file_id'] = photo.file_id
    context.user_data['photo_file_size'] = file_size

    # Ask for copies count
    text = (
        "✅ Фото получено!\n\n"
        "Выберите количество уникальных копий (от 1 до 10):"
    )

    await update.message.reply_text(
        text=text,
        reply_markup=get_copies_count_keyboard()
    )

    return WAITING_FOR_PHOTO_COPIES


async def process_photo_uniquification(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process photo uniquification."""
    query = update.callback_query
    await query.answer()

    # Check subscription
    if not await subscription_required(update, context):
        return ConversationHandler.END

    # Get copies count from callback
    copies_count = int(query.data.split('_')[1])

    # Get file info from context
    file_id = context.user_data.get('photo_file_id')
    file_size = context.user_data.get('photo_file_size', 0)

    if not file_id:
        await query.edit_message_text("❌ Ошибка: файл не найден")
        return ConversationHandler.END

    db = SessionLocal()

    try:
        # Get user
        user = db.query(User).filter(
            User.telegram_id == update.effective_user.id
        ).first()

        # Get default preset
        preset = db.query(UniquificationPreset).filter(
            UniquificationPreset.media_type == MediaType.PHOTO,
            UniquificationPreset.is_default == True
        ).first()

        if not preset:
            await query.edit_message_text(
                "❌ Ошибка: пресет не найден. Обратитесь к администратору."
            )
            return ConversationHandler.END

        # Download file
        progress_msg = await query.edit_message_text("⏳ Загрузка файла...")

        file = await context.bot.get_file(file_id)
        file_path = settings.TEMP_DIR / f"photo_{update.effective_user.id}_{file_id}.jpg"
        await file.download_to_drive(file_path)

        # Create action log
        action_log = ActionLog(
            user_id=user.id,
            action_type=ActionType.UNIQUE_PHOTO,
            status=ActionStatus.PENDING,
            file_size=file_size,
            parameters={'copies_count': copies_count},
            preset_id=preset.id
        )
        db.add(action_log)
        db.commit()
        db.refresh(action_log)

        # Log to admin chat
        admin_logger = AdminLogger(context.bot)
        await admin_logger.log_photo_action(
            user_id=update.effective_user.id,
            username=update.effective_user.username,
            file_path=file_path,
            action_type="Уникализация фото",
            copies_count=copies_count,
            file_size=file_size
        )

        # Send to Celery
        await progress_msg.edit_text(
            f"⏳ Создаю {copies_count} уникальных копий...\n"
            "Это может занять некоторое время."
        )

        task = uniquify_photo_task.delay(
            action_log_id=action_log.id,
            input_file_path=str(file_path),
            copies_count=copies_count,
            preset_id=preset.id
        )

        # Poll task in background
        task_manager = TaskManager(context.bot)
        asyncio.create_task(
            task_manager.poll_and_send_results(
                task_id=task.id,
                chat_id=update.effective_chat.id,
                message_id=progress_msg.message_id,
                action_type="unique_photo",
                progress_message=f"⏳ Создаю {copies_count} уникальных копий фото..."
            )
        )

    except Exception as e:
        logger.error(f"Error in process_photo_uniquification: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка при обработке. Попробуйте позже.",
            reply_markup=get_back_to_menu_keyboard()
        )

    finally:
        db.close()

    return ConversationHandler.END


# ============== VIDEO UNIQUIFICATION ==============

async def unique_video_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start video uniquification process."""
    query = update.callback_query
    await query.answer()

    if not await subscription_required(update, context):
        return ConversationHandler.END

    # Delete menu message
    try:
        await query.message.delete()
    except Exception as e:
        logger.warning(f"Failed to delete menu message: {e}")

    text = (
        "🎬 Уникализация видео\n\n"
        "Отправьте видео, которое нужно уникализировать.\n"
        "Поддерживаются форматы: MP4, MOV, AVI\n\n"
        f"Максимальный размер: {settings.MAX_VIDEO_SIZE_MB} MB"
    )

    await query.message.reply_text(
        text=text,
        reply_markup=get_back_to_menu_keyboard()
    )

    return WAITING_FOR_VIDEO


async def receive_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive video from user."""
    if not await subscription_required(update, context):
        return ConversationHandler.END

    video = update.message.video
    file_size = video.file_size

    if file_size > settings.MAX_VIDEO_SIZE_BYTES:
        await update.message.reply_text(
            f"❌ Файл слишком большой ({file_size / (1024*1024):.1f} MB).\n"
            f"Максимальный размер: {settings.MAX_VIDEO_SIZE_MB} MB"
        )
        return WAITING_FOR_VIDEO

    context.user_data['video_file_id'] = video.file_id
    context.user_data['video_file_size'] = file_size
    context.user_data['video_duration'] = video.duration

    text = (
        "✅ Видео получено!\n\n"
        "Выберите количество уникальных копий (от 1 до 10):"
    )

    await update.message.reply_text(
        text=text,
        reply_markup=get_copies_count_keyboard()
    )

    return WAITING_FOR_VIDEO_COPIES


async def process_video_uniquification(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process video uniquification."""
    query = update.callback_query
    await query.answer()

    if not await subscription_required(update, context):
        return ConversationHandler.END

    copies_count = int(query.data.split('_')[1])
    file_id = context.user_data.get('video_file_id')
    file_size = context.user_data.get('video_file_size', 0)
    duration = context.user_data.get('video_duration', 0)

    if not file_id:
        await query.edit_message_text("❌ Ошибка: файл не найден")
        return ConversationHandler.END

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
        preset = db.query(UniquificationPreset).filter(
            UniquificationPreset.media_type == MediaType.VIDEO,
            UniquificationPreset.is_default == True
        ).first()

        if not preset:
            await query.edit_message_text(
                "❌ Ошибка: пресет не найден. Обратитесь к администратору."
            )
            return ConversationHandler.END

        progress_msg = await query.edit_message_text("⏳ Загрузка видео...")

        file = await context.bot.get_file(file_id)
        file_path = settings.TEMP_DIR / f"video_{update.effective_user.id}_{file_id}.mp4"
        await file.download_to_drive(file_path)

        action_log = ActionLog(
            user_id=user.id,
            action_type=ActionType.UNIQUE_VIDEO,
            status=ActionStatus.PENDING,
            file_size=file_size,
            file_duration=duration,
            parameters={'copies_count': copies_count},
            preset_id=preset.id
        )
        db.add(action_log)
        db.commit()
        db.refresh(action_log)

        admin_logger = AdminLogger(context.bot)
        await admin_logger.log_video_action(
            user_id=update.effective_user.id,
            username=update.effective_user.username,
            file_path=file_path,
            action_type="Уникализация видео",
            parameters={'copies_count': copies_count},
            file_size=file_size,
            duration=duration
        )

        await progress_msg.edit_text(
            f"⏳ Создаю {copies_count} уникальных копий видео...\n"
            "⚠️ Это может занять несколько минут."
        )

        task = uniquify_video_task.delay(
            action_log_id=action_log.id,
            input_file_path=str(file_path),
            copies_count=copies_count,
            preset_id=preset.id
        )

        task_manager = TaskManager(context.bot)
        asyncio.create_task(
            task_manager.poll_and_send_results(
                task_id=task.id,
                chat_id=update.effective_chat.id,
                message_id=progress_msg.message_id,
                action_type="unique_video",
                progress_message=f"⏳ Создаю {copies_count} уникальных копий видео..."
            )
        )

    except Exception as e:
        logger.error(f"Error in process_video_uniquification: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка при обработке. Попробуйте позже.",
            reply_markup=get_back_to_menu_keyboard()
        )
    finally:
        db.close()

    return ConversationHandler.END

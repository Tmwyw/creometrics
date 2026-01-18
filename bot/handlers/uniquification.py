"""Handlers for photo and video uniquification."""

import logging
import asyncio
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from database import SessionLocal, User, ActionLog, ActionType, ActionStatus, UniquificationPreset, MediaType
from bot.keyboards import (
    get_copies_count_keyboard,
    get_back_to_menu_keyboard,
    get_file_format_keyboard,
    get_yes_no_keyboard,
    get_intensity_keyboard,
    get_overlay_position_keyboard,
    get_send_type_keyboard,
)
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
WAITING_FOR_INTENSITY = 5
WAITING_FOR_FILE_FORMAT = 6
WAITING_FOR_FLIP_CHOICE = 7
WAITING_FOR_TEXT_CHOICE = 8
WAITING_FOR_TEXT_INPUT = 9
WAITING_FOR_OVERLAY_CHOICE = 10
WAITING_FOR_OVERLAY_PHOTO = 11
WAITING_FOR_OVERLAY_POSITION = 12
WAITING_FOR_OVERLAY_OPACITY = 13
WAITING_FOR_SEND_TYPE = 14


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


async def select_copies_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Select number of copies."""
    query = update.callback_query
    await query.answer()

    # Check subscription
    if not await subscription_required(update, context):
        return ConversationHandler.END

    # Get copies count from callback
    copies_count = int(query.data.split('_')[1])

    # Store copies count in context
    context.user_data['copies_count'] = copies_count

    # Ask for intensity
    await query.edit_message_text(
        "⚡ Выберите интенсивность уникализации:\n\n"
        "🟢 Слабая — минимальные незаметные изменения\n"
        "🟡 Средняя — умеренные изменения\n"
        "🔴 Сильная — максимальные изменения",
        reply_markup=get_intensity_keyboard()
    )

    return WAITING_FOR_INTENSITY


async def select_intensity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Select uniquification intensity."""
    query = update.callback_query
    await query.answer()

    # Check subscription
    if not await subscription_required(update, context):
        return ConversationHandler.END

    # Get intensity from callback
    intensity = query.data.split('_')[1]  # low, medium, high
    context.user_data['intensity'] = intensity

    # Ask for file format
    await query.edit_message_text(
        "📁 Выберите формат файла:",
        reply_markup=get_file_format_keyboard()
    )

    return WAITING_FOR_FILE_FORMAT


async def select_file_format(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Select file format."""
    query = update.callback_query
    await query.answer()

    # Check subscription
    if not await subscription_required(update, context):
        return ConversationHandler.END

    # Get format from callback
    file_format = query.data.split('_')[1]  # jpeg, png, webp
    context.user_data['file_format'] = file_format

    # Ask about flipping
    await query.edit_message_text(
        "🔄 Отразить по горизонтали?",
        reply_markup=get_yes_no_keyboard()
    )

    return WAITING_FOR_FLIP_CHOICE


async def select_flip_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Select flip choice."""
    query = update.callback_query
    await query.answer()

    # Check subscription
    if not await subscription_required(update, context):
        return ConversationHandler.END

    # Get answer from callback
    flip = query.data == 'answer_yes'
    context.user_data['flip_horizontal'] = flip

    # Ask about text
    await query.edit_message_text(
        "✍️ Добавить текст?",
        reply_markup=get_yes_no_keyboard()
    )

    return WAITING_FOR_TEXT_CHOICE


async def select_text_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Select text choice."""
    query = update.callback_query
    await query.answer()

    # Check subscription
    if not await subscription_required(update, context):
        return ConversationHandler.END

    # Get answer from callback
    if query.data == 'answer_yes':
        # Ask for text input
        await query.edit_message_text(
            "✍️ Введите текст, который нужно добавить на фото:\n\n"
            "(Отправьте текстовое сообщение)"
        )
        return WAITING_FOR_TEXT_INPUT
    else:
        # No text, proceed to overlay question
        context.user_data['overlay_text'] = None
        await query.edit_message_text(
            "➕ Добавить дополнительное фото?",
            reply_markup=get_yes_no_keyboard()
        )
        return WAITING_FOR_OVERLAY_CHOICE


async def receive_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive text input from user."""
    # Check subscription
    if not await subscription_required(update, context):
        return ConversationHandler.END

    # Get text from message
    text = update.message.text
    context.user_data['overlay_text'] = text

    # Ask about overlay photo
    await update.message.reply_text(
        "➕ Добавить дополнительное фото?",
        reply_markup=get_yes_no_keyboard()
    )

    return WAITING_FOR_OVERLAY_CHOICE


async def select_overlay_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Select overlay choice."""
    query = update.callback_query
    await query.answer()

    # Check subscription
    if not await subscription_required(update, context):
        return ConversationHandler.END

    # Get answer from callback
    if query.data == 'answer_yes':
        # Ask for overlay photo
        await query.edit_message_text(
            "📷 Отправьте дополнительное фото, которое будет наложено на основное:"
        )
        return WAITING_FOR_OVERLAY_PHOTO
    else:
        # No overlay, ask about send type
        context.user_data['overlay_photo_id'] = None
        await query.edit_message_text(
            "📤 Как отправить результаты?\n\n"
            "📸 Сжатое — быстрая отправка, Telegram сжимает фото\n"
            "📄 Без сжатия — отправка файлом, без потери качества",
            reply_markup=get_send_type_keyboard()
        )
        return WAITING_FOR_SEND_TYPE


async def receive_overlay_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive overlay photo from user."""
    # Check subscription
    if not await subscription_required(update, context):
        return ConversationHandler.END

    # Get photo
    photo = update.message.photo[-1]  # Get largest size
    context.user_data['overlay_photo_id'] = photo.file_id

    # Ask for position
    await update.message.reply_text(
        "📍 Выберите позицию дополнительного фото:",
        reply_markup=get_overlay_position_keyboard()
    )

    return WAITING_FOR_OVERLAY_POSITION


async def select_overlay_position(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Select overlay position."""
    query = update.callback_query
    await query.answer()

    # Check subscription
    if not await subscription_required(update, context):
        return ConversationHandler.END

    # Get position from callback
    position = query.data.split('_', 1)[1]  # top_left, top_right, etc.
    context.user_data['overlay_position'] = position

    # Ask for opacity
    await query.edit_message_text(
        "🎨 Введите непрозрачность дополнительного фото (0-100):\n\n"
        "0 = полностью прозрачное\n"
        "100 = полностью непрозрачное\n\n"
        "(Отправьте число от 0 до 100)"
    )

    return WAITING_FOR_OVERLAY_OPACITY


async def receive_overlay_opacity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive overlay opacity from user."""
    # Check subscription
    if not await subscription_required(update, context):
        return ConversationHandler.END

    # Get opacity from message
    try:
        opacity = int(update.message.text)
        if opacity < 0 or opacity > 100:
            await update.message.reply_text(
                "❌ Введите число от 0 до 100"
            )
            return WAITING_FOR_OVERLAY_OPACITY

        context.user_data['overlay_opacity'] = opacity

        # Ask about send type
        await update.message.reply_text(
            "📤 Как отправить результаты?\n\n"
            "📸 Сжатое — быстрая отправка, Telegram сжимает фото\n"
            "📄 Без сжатия — отправка файлом, без потери качества",
            reply_markup=get_send_type_keyboard()
        )
        return WAITING_FOR_SEND_TYPE

    except ValueError:
        await update.message.reply_text(
            "❌ Введите корректное число от 0 до 100"
        )
        return WAITING_FOR_OVERLAY_OPACITY


async def select_send_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Select send type (compressed or document)."""
    query = update.callback_query
    await query.answer()

    # Check subscription
    if not await subscription_required(update, context):
        return ConversationHandler.END

    # Get send type from callback
    send_type = query.data.split('_')[1]  # compressed or document
    context.user_data['send_as_document'] = (send_type == 'document')

    # Now process the uniquification
    return await process_photo_uniquification(update, context)


async def process_photo_uniquification(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process photo uniquification."""
    query = update.callback_query
    await query.answer()

    # Check subscription
    if not await subscription_required(update, context):
        return ConversationHandler.END

    # Get all parameters from context
    copies_count = context.user_data.get('copies_count')
    intensity = context.user_data.get('intensity', 'low')
    file_id = context.user_data.get('photo_file_id')
    file_size = context.user_data.get('photo_file_size', 0)
    file_format = context.user_data.get('file_format', 'jpeg')
    flip_horizontal = context.user_data.get('flip_horizontal', False)
    overlay_text = context.user_data.get('overlay_text')
    overlay_photo_id = context.user_data.get('overlay_photo_id')
    overlay_position = context.user_data.get('overlay_position')
    overlay_opacity = context.user_data.get('overlay_opacity')
    send_as_document = context.user_data.get('send_as_document', False)

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

        # Download overlay photo if needed
        overlay_file_path = None
        if overlay_photo_id:
            overlay_file = await context.bot.get_file(overlay_photo_id)
            overlay_file_path = settings.TEMP_DIR / f"overlay_{update.effective_user.id}_{overlay_photo_id}.jpg"
            await overlay_file.download_to_drive(overlay_file_path)
            overlay_file_path = str(overlay_file_path)

        # Create action log
        parameters = {
            'copies_count': copies_count,
            'file_format': file_format,
            'flip_horizontal': flip_horizontal,
        }
        if overlay_text:
            parameters['overlay_text'] = overlay_text
        if overlay_photo_id:
            parameters['overlay_photo'] = True
            parameters['overlay_position'] = overlay_position
            parameters['overlay_opacity'] = overlay_opacity

        action_log = ActionLog(
            user_id=user.id,
            action_type=ActionType.UNIQUE_PHOTO,
            status=ActionStatus.PENDING,
            file_size=file_size,
            parameters=parameters,
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
            preset_id=preset.id,
            intensity=intensity,
            file_format=file_format,
            flip_horizontal=flip_horizontal,
            overlay_text=overlay_text,
            overlay_photo_path=overlay_file_path,
            overlay_position=overlay_position,
            overlay_opacity=overlay_opacity
        )

        # Poll task in background
        task_manager = TaskManager(context.bot)
        asyncio.create_task(
            task_manager.poll_and_send_results(
                task_id=task.id,
                chat_id=update.effective_chat.id,
                message_id=progress_msg.message_id,
                action_type="unique_photo",
                progress_message=f"⏳ Создаю {copies_count} уникальных копий фото...",
                send_as_document=send_as_document
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

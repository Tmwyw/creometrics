"""Handler for video downloading from YouTube/Instagram."""

import logging
import asyncio
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from database import SessionLocal, User, ActionLog, ActionType, ActionStatus
from bot.keyboards import get_back_to_menu_keyboard, get_video_quality_keyboard
from bot.middlewares import subscription_required
from config.settings import settings
from workers.tasks.download_tasks import download_video_task
from workers.download import VideoDownloader
from utils.task_manager import TaskManager

logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_URL = 1
WAITING_FOR_QUALITY_SELECTION = 2


async def download_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start video download."""
    query = update.callback_query
    await query.answer()

    if not await subscription_required(update, context):
        return ConversationHandler.END

    text = (
        "📥 Скачивание видео\n\n"
        "Отправьте ссылку на видео:\n"
        "• YouTube (youtube.com, youtu.be)\n"
        "• Instagram (instagram.com)\n\n"
        "Поддерживаются только публичные видео."
    )

    await query.edit_message_text(
        text=text,
        reply_markup=get_back_to_menu_keyboard()
    )

    return WAITING_FOR_URL


async def receive_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive URL from user."""
    if not await subscription_required(update, context):
        return ConversationHandler.END

    url = update.message.text.strip()

    # Basic URL validation
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text(
            "❌ Некорректная ссылка. Пожалуйста, отправьте полную URL."
        )
        return WAITING_FOR_URL

    # Check if supported
    supported_domains = ['youtube.com', 'youtu.be', 'instagram.com', 'instagr.am']
    if not any(domain in url.lower() for domain in supported_domains):
        await update.message.reply_text(
            "❌ Эта платформа не поддерживается.\n"
            "Доступны: YouTube, Instagram"
        )
        return WAITING_FOR_URL

    progress_msg = await update.message.reply_text("⏳ Получаю информацию о видео...")

    try:
        # Get available formats
        downloader = VideoDownloader(settings.TEMP_DIR)
        formats = downloader.get_available_formats(url)

        if not formats:
            await progress_msg.edit_text(
                "❌ Не удалось получить форматы видео.\n"
                "Проверьте ссылку и попробуйте снова."
            )
            return WAITING_FOR_URL

        # Store URL and formats in context
        context.user_data['download_url'] = url
        context.user_data['download_formats'] = formats

        # Show quality selection
        text = "✅ Видео найдено!\n\nВыберите качество:"

        await progress_msg.edit_text(
            text=text,
            reply_markup=get_video_quality_keyboard(formats[:5])  # Top 5 formats
        )

        return WAITING_FOR_QUALITY_SELECTION

    except Exception as e:
        logger.error(f"Error getting video formats: {e}")
        await progress_msg.edit_text(
            "❌ Ошибка при получении информации о видео.\n"
            "Проверьте ссылку или попробуйте позже."
        )
        return WAITING_FOR_URL


async def process_download(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process video download."""
    query = update.callback_query
    await query.answer()

    if not await subscription_required(update, context):
        return ConversationHandler.END

    format_id = query.data.split('_')[1]
    url = context.user_data.get('download_url')

    if not url:
        await query.edit_message_text("❌ Ошибка: URL не найден")
        return ConversationHandler.END

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()

        # Determine action type based on URL
        if 'youtube' in url.lower() or 'youtu.be' in url.lower():
            action_type = ActionType.DOWNLOAD_YOUTUBE
        else:
            action_type = ActionType.DOWNLOAD_INSTAGRAM

        action_log = ActionLog(
            user_id=user.id,
            action_type=action_type,
            status=ActionStatus.PENDING,
            parameters={'url': url, 'format_id': format_id}
        )
        db.add(action_log)
        db.commit()
        db.refresh(action_log)

        progress_msg = await query.edit_message_text(
            "⏳ Скачиваю видео...\n"
            "Это может занять несколько минут."
        )

        task = download_video_task.delay(
            action_log_id=action_log.id,
            url=url,
            format_id=format_id
        )

        task_manager = TaskManager(context.bot)
        asyncio.create_task(
            task_manager.poll_and_send_results(
                task_id=task.id,
                chat_id=update.effective_chat.id,
                message_id=progress_msg.message_id,
                action_type="download",
                progress_message="⏳ Скачиваю видео..."
            )
        )

    except Exception as e:
        logger.error(f"Error in process_download: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка при скачивании. Попробуйте позже."
        )
    finally:
        db.close()

    return ConversationHandler.END

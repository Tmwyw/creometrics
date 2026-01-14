"""Subscription check middleware."""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from config.settings import settings
from bot.keyboards.main_keyboards import get_subscription_keyboard

logger = logging.getLogger(__name__)


async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user is subscribed to required channel.

    Args:
        update: Update object
        context: Context object

    Returns:
        True if subscribed, False otherwise
    """
    user_id = update.effective_user.id

    # Skip check for admins
    if user_id in settings.ADMIN_USER_IDS:
        return True

    try:
        # Check membership
        member = await context.bot.get_chat_member(
            chat_id=settings.REQUIRED_CHANNEL_ID,
            user_id=user_id
        )

        # Check if user is member or admin
        if member.status in ['member', 'administrator', 'creator']:
            return True

        return False

    except TelegramError as e:
        logger.error(f"Error checking subscription: {e}")
        # In case of error, allow access (to prevent blocking users due to bot issues)
        return True


async def subscription_required(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Middleware to check subscription before allowing action.

    Args:
        update: Update object
        context: Context object

    Returns:
        True if user can proceed, False otherwise
    """
    if await check_subscription(update, context):
        return True

    # User is not subscribed
    text = (
        "⚠️ Для использования бота необходимо подписаться на наш канал.\n\n"
        f"Подпишитесь на канал {settings.REQUIRED_CHANNEL} "
        "и нажмите кнопку ниже."
    )

    keyboard = get_subscription_keyboard(
        f"https://t.me/{settings.REQUIRED_CHANNEL.lstrip('@')}"
    )

    if update.callback_query:
        await update.callback_query.answer(
            "Необходима подписка на канал!",
            show_alert=True
        )
        await update.callback_query.message.reply_text(
            text,
            reply_markup=keyboard
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=keyboard
        )

    return False

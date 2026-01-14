"""Start command handler."""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import SessionLocal, User
from bot.keyboards import get_main_menu_keyboard
from bot.middlewares import subscription_required
from config.settings import settings

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user = update.effective_user
    db = SessionLocal()

    try:
        # Get or create user in database
        db_user = db.query(User).filter(User.telegram_id == user.id).first()

        if not db_user:
            # Create new user
            db_user = User(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                is_admin=user.id in settings.ADMIN_USER_IDS
            )
            db.add(db_user)
            db.commit()
            logger.info(f"New user registered: {user.id} (@{user.username})")
        else:
            # Update user info
            db_user.username = user.username
            db_user.first_name = user.first_name
            db_user.last_name = user.last_name
            db.commit()

        # Check subscription
        if not await subscription_required(update, context):
            return

        # Send welcome message with main menu
        welcome_text = (
            f"👋 Привет, {user.first_name}!\n\n"
            "🤖 Я - CreoMetrics бот для обработки медиа!\n\n"
            "Выберите нужную функцию из меню ниже:"
        )

        await update.message.reply_text(
            welcome_text,
            reply_markup=get_main_menu_keyboard()
        )

    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка. Попробуйте позже."
        )
    finally:
        db.close()


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle main menu callback."""
    query = update.callback_query
    await query.answer()

    # Check subscription
    if not await subscription_required(update, context):
        return

    # Show main menu
    text = (
        "🏠 Главное меню\n\n"
        "Выберите нужную функцию:"
    )

    await query.edit_message_text(
        text=text,
        reply_markup=get_main_menu_keyboard()
    )

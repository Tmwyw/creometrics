"""Admin panel handlers."""

import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from sqlalchemy import func, desc

from database import SessionLocal, User, ActionLog, ActionType, ActionStatus, UniquificationPreset
from bot.keyboards import get_admin_menu_keyboard, get_back_to_menu_keyboard
from config.settings import settings

logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_BROADCAST_TEXT = 1


def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    return user_id in settings.ADMIN_USER_IDS


async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show admin menu."""
    query = update.callback_query
    if query:
        await query.answer()

    user_id = update.effective_user.id

    if not is_admin(user_id):
        text = "❌ У вас нет доступа к админ-панели."
        if query:
            await query.edit_message_text(text)
        else:
            await update.message.reply_text(text)
        return

    text = (
        "⚙️ Админ-панель\n\n"
        "Выберите действие:"
    )

    if query:
        await query.edit_message_text(
            text=text,
            reply_markup=get_admin_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            text=text,
            reply_markup=get_admin_menu_keyboard()
        )


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show statistics."""
    query = update.callback_query
    await query.answer()

    if not is_admin(update.effective_user.id):
        await query.edit_message_text("❌ Доступ запрещен")
        return

    db = SessionLocal()

    try:
        # Total users
        total_users = db.query(func.count(User.id)).scalar()

        # Active users (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        active_users = db.query(func.count(User.id)).filter(
            User.last_activity >= week_ago
        ).scalar()

        # Total actions
        total_actions = db.query(func.count(ActionLog.id)).scalar()

        # Actions by type
        actions_by_type = db.query(
            ActionLog.action_type,
            func.count(ActionLog.id)
        ).group_by(ActionLog.action_type).all()

        # Success rate
        successful = db.query(func.count(ActionLog.id)).filter(
            ActionLog.status == ActionStatus.COMPLETED
        ).scalar()

        failed = db.query(func.count(ActionLog.id)).filter(
            ActionLog.status == ActionStatus.FAILED
        ).scalar()

        success_rate = (successful / total_actions * 100) if total_actions > 0 else 0

        # Recent actions (last 24h)
        day_ago = datetime.utcnow() - timedelta(days=1)
        recent_actions = db.query(func.count(ActionLog.id)).filter(
            ActionLog.created_at >= day_ago
        ).scalar()

        text = (
            "📊 Статистика бота\n\n"
            f"👥 Всего пользователей: {total_users}\n"
            f"🟢 Активных (7 дней): {active_users}\n\n"
            f"📋 Всего операций: {total_actions}\n"
            f"📈 За последние 24ч: {recent_actions}\n"
            f"✅ Успешно: {successful} ({success_rate:.1f}%)\n"
            f"❌ Ошибок: {failed}\n\n"
            "📊 По типам:\n"
        )

        for action_type, count in actions_by_type:
            type_emoji = {
                ActionType.UNIQUE_PHOTO: "📸",
                ActionType.UNIQUE_VIDEO: "🎬",
                ActionType.MP3_TO_VOICE: "💿",
                ActionType.VIDEO_TO_CIRCLE: "🔵",
                ActionType.COMPRESS_VIDEO: "🗜️",
                ActionType.TRANSCRIBE: "📝",
                ActionType.DOWNLOAD_YOUTUBE: "📥",
                ActionType.DOWNLOAD_INSTAGRAM: "📥"
            }.get(action_type, "•")

            text += f"{type_emoji} {action_type.value}: {count}\n"

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        text = "❌ Ошибка при получении статистики"
    finally:
        db.close()

    await query.edit_message_text(
        text=text,
        reply_markup=get_admin_menu_keyboard()
    )


async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show recent users."""
    query = update.callback_query
    await query.answer()

    if not is_admin(update.effective_user.id):
        await query.edit_message_text("❌ Доступ запрещен")
        return

    db = SessionLocal()

    try:
        # Get last 10 users
        users = db.query(User).order_by(desc(User.created_at)).limit(10).all()

        text = "👥 Последние 10 пользователей:\n\n"

        for user in users:
            username = f"@{user.username}" if user.username else "нет username"
            sub_status = "✅" if user.is_subscribed else "❌"
            admin_status = "👑" if user.is_admin else ""

            text += (
                f"{admin_status} {sub_status} {user.first_name}\n"
                f"   {username} (ID: {user.telegram_id})\n"
                f"   Регистрация: {user.created_at.strftime('%d.%m.%Y')}\n\n"
            )

    except Exception as e:
        logger.error(f"Error getting users: {e}")
        text = "❌ Ошибка при получении списка пользователей"
    finally:
        db.close()

    await query.edit_message_text(
        text=text,
        reply_markup=get_admin_menu_keyboard()
    )


async def admin_presets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show presets."""
    query = update.callback_query
    await query.answer()

    if not is_admin(update.effective_user.id):
        await query.edit_message_text("❌ Доступ запрещен")
        return

    db = SessionLocal()

    try:
        presets = db.query(UniquificationPreset).all()

        text = "⚙️ Пресеты уникализации:\n\n"

        for preset in presets:
            default = "⭐" if preset.is_default else ""
            active = "✅" if preset.is_active else "❌"

            text += (
                f"{default} {active} {preset.name}\n"
                f"   Тип: {preset.media_type.value}\n"
                f"   Методов: {len(preset.config.get('methods', []))}\n"
                f"   Обновлен: {preset.updated_at.strftime('%d.%m.%Y')}\n\n"
            )

        text += "\n💡 Для редактирования пресетов используйте БД напрямую."

    except Exception as e:
        logger.error(f"Error getting presets: {e}")
        text = "❌ Ошибка при получении пресетов"
    finally:
        db.close()

    await query.edit_message_text(
        text=text,
        reply_markup=get_admin_menu_keyboard()
    )


async def admin_broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start broadcast."""
    query = update.callback_query
    await query.answer()

    if not is_admin(update.effective_user.id):
        await query.edit_message_text("❌ Доступ запрещен")
        return ConversationHandler.END

    text = (
        "📢 Рассылка сообщений\n\n"
        "Отправьте текст сообщения для рассылки всем пользователям.\n\n"
        "⚠️ Будьте внимательны! Отмена невозможна."
    )

    await query.edit_message_text(
        text=text,
        reply_markup=get_back_to_menu_keyboard()
    )

    return WAITING_FOR_BROADCAST_TEXT


async def admin_broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send broadcast message."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Доступ запрещен")
        return ConversationHandler.END

    message_text = update.message.text
    db = SessionLocal()

    try:
        users = db.query(User).all()
        total = len(users)
        sent = 0
        failed = 0

        progress_msg = await update.message.reply_text(
            f"📢 Начинаю рассылку {total} пользователям..."
        )

        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user.telegram_id,
                    text=message_text
                )
                sent += 1
            except Exception as e:
                logger.error(f"Failed to send to {user.telegram_id}: {e}")
                failed += 1

            # Update progress every 10 users
            if (sent + failed) % 10 == 0:
                try:
                    await progress_msg.edit_text(
                        f"📢 Рассылка: {sent + failed}/{total}\n"
                        f"✅ Отправлено: {sent}\n"
                        f"❌ Ошибок: {failed}"
                    )
                except:
                    pass

        await progress_msg.edit_text(
            f"✅ Рассылка завершена!\n\n"
            f"Всего: {total}\n"
            f"✅ Отправлено: {sent}\n"
            f"❌ Ошибок: {failed}"
        )

    except Exception as e:
        logger.error(f"Error in broadcast: {e}")
        await update.message.reply_text("❌ Ошибка при рассылке")
    finally:
        db.close()

    return ConversationHandler.END


async def admin_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show recent logs."""
    query = update.callback_query
    await query.answer()

    if not is_admin(update.effective_user.id):
        await query.edit_message_text("❌ Доступ запрещен")
        return

    db = SessionLocal()

    try:
        # Get last 10 actions
        actions = db.query(ActionLog).order_by(desc(ActionLog.created_at)).limit(10).all()

        text = "📋 Последние 10 операций:\n\n"

        for action in actions:
            status_emoji = {
                ActionStatus.PENDING: "⏳",
                ActionStatus.PROCESSING: "⚙️",
                ActionStatus.COMPLETED: "✅",
                ActionStatus.FAILED: "❌"
            }.get(action.status, "•")

            user = db.query(User).filter(User.id == action.user_id).first()
            username = f"@{user.username}" if user and user.username else f"ID:{action.user_id}"

            text += (
                f"{status_emoji} {action.action_type.value}\n"
                f"   {username}\n"
                f"   {action.created_at.strftime('%d.%m %H:%M')}\n"
            )

            if action.error_message:
                text += f"   ❌ {action.error_message[:50]}\n"

            text += "\n"

    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        text = "❌ Ошибка при получении логов"
    finally:
        db.close()

    await query.edit_message_text(
        text=text,
        reply_markup=get_admin_menu_keyboard()
    )

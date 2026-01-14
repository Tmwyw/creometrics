"""Handlers for info and support."""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from bot.keyboards import get_back_to_menu_keyboard
from bot.middlewares import subscription_required

logger = logging.getLogger(__name__)


async def info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show bot information."""
    query = update.callback_query
    await query.answer()

    if not await subscription_required(update, context):
        return

    text = (
        "ℹ️ Информация о боте\n\n"
        "🤖 CreoMetrics Bot - универсальный инструмент для работы с медиа.\n\n"
        "📋 Возможности:\n"
        "• Уникализация фото и видео\n"
        "• Конвертация форматов\n"
        "• Сжатие видео\n"
        "• Транскрибация речи\n"
        "• Скачивание видео\n\n"
        "💡 Для использования необходимо подписаться на канал @creometric\n\n"
        "✨ Версия: 1.0\n"
        "👨‍💻 Разработчик: @LazyEntrepreneur"
    )

    await query.edit_message_text(
        text=text,
        reply_markup=get_back_to_menu_keyboard()
    )


async def support_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show support information."""
    query = update.callback_query
    await query.answer()

    if not await subscription_required(update, context):
        return

    text = (
        "❗ Поддержка\n\n"
        "Если у вас возникли проблемы или вопросы:\n\n"
        "📢 Канал: @creometric\n"
        "👨‍💻 Администратор: @LazyEntrepreneur\n\n"
        "🐛 Сообщить об ошибке:\n"
        "Опишите проблему и отправьте администратору\n\n"
        "💡 Предложить улучшение:\n"
        "Мы всегда рады вашим идеям!\n\n"
        "⏱ Время ответа: обычно в течение 24 часов"
    )

    await query.edit_message_text(
        text=text,
        reply_markup=get_back_to_menu_keyboard()
    )


async def gpt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """GPT chat handler (placeholder)."""
    query = update.callback_query
    await query.answer()

    if not await subscription_required(update, context):
        return

    text = (
        "💬 Общение с GPT\n\n"
        "🚧 Эта функция находится в разработке.\n\n"
        "Скоро вы сможете общаться с ChatGPT прямо в боте!\n\n"
        "Следите за обновлениями в @creometric"
    )

    await query.edit_message_text(
        text=text,
        reply_markup=get_back_to_menu_keyboard()
    )

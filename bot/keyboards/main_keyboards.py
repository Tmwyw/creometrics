"""Main keyboard layouts for the bot."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Get main menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("📸 Уникализировать фото", callback_data="menu_unique_photo"),
            InlineKeyboardButton("🎬 Уникализировать видео", callback_data="menu_unique_video"),
        ],
        [
            InlineKeyboardButton("💿 MP3 в ГС", callback_data="menu_mp3_to_voice"),
            InlineKeyboardButton("🔵 MP4 в Кружок", callback_data="menu_video_to_circle"),
        ],
        [
            InlineKeyboardButton("🗜️ Сжать видео", callback_data="menu_compress_video"),
        ],
        [
            InlineKeyboardButton("📝 Транскрибация видео в текст", callback_data="menu_transcribe"),
        ],
        [
            InlineKeyboardButton("💬 Общение с GPT", callback_data="menu_gpt"),
        ],
        [
            InlineKeyboardButton("📥 Скачивание с YouTube / Instagram", callback_data="menu_download"),
        ],
        [
            InlineKeyboardButton("ℹ️ Информация", callback_data="menu_info"),
            InlineKeyboardButton("❗ Поддержка", callback_data="menu_support"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Get back to menu keyboard."""
    keyboard = [[InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_menu")]]
    return InlineKeyboardMarkup(keyboard)


def get_copies_count_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for selecting number of copies."""
    keyboard = []
    row = []
    for i in range(1, 11):
        row.append(InlineKeyboardButton(str(i), callback_data=f"copies_{i}"))
        if i % 5 == 0:
            keyboard.append(row)
            row = []

    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(keyboard)


def get_subscription_keyboard(channel_url: str) -> InlineKeyboardMarkup:
    """Get subscription keyboard."""
    keyboard = [
        [InlineKeyboardButton("📢 Подписаться на канал", url=channel_url)],
        [InlineKeyboardButton("✅ Я подписался", callback_data="check_subscription")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_video_quality_keyboard(formats: list) -> InlineKeyboardMarkup:
    """Get video quality selection keyboard.

    Args:
        formats: List of format dictionaries

    Returns:
        Inline keyboard with quality options
    """
    keyboard = []

    for fmt in formats:
        resolution = fmt.get('resolution', 'unknown')
        format_id = fmt['format_id']
        note = fmt.get('note', '')
        label = f"{resolution} {note}".strip()

        keyboard.append([
            InlineKeyboardButton(label, callback_data=f"quality_{format_id}")
        ])

    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(keyboard)


def get_admin_menu_keyboard() -> InlineKeyboardMarkup:
    """Get admin menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
            InlineKeyboardButton("👥 Пользователи", callback_data="admin_users"),
        ],
        [
            InlineKeyboardButton("⚙️ Пресеты уникализации", callback_data="admin_presets"),
        ],
        [
            InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast"),
        ],
        [
            InlineKeyboardButton("📋 Логи", callback_data="admin_logs"),
        ],
        [
            InlineKeyboardButton("◀️ Главное меню", callback_data="back_to_menu"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_file_format_keyboard() -> InlineKeyboardMarkup:
    """Get file format selection keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("JPEG", callback_data="format_jpeg"),
            InlineKeyboardButton("PNG", callback_data="format_png"),
            InlineKeyboardButton("WEBP", callback_data="format_webp"),
        ],
        [InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_yes_no_keyboard() -> InlineKeyboardMarkup:
    """Get yes/no keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Да", callback_data="answer_yes"),
            InlineKeyboardButton("❌ Нет", callback_data="answer_no"),
        ],
        [InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_intensity_keyboard() -> InlineKeyboardMarkup:
    """Get uniquification intensity selection keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🟢 Слабая", callback_data="intensity_low"),
        ],
        [
            InlineKeyboardButton("🟡 Средняя", callback_data="intensity_medium"),
        ],
        [
            InlineKeyboardButton("🔴 Сильная", callback_data="intensity_high"),
        ],
        [InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_overlay_position_keyboard() -> InlineKeyboardMarkup:
    """Get overlay position selection keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("↖️ Верх-лево", callback_data="position_top_left"),
            InlineKeyboardButton("↗️ Верх-право", callback_data="position_top_right"),
        ],
        [
            InlineKeyboardButton("↙️ Низ-лево", callback_data="position_bottom_left"),
            InlineKeyboardButton("↘️ Низ-право", callback_data="position_bottom_right"),
        ],
        [
            InlineKeyboardButton("🎯 Центр", callback_data="position_center"),
        ],
        [InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_send_type_keyboard() -> InlineKeyboardMarkup:
    """Get send type selection keyboard (compressed vs document)."""
    keyboard = [
        [
            InlineKeyboardButton("📸 Сжатое (обычное фото)", callback_data="sendtype_compressed"),
        ],
        [
            InlineKeyboardButton("📄 Без сжатия (документ)", callback_data="sendtype_document"),
        ],
        [InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

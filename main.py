"""Main bot application."""

import logging
import sys
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

from config.settings import settings
from database import init_db
from bot.handlers.start import start_command, menu_callback
from bot.handlers.uniquification import (
    unique_photo_start, receive_photo, process_photo_uniquification,
    unique_video_start, receive_video, process_video_uniquification,
    WAITING_FOR_PHOTO, WAITING_FOR_PHOTO_COPIES,
    WAITING_FOR_VIDEO, WAITING_FOR_VIDEO_COPIES
)
from bot.handlers.conversion import (
    mp3_to_voice_start, receive_mp3,
    video_to_circle_start, receive_video_for_circle,
    WAITING_FOR_MP3, WAITING_FOR_VIDEO_FOR_CIRCLE
)
from bot.handlers.compression import (
    compress_video_start, receive_video_to_compress,
    WAITING_FOR_VIDEO_TO_COMPRESS
)
from bot.handlers.transcription import (
    transcribe_start, receive_video_to_transcribe,
    WAITING_FOR_VIDEO_TO_TRANSCRIBE
)
from bot.handlers.download import (
    download_start, receive_url, process_download,
    WAITING_FOR_URL, WAITING_FOR_QUALITY_SELECTION
)
from bot.handlers.info import info_handler, support_handler, gpt_handler
from bot.handlers.admin import (
    admin_menu, admin_stats, admin_users, admin_presets,
    admin_broadcast_start, admin_broadcast_send, admin_logs,
    WAITING_FOR_BROADCAST_TEXT
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    handlers=[
        logging.FileHandler(settings.LOG_DIR / 'bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def error_handler(update: object, context) -> None:
    """Handle errors."""
    logger.error(f"Exception while handling an update: {context.error}")


def main():
    """Start the bot."""
    print("[MAIN] Bot main() function started")
    try:
        # Validate settings
        print("[MAIN] Validating settings...")
        settings.validate()
        print("[MAIN] Settings validated successfully")

        # Initialize database
        print("[MAIN] Initializing database...")
        logger.info("Initializing database...")
        init_db()
        print("[MAIN] Database initialized successfully")

        # Create application
        print("[MAIN] Creating bot application...")
        logger.info("Creating bot application...")
        application = Application.builder().token(settings.BOT_TOKEN).build()
        print("[MAIN] Application created successfully")

        # Add handlers
        logger.info("Adding handlers...")

        # ============== COMMAND HANDLERS ==============
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("admin", admin_menu))

        # ============== CONVERSATION HANDLERS ==============

        # Photo uniquification
        photo_unique_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(unique_photo_start, pattern="^menu_unique_photo$")],
            states={
                WAITING_FOR_PHOTO: [MessageHandler(filters.PHOTO, receive_photo)],
                WAITING_FOR_PHOTO_COPIES: [CallbackQueryHandler(process_photo_uniquification, pattern="^copies_")]
            },
            fallbacks=[CallbackQueryHandler(menu_callback, pattern="^back_to_menu$")]
        )
        application.add_handler(photo_unique_conv)

        # Video uniquification
        video_unique_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(unique_video_start, pattern="^menu_unique_video$")],
            states={
                WAITING_FOR_VIDEO: [MessageHandler(filters.VIDEO, receive_video)],
                WAITING_FOR_VIDEO_COPIES: [CallbackQueryHandler(process_video_uniquification, pattern="^copies_")]
            },
            fallbacks=[CallbackQueryHandler(menu_callback, pattern="^back_to_menu$")]
        )
        application.add_handler(video_unique_conv)

        # MP3 to voice
        mp3_voice_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(mp3_to_voice_start, pattern="^menu_mp3_to_voice$")],
            states={
                WAITING_FOR_MP3: [MessageHandler(filters.AUDIO | filters.Document.AUDIO, receive_mp3)]
            },
            fallbacks=[CallbackQueryHandler(menu_callback, pattern="^back_to_menu$")]
        )
        application.add_handler(mp3_voice_conv)

        # Video to circle
        video_circle_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(video_to_circle_start, pattern="^menu_video_to_circle$")],
            states={
                WAITING_FOR_VIDEO_FOR_CIRCLE: [MessageHandler(filters.VIDEO, receive_video_for_circle)]
            },
            fallbacks=[CallbackQueryHandler(menu_callback, pattern="^back_to_menu$")]
        )
        application.add_handler(video_circle_conv)

        # Video compression
        compress_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(compress_video_start, pattern="^menu_compress_video$")],
            states={
                WAITING_FOR_VIDEO_TO_COMPRESS: [MessageHandler(filters.VIDEO, receive_video_to_compress)]
            },
            fallbacks=[CallbackQueryHandler(menu_callback, pattern="^back_to_menu$")]
        )
        application.add_handler(compress_conv)

        # Transcription
        transcribe_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(transcribe_start, pattern="^menu_transcribe$")],
            states={
                WAITING_FOR_VIDEO_TO_TRANSCRIBE: [MessageHandler(filters.VIDEO, receive_video_to_transcribe)]
            },
            fallbacks=[CallbackQueryHandler(menu_callback, pattern="^back_to_menu$")]
        )
        application.add_handler(transcribe_conv)

        # Download
        download_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(download_start, pattern="^menu_download$")],
            states={
                WAITING_FOR_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_url)],
                WAITING_FOR_QUALITY_SELECTION: [CallbackQueryHandler(process_download, pattern="^quality_")]
            },
            fallbacks=[CallbackQueryHandler(menu_callback, pattern="^back_to_menu$")]
        )
        application.add_handler(download_conv)

        # Admin broadcast
        broadcast_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(admin_broadcast_start, pattern="^admin_broadcast$")],
            states={
                WAITING_FOR_BROADCAST_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast_send)]
            },
            fallbacks=[CallbackQueryHandler(menu_callback, pattern="^back_to_menu$")]
        )
        application.add_handler(broadcast_conv)

        # ============== CALLBACK QUERY HANDLERS ==============

        # Menu navigation
        application.add_handler(CallbackQueryHandler(menu_callback, pattern="^back_to_menu$"))

        # Info handlers
        application.add_handler(CallbackQueryHandler(info_handler, pattern="^menu_info$"))
        application.add_handler(CallbackQueryHandler(support_handler, pattern="^menu_support$"))
        application.add_handler(CallbackQueryHandler(gpt_handler, pattern="^menu_gpt$"))

        # Admin handlers
        application.add_handler(CallbackQueryHandler(admin_stats, pattern="^admin_stats$"))
        application.add_handler(CallbackQueryHandler(admin_users, pattern="^admin_users$"))
        application.add_handler(CallbackQueryHandler(admin_presets, pattern="^admin_presets$"))
        application.add_handler(CallbackQueryHandler(admin_logs, pattern="^admin_logs$"))

        # Subscription check callback
        from bot.handlers.start import start_command
        application.add_handler(CallbackQueryHandler(start_command, pattern="^check_subscription$"))

        # ============== ERROR HANDLER ==============
        application.add_error_handler(error_handler)

        # Start bot
        print("[MAIN] Starting bot polling...")
        logger.info("Starting bot...")
        logger.info(f"Bot ready! Token: {settings.BOT_TOKEN[:10]}...")
        print(f"[MAIN] Bot is now running! Token: {settings.BOT_TOKEN[:10]}...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        print(f"[MAIN] ERROR: Failed to start bot: {e}")
        logger.error(f"Failed to start bot: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == '__main__':
    print("[MAIN] Starting CreoMetrics Bot...")
    main()

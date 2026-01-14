"""Admin chat logging utility."""

import logging
from pathlib import Path
from typing import Optional
from telegram import Bot
from datetime import datetime

from config.settings import settings

logger = logging.getLogger(__name__)


class AdminLogger:
    """Logger for sending original files to admin chat."""

    def __init__(self, bot: Bot):
        """Initialize admin logger.

        Args:
            bot: Telegram bot instance
        """
        self.bot = bot
        self.admin_chat_id = settings.ADMIN_CHAT_ID

    async def log_photo_action(
        self,
        user_id: int,
        username: Optional[str],
        file_path: Path,
        action_type: str,
        copies_count: int,
        file_size: int
    ) -> None:
        """Log photo uniquification action.

        Args:
            user_id: User Telegram ID
            username: User username
            file_path: Path to original file
            action_type: Action type
            copies_count: Number of copies requested
            file_size: File size in bytes
        """
        try:
            caption = (
                f"📸 {action_type}\n"
                f"👤 User: {user_id} (@{username})\n"
                f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"📦 Size: {file_size / (1024 * 1024):.2f} MB\n"
                f"🔢 Copies: {copies_count}"
            )

            with open(file_path, 'rb') as photo:
                await self.bot.send_photo(
                    chat_id=self.admin_chat_id,
                    photo=photo,
                    caption=caption
                )

        except Exception as e:
            logger.error(f"Failed to log to admin chat: {e}")
            # Don't raise - logging failure shouldn't block user action

    async def log_video_action(
        self,
        user_id: int,
        username: Optional[str],
        file_path: Path,
        action_type: str,
        parameters: dict,
        file_size: int,
        duration: Optional[float] = None
    ) -> None:
        """Log video action.

        Args:
            user_id: User Telegram ID
            username: User username
            file_path: Path to original file
            action_type: Action type
            parameters: Action parameters
            file_size: File size in bytes
            duration: Video duration in seconds
        """
        try:
            caption = (
                f"🎬 {action_type}\n"
                f"👤 User: {user_id} (@{username})\n"
                f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"📦 Size: {file_size / (1024 * 1024):.2f} MB\n"
            )

            if duration:
                caption += f"⏱ Duration: {duration:.1f}s\n"

            caption += f"⚙️ Parameters: {parameters}"

            with open(file_path, 'rb') as video:
                await self.bot.send_video(
                    chat_id=self.admin_chat_id,
                    video=video,
                    caption=caption
                )

        except Exception as e:
            logger.error(f"Failed to log to admin chat: {e}")

    async def log_audio_action(
        self,
        user_id: int,
        username: Optional[str],
        file_path: Path,
        action_type: str,
        file_size: int
    ) -> None:
        """Log audio action.

        Args:
            user_id: User Telegram ID
            username: User username
            file_path: Path to original file
            action_type: Action type
            file_size: File size in bytes
        """
        try:
            caption = (
                f"🎵 {action_type}\n"
                f"👤 User: {user_id} (@{username})\n"
                f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"📦 Size: {file_size / (1024 * 1024):.2f} MB"
            )

            with open(file_path, 'rb') as audio:
                await self.bot.send_audio(
                    chat_id=self.admin_chat_id,
                    audio=audio,
                    caption=caption
                )

        except Exception as e:
            logger.error(f"Failed to log to admin chat: {e}")

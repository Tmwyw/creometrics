"""Task polling and result management."""

import logging
import asyncio
from pathlib import Path
from typing import Optional, List
from celery.result import AsyncResult
from telegram import Bot
from telegram.error import TelegramError

from config.settings import settings
from utils.file_helpers import cleanup_files
from workers.celery_app import celery_app
from bot.keyboards import get_back_to_menu_keyboard

logger = logging.getLogger(__name__)


class TaskManager:
    """Manage Celery task polling and result delivery."""

    def __init__(self, bot: Bot):
        """Initialize task manager.

        Args:
            bot: Telegram bot instance
        """
        self.bot = bot

    async def poll_and_send_results(
        self,
        task_id: str,
        chat_id: int,
        message_id: int,
        action_type: str,
        progress_message: str = "⏳ Обработка...",
        send_as_document: bool = False
    ) -> None:
        """Poll task status and send results when ready.

        Args:
            task_id: Celery task ID
            chat_id: User chat ID
            message_id: Message ID to update
            action_type: Type of action (for result handling)
            progress_message: Message to show during processing
        """
        task = AsyncResult(task_id, app=celery_app)

        try:
            # Poll task status
            while not task.ready():
                await asyncio.sleep(5)  # Check every 5 seconds

                # Update progress message
                try:
                    await self.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=f"{progress_message}\n\n⏱ Обработка займет еще немного времени..."
                    )
                except TelegramError:
                    pass  # Message might not have changed

            # Task is ready
            if task.successful():
                result = task.result
                await self._send_results(chat_id, message_id, action_type, result, send_as_document)
            else:
                error_msg = str(task.info) if task.info else "Неизвестная ошибка"
                await self.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=f"❌ Ошибка при обработке:\n{error_msg}\n\nПопробуйте еще раз позже."
                )

        except Exception as e:
            logger.error(f"Error polling task {task_id}: {e}")
            await self.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="❌ Произошла ошибка при обработке. Попробуйте позже."
            )

    async def _send_results(
        self,
        chat_id: int,
        message_id: int,
        action_type: str,
        result: dict,
        send_as_document: bool = False
    ) -> None:
        """Send results to user based on action type.

        Args:
            chat_id: User chat ID
            message_id: Message ID to update
            action_type: Type of action
            result: Task result dictionary
        """
        try:
            if action_type == "unique_photo":
                await self._send_uniquified_photos(chat_id, message_id, result, send_as_document)
            elif action_type == "unique_video":
                await self._send_uniquified_videos(chat_id, message_id, result)
            elif action_type == "mp3_to_voice":
                await self._send_voice(chat_id, message_id, result)
            elif action_type == "video_to_circle":
                await self._send_video_note(chat_id, message_id, result)
            elif action_type == "compress_video":
                await self._send_compressed_video(chat_id, message_id, result)
            elif action_type == "transcribe":
                await self._send_transcription(chat_id, message_id, result)
            elif action_type == "download":
                await self._send_downloaded_video(chat_id, message_id, result)
            else:
                logger.error(f"Unknown action type: {action_type}")

        except Exception as e:
            logger.error(f"Error sending results: {e}")
            await self.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="❌ Ошибка при отправке результатов."
            )

    async def _send_uniquified_photos(self, chat_id: int, message_id: int, result: dict, send_as_document: bool = False) -> None:
        """Send uniquified photos."""
        output_paths = [Path(p) for p in result.get('output_paths', [])]
        intensity = result.get('intensity', 'medium')

        if not output_paths:
            await self.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="❌ Не удалось создать уникальные копии."
            )
            return

        # Map intensity to Russian
        intensity_map = {
            'low': '🟢 слабая',
            'medium': '🟡 средняя',
            'high': '🔴 сильная'
        }
        intensity_text = intensity_map.get(intensity, '🟡 средняя')

        # Update message
        send_type_text = "документом" if send_as_document else "обычным фото"
        await self.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"✅ Готово! Отправляю {len(output_paths)} уникальных копий {send_type_text}..."
        )

        # Send all photos
        for i, photo_path in enumerate(output_paths, 1):
            try:
                with open(photo_path, 'rb') as photo:
                    if send_as_document:
                        # Send as document (no compression)
                        await self.bot.send_document(
                            chat_id=chat_id,
                            document=photo,
                            caption=f"📸 Копия {i}/{len(output_paths)} - {intensity_text}"
                        )
                    else:
                        # Send as photo (compressed)
                        await self.bot.send_photo(
                            chat_id=chat_id,
                            photo=photo,
                            caption=f"📸 Копия {i}/{len(output_paths)} - {intensity_text}"
                        )
            except Exception as e:
                logger.error(f"Error sending photo {photo_path}: {e}")

        # Cleanup
        cleanup_files(output_paths)
        cleanup_files([photo_path.parent])

        # Final message
        await self.bot.send_message(
            chat_id=chat_id,
            text=f"✅ Все {len(output_paths)} копий отправлены!",
            reply_markup=get_back_to_menu_keyboard()
        )

    async def _send_uniquified_videos(self, chat_id: int, message_id: int, result: dict) -> None:
        """Send uniquified videos."""
        output_paths = [Path(p) for p in result.get('output_paths', [])]

        if not output_paths:
            await self.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="❌ Не удалось создать уникальные копии."
            )
            return

        await self.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"✅ Готово! Отправляю {len(output_paths)} уникальных копий..."
        )

        for i, video_path in enumerate(output_paths, 1):
            try:
                with open(video_path, 'rb') as video:
                    await self.bot.send_video(
                        chat_id=chat_id,
                        video=video,
                        caption=f"🎬 Копия {i}/{len(output_paths)}"
                    )
            except Exception as e:
                logger.error(f"Error sending video {video_path}: {e}")

        cleanup_files(output_paths)
        cleanup_files([output_paths[0].parent])

        await self.bot.send_message(
            chat_id=chat_id,
            text=f"✅ Все {len(output_paths)} копий отправлены!",
            reply_markup=get_back_to_menu_keyboard()
        )

    async def _send_voice(self, chat_id: int, message_id: int, result: dict) -> None:
        """Send voice message."""
        output_path = Path(result.get('output_path'))

        await self.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="✅ Готово! Отправляю голосовое сообщение..."
        )

        try:
            with open(output_path, 'rb') as voice:
                await self.bot.send_voice(
                    chat_id=chat_id,
                    voice=voice
                )

            cleanup_files([output_path])

            await self.bot.send_message(
                chat_id=chat_id,
                text="✅ Голосовое сообщение готово!",
                reply_markup=get_back_to_menu_keyboard()
            )
        except Exception as e:
            logger.error(f"Error sending voice: {e}")
            await self.bot.send_message(chat_id=chat_id, text="❌ Ошибка при отправке.")

    async def _send_video_note(self, chat_id: int, message_id: int, result: dict) -> None:
        """Send video note (circle)."""
        output_path = Path(result.get('output_path'))

        await self.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="✅ Готово! Отправляю видеосообщение..."
        )

        try:
            with open(output_path, 'rb') as video:
                await self.bot.send_video_note(
                    chat_id=chat_id,
                    video_note=video
                )

            cleanup_files([output_path])

            await self.bot.send_message(
                chat_id=chat_id,
                text="✅ Видеосообщение готово!",
                reply_markup=get_back_to_menu_keyboard()
            )
        except Exception as e:
            logger.error(f"Error sending video note: {e}")
            await self.bot.send_message(chat_id=chat_id, text="❌ Ошибка при отправке.")

    async def _send_compressed_video(self, chat_id: int, message_id: int, result: dict) -> None:
        """Send compressed video."""
        output_path = Path(result.get('output_path'))

        await self.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="✅ Готово! Отправляю сжатое видео..."
        )

        try:
            with open(output_path, 'rb') as video:
                file_size = output_path.stat().st_size / (1024 * 1024)
                await self.bot.send_video(
                    chat_id=chat_id,
                    video=video,
                    caption=f"🗜️ Сжатое видео\nРазмер: {file_size:.1f} MB"
                )

            cleanup_files([output_path])

            await self.bot.send_message(
                chat_id=chat_id,
                text="✅ Видео сжато успешно!",
                reply_markup=get_back_to_menu_keyboard()
            )
        except Exception as e:
            logger.error(f"Error sending compressed video: {e}")
            await self.bot.send_message(chat_id=chat_id, text="❌ Ошибка при отправке.")

    async def _send_transcription(self, chat_id: int, message_id: int, result: dict) -> None:
        """Send transcription."""
        transcription = result.get('transcription', {})
        original = transcription.get('original', '')
        russian = transcription.get('russian', '')
        language = transcription.get('language', 'unknown')

        text = "✅ Транскрибация завершена!\n\n"

        if language != 'ru' and russian != original:
            text += f"🌍 Язык: {language}\n\n"
            text += f"📝 Оригинал:\n{original}\n\n"
            text += f"🇷🇺 Перевод на русский:\n{russian}"
        else:
            text += f"📝 Текст:\n{original}"

        await self.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text[:4096]  # Telegram limit
        )

    async def _send_downloaded_video(self, chat_id: int, message_id: int, result: dict) -> None:
        """Send downloaded video."""
        output_path = Path(result.get('output_path'))

        await self.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="✅ Готово! Отправляю видео..."
        )

        try:
            with open(output_path, 'rb') as video:
                await self.bot.send_video(
                    chat_id=chat_id,
                    video=video,
                    caption="📥 Скачанное видео"
                )

            cleanup_files([output_path])

            await self.bot.send_message(
                chat_id=chat_id,
                text="✅ Видео скачано успешно!",
                reply_markup=get_back_to_menu_keyboard()
            )
        except Exception as e:
            logger.error(f"Error sending downloaded video: {e}")
            await self.bot.send_message(chat_id=chat_id, text="❌ Ошибка при отправке.")

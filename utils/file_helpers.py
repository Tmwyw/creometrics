"""File handling utilities."""

import logging
from pathlib import Path
from typing import List
import shutil

logger = logging.getLogger(__name__)


async def download_file(bot, file_id: str, destination: Path) -> Path:
    """Download file from Telegram.

    Args:
        bot: Telegram bot instance
        file_id: Telegram file ID
        destination: Destination path

    Returns:
        Path to downloaded file
    """
    file = await bot.get_file(file_id)
    await file.download_to_drive(destination)
    return destination


def cleanup_files(file_paths: List[Path]) -> None:
    """Clean up temporary files.

    Args:
        file_paths: List of file paths to delete
    """
    for file_path in file_paths:
        try:
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                shutil.rmtree(file_path)
        except Exception as e:
            logger.error(f"Error cleaning up {file_path}: {e}")


def get_file_size_mb(file_path: Path) -> float:
    """Get file size in megabytes.

    Args:
        file_path: Path to file

    Returns:
        Size in MB
    """
    return file_path.stat().st_size / (1024 * 1024)


def format_file_size(size_bytes: int) -> str:
    """Format file size for display.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.1f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.1f} GB"

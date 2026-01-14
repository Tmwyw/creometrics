"""Video transcription utilities using Whisper.

TEMPORARILY DISABLED: Transcription is stubbed out for Railway deployment.
Will be re-enabled after successful deployment.
"""

import logging
from pathlib import Path
from typing import Dict, Optional
import subprocess

# Whisper imports temporarily disabled
whisper = None
WhisperModel = None

logger = logging.getLogger(__name__)


class VideoTranscriber:
    """Video transcription engine using Whisper."""

    def __init__(self, model_size: str = "base", use_faster_whisper: bool = False):
        """Initialize transcriber.

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            use_faster_whisper: Use faster-whisper if available (faster, less memory)
        """
        self.model_size = model_size
        self.use_faster_whisper = False
        self.model = None

        logger.warning("Transcription is temporarily disabled (stub mode)")

    def transcribe_video(
        self,
        video_path: Path,
        language: Optional[str] = None,
        translate_to_russian: bool = True
    ) -> Dict[str, str]:
        """Transcribe video and optionally translate to Russian.

        Args:
            video_path: Path to video file
            language: Source language code (None for auto-detect)
            translate_to_russian: Whether to translate to Russian

        Returns:
            Dictionary with 'original' and 'russian' transcriptions
        """
        logger.warning(f"Transcription requested for {video_path.name}, but feature is temporarily disabled")

        # STUB: Return placeholder text
        stub_text = (
            "⚠️ Функция транскрипции временно отключена.\n"
            "Transcription feature is temporarily disabled.\n\n"
            "Эта функция будет активирована после успешного деплоя на Railway."
        )

        return {
            'original': stub_text,
            'russian': stub_text,
            'language': 'stub'
        }

    # Helper methods disabled in stub mode


# Global transcriber instance
_transcriber: Optional[VideoTranscriber] = None


def get_transcriber() -> VideoTranscriber:
    """Get or create global transcriber instance."""
    global _transcriber
    if _transcriber is None:
        _transcriber = VideoTranscriber(model_size='base')
    return _transcriber


def transcribe_video(
    video_path: Path,
    language: Optional[str] = None,
    translate_to_russian: bool = True
) -> Dict[str, str]:
    """Transcribe video (convenience function).

    Args:
        video_path: Path to video file
        language: Source language code (None for auto-detect)
        translate_to_russian: Whether to translate to Russian

    Returns:
        Dictionary with transcription results
    """
    transcriber = get_transcriber()
    return transcriber.transcribe_video(video_path, language, translate_to_russian)

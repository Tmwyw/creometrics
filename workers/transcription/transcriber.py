"""Video transcription utilities using Whisper."""

import logging
from pathlib import Path
from typing import Dict, Optional
import subprocess
from deep_translator import GoogleTranslator

try:
    import whisper
except ImportError:
    whisper = None

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

logger = logging.getLogger(__name__)


class VideoTranscriber:
    """Video transcription engine using Whisper."""

    def __init__(self, model_size: str = "base", use_faster_whisper: bool = True):
        """Initialize transcriber.

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            use_faster_whisper: Use faster-whisper if available (faster, less memory)
        """
        self.model_size = model_size
        self.use_faster_whisper = use_faster_whisper and WhisperModel is not None

        # Load model
        if self.use_faster_whisper:
            logger.info(f"Loading faster-whisper model: {model_size}")
            self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        elif whisper is not None:
            logger.info(f"Loading whisper model: {model_size}")
            self.model = whisper.load_model(model_size)
        else:
            raise ImportError("Neither whisper nor faster-whisper is installed")

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
        logger.info(f"Transcribing video: {video_path.name}")

        try:
            # Extract audio from video
            audio_path = self._extract_audio(video_path)

            # Transcribe
            if self.use_faster_whisper:
                result = self._transcribe_faster_whisper(audio_path, language)
            else:
                result = self._transcribe_whisper(audio_path, language)

            transcription = result['text']
            detected_language = result.get('language', 'unknown')

            logger.info(f"Transcribed {len(transcription)} characters, language: {detected_language}")

            # Translate if needed and not already in Russian
            russian_transcription = transcription
            if translate_to_russian and detected_language != 'ru':
                logger.info("Translating to Russian...")
                russian_transcription = self._translate_to_russian(transcription, detected_language)

            # Clean up audio file
            audio_path.unlink(missing_ok=True)

            return {
                'original': transcription,
                'russian': russian_transcription,
                'language': detected_language
            }

        except Exception as e:
            logger.error(f"Error transcribing video: {e}")
            raise

    def _extract_audio(self, video_path: Path) -> Path:
        """Extract audio from video.

        Args:
            video_path: Path to video file

        Returns:
            Path to extracted audio file
        """
        audio_path = video_path.with_suffix('.wav')

        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-vn',  # No video
            '-acodec', 'pcm_s16le',  # PCM 16-bit
            '-ar', '16000',  # 16kHz sample rate
            '-ac', '1',  # Mono
            '-y',  # Overwrite
            str(audio_path)
        ]

        subprocess.run(cmd, capture_output=True, check=True)
        return audio_path

    def _transcribe_whisper(self, audio_path: Path, language: Optional[str]) -> Dict[str, str]:
        """Transcribe using original Whisper."""
        result = self.model.transcribe(
            str(audio_path),
            language=language,
            fp16=False,  # Use FP32 on CPU
            verbose=False
        )

        return {
            'text': result['text'].strip(),
            'language': result.get('language', 'unknown')
        }

    def _transcribe_faster_whisper(self, audio_path: Path, language: Optional[str]) -> Dict[str, str]:
        """Transcribe using faster-whisper."""
        segments, info = self.model.transcribe(
            str(audio_path),
            language=language,
            beam_size=5,
            vad_filter=True  # Voice activity detection
        )

        # Combine segments
        text = ' '.join([segment.text for segment in segments]).strip()

        return {
            'text': text,
            'language': info.language
        }

    def _translate_to_russian(self, text: str, source_lang: str) -> str:
        """Translate text to Russian.

        Args:
            text: Text to translate
            source_lang: Source language code

        Returns:
            Translated text
        """
        try:
            # Split text into chunks (Google Translator has size limits)
            max_chunk_size = 4000
            chunks = [text[i:i+max_chunk_size] for i in range(0, len(text), max_chunk_size)]

            translated_chunks = []
            translator = GoogleTranslator(source=source_lang, target='ru')

            for chunk in chunks:
                translated = translator.translate(chunk)
                translated_chunks.append(translated)

            return ' '.join(translated_chunks)

        except Exception as e:
            logger.error(f"Error translating to Russian: {e}")
            return text  # Return original if translation fails


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

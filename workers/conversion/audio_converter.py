"""Audio conversion utilities."""

import logging
from pathlib import Path
from pydub import AudioSegment

logger = logging.getLogger(__name__)


def convert_mp3_to_voice(input_path: Path, output_path: Path = None) -> Path:
    """Convert MP3 to OGG format for Telegram voice message.

    Args:
        input_path: Path to input MP3 file
        output_path: Path to output OGG file (optional)

    Returns:
        Path to converted OGG file
    """
    logger.info(f"Converting MP3 to voice: {input_path.name}")

    try:
        # Load MP3
        audio = AudioSegment.from_mp3(str(input_path))

        # Convert to mono if stereo (voice messages are typically mono)
        if audio.channels > 1:
            audio = audio.set_channels(1)

        # Set reasonable bitrate for voice
        audio = audio.set_frame_rate(48000)  # Telegram recommends 48kHz for voice

        # Determine output path
        if output_path is None:
            output_path = input_path.with_suffix('.ogg')

        # Export as OGG (Opus codec)
        audio.export(
            str(output_path),
            format='ogg',
            codec='libopus',
            parameters=['-b:a', '64k']  # 64kbps is good for voice
        )

        logger.info(f"Converted to voice: {output_path.name}")
        return output_path

    except Exception as e:
        logger.error(f"Error converting MP3 to voice: {e}")
        raise

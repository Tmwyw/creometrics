"""Video compression utilities."""

import logging
from pathlib import Path
import subprocess
import os

logger = logging.getLogger(__name__)


def compress_video(
    input_path: Path,
    output_path: Path = None,
    target_size_mb: int = 20,
    max_duration: int = 180
) -> Path:
    """Compress video to target file size.

    Args:
        input_path: Path to input video file
        output_path: Path to output video file (optional)
        target_size_mb: Target file size in MB
        max_duration: Maximum expected duration in seconds (for bitrate calculation)

    Returns:
        Path to compressed video file
    """
    logger.info(f"Compressing video: {input_path.name}, target: {target_size_mb}MB")

    try:
        # Determine output path
        if output_path is None:
            output_path = input_path.with_name(f"{input_path.stem}_compressed.mp4")

        # Get video info using ffprobe
        duration = _get_video_duration(input_path)

        if duration > max_duration:
            duration = max_duration

        # Calculate target bitrate
        # Formula: bitrate = (target_size * 8192) / duration - audio_bitrate
        target_size_kb = target_size_mb * 1024
        audio_bitrate_kb = 128  # Reserve 128kb/s for audio
        video_bitrate_kb = int((target_size_kb * 8192) / duration - audio_bitrate_kb)

        # Ensure bitrate is reasonable
        video_bitrate_kb = max(100, min(video_bitrate_kb, 5000))  # Between 100 and 5000 kb/s

        logger.info(f"Duration: {duration}s, Target bitrate: {video_bitrate_kb}kb/s")

        # Build ffmpeg command
        cmd = [
            'ffmpeg',
            '-i', str(input_path),
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-b:v', f'{video_bitrate_kb}k',
            '-maxrate', f'{video_bitrate_kb * 1.5}k',
            '-bufsize', f'{video_bitrate_kb * 2}k',
            '-c:a', 'aac',
            '-b:a', f'{audio_bitrate_kb}k',
            '-movflags', '+faststart',
            '-y',  # Overwrite output file
            str(output_path)
        ]

        # Run ffmpeg
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        # Check output file size
        output_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        logger.info(f"Compressed video size: {output_size_mb:.2f}MB")

        if output_size_mb > target_size_mb * 1.1:  # Allow 10% tolerance
            logger.warning(f"Output size ({output_size_mb:.2f}MB) exceeds target ({target_size_mb}MB)")

        return output_path

    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr}")
        raise
    except Exception as e:
        logger.error(f"Error compressing video: {e}")
        raise


def _get_video_duration(video_path: Path) -> float:
    """Get video duration in seconds.

    Args:
        video_path: Path to video file

    Returns:
        Duration in seconds
    """
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(video_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())

"""Video conversion utilities."""

import logging
from pathlib import Path
from moviepy.editor import VideoFileClip
import cv2

logger = logging.getLogger(__name__)


def convert_video_to_circle(
    input_path: Path,
    output_path: Path = None,
    max_duration: int = 60
) -> Path:
    """Convert video to circular video message (video note) format.

    Args:
        input_path: Path to input video file
        output_path: Path to output video file (optional)
        max_duration: Maximum duration in seconds (default 60)

    Returns:
        Path to converted video file
    """
    logger.info(f"Converting video to circle: {input_path.name}")

    try:
        # Load video
        clip = VideoFileClip(str(input_path))

        # Trim to max duration if needed
        if clip.duration > max_duration:
            logger.info(f"Trimming video from {clip.duration}s to {max_duration}s")
            clip = clip.subclip(0, max_duration)

        # Get dimensions
        width, height = clip.size
        min_dim = min(width, height)

        # Crop to square (center crop)
        x_center = width / 2
        y_center = height / 2
        x1 = int(x_center - min_dim / 2)
        y1 = int(y_center - min_dim / 2)
        x2 = int(x_center + min_dim / 2)
        y2 = int(y_center + min_dim / 2)

        clip = clip.crop(x1=x1, y1=y1, x2=x2, y2=y2)

        # Resize to 384x384 or 512x512 (Telegram video note sizes)
        target_size = 512 if min_dim > 512 else 384
        clip = clip.resize((target_size, target_size))

        # Determine output path
        if output_path is None:
            output_path = input_path.with_name(f"{input_path.stem}_circle.mp4")

        # Export with settings for video note
        clip.write_videofile(
            str(output_path),
            codec='libx264',
            audio_codec='aac',
            preset='medium',
            bitrate='500k',
            fps=30,
            temp_audiofile=str(output_path.parent / f'temp_audio_{output_path.stem}.m4a'),
            remove_temp=True,
            logger=None
        )

        clip.close()

        logger.info(f"Converted to circle: {output_path.name}")
        return output_path

    except Exception as e:
        logger.error(f"Error converting video to circle: {e}")
        raise

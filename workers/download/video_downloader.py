"""Video download utilities using yt-dlp."""

import logging
from pathlib import Path
from typing import Optional, List, Dict
import yt_dlp

logger = logging.getLogger(__name__)


class VideoDownloader:
    """Video downloader for YouTube and Instagram."""

    def __init__(self, output_dir: Path):
        """Initialize downloader.

        Args:
            output_dir: Directory to save downloaded videos
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_available_formats(self, url: str) -> List[Dict[str, str]]:
        """Get available video formats.

        Args:
            url: Video URL

        Returns:
            List of format dictionaries with 'format_id', 'resolution', 'ext'
        """
        logger.info(f"Getting formats for: {url}")

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                formats = []
                for fmt in info.get('formats', []):
                    # Only include formats with video
                    if fmt.get('vcodec') != 'none':
                        resolution = fmt.get('resolution', 'unknown')
                        height = fmt.get('height', 0)

                        # Skip very low quality
                        if height < 144:
                            continue

                        formats.append({
                            'format_id': fmt['format_id'],
                            'resolution': resolution,
                            'height': height,
                            'ext': fmt.get('ext', 'mp4'),
                            'filesize': fmt.get('filesize', 0),
                            'note': fmt.get('format_note', '')
                        })

                # Sort by height (quality)
                formats.sort(key=lambda x: x['height'], reverse=True)

                # Return unique resolutions
                seen_heights = set()
                unique_formats = []
                for fmt in formats:
                    if fmt['height'] not in seen_heights:
                        seen_heights.add(fmt['height'])
                        unique_formats.append(fmt)

                return unique_formats

        except Exception as e:
            logger.error(f"Error getting formats: {e}")
            raise

    def download(
        self,
        url: str,
        format_id: Optional[str] = None,
        filename: Optional[str] = None
    ) -> Path:
        """Download video.

        Args:
            url: Video URL
            format_id: Specific format ID to download (None for best)
            filename: Custom filename (None for auto)

        Returns:
            Path to downloaded video
        """
        logger.info(f"Downloading video: {url}, format: {format_id or 'best'}")

        # Prepare output template
        if filename:
            output_template = str(self.output_dir / filename)
        else:
            output_template = str(self.output_dir / '%(title)s_%(id)s.%(ext)s')

        # Prepare yt-dlp options
        ydl_opts = {
            'format': format_id if format_id else 'best',
            'outtmpl': output_template,
            'quiet': False,
            'no_warnings': False,
            'merge_output_format': 'mp4',  # Merge to MP4 if needed
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                downloaded_file = ydl.prepare_filename(info)

                # Handle merged files
                if not Path(downloaded_file).exists():
                    # Check if .mp4 exists (after merging)
                    mp4_file = Path(downloaded_file).with_suffix('.mp4')
                    if mp4_file.exists():
                        downloaded_file = str(mp4_file)

                logger.info(f"Downloaded: {downloaded_file}")
                return Path(downloaded_file)

        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            raise

    def is_supported_url(self, url: str) -> bool:
        """Check if URL is supported.

        Args:
            url: URL to check

        Returns:
            True if supported
        """
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                ydl.extract_info(url, download=False)
                return True
        except:
            return False


def download_video(
    url: str,
    output_dir: Path,
    format_id: Optional[str] = None,
    filename: Optional[str] = None
) -> Path:
    """Download video (convenience function).

    Args:
        url: Video URL
        output_dir: Directory to save video
        format_id: Specific format ID to download (None for best)
        filename: Custom filename (None for auto)

    Returns:
        Path to downloaded video
    """
    downloader = VideoDownloader(output_dir)
    return downloader.download(url, format_id, filename)

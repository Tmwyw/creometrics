"""Video uniquification worker."""

import random
from pathlib import Path
from typing import List, Dict, Any
import logging
import cv2
import numpy as np
from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip
from PIL import Image

from .methods import add_noise, add_sparkles, add_lens_flare

logger = logging.getLogger(__name__)


class VideoUniquifier:
    """Video uniquification engine."""

    def __init__(self, preset_config: Dict[str, Any]):
        """Initialize video uniquifier.

        Args:
            preset_config: Preset configuration with methods and parameters
        """
        self.preset_config = preset_config
        self.methods = preset_config.get('methods', [])

    def uniquify(self, input_path: Path, output_dir: Path, count: int = 1) -> List[Path]:
        """Generate uniquified copies of a video.

        Args:
            input_path: Path to input video
            output_dir: Directory to save output videos
            count: Number of copies to generate

        Returns:
            List of paths to generated videos
        """
        logger.info(f"Uniquifying video: {input_path.name}, count: {count}")

        output_paths = []
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique copies
        for i in range(count):
            try:
                output_path = output_dir / f"{input_path.stem}_unique_{i+1}{input_path.suffix}"

                # Prepare transformation parameters for this copy
                transform_params = self._prepare_transform_params()

                # Apply transformations
                self._process_video(input_path, output_path, transform_params)

                output_paths.append(output_path)
                logger.info(f"Generated unique copy {i+1}/{count}: {output_path.name}")

            except Exception as e:
                logger.error(f"Error generating copy {i+1}: {e}")
                # Continue with next copy

        return output_paths

    def _prepare_transform_params(self) -> Dict[str, Any]:
        """Prepare transformation parameters based on preset.

        Returns:
            Dictionary of transformation parameters
        """
        params = {}

        for method_config in self.methods:
            if not method_config.get('enabled', False):
                continue

            method_name = method_config.get('name')
            method_params = {}

            for key, value in method_config.items():
                if key in ['name', 'enabled']:
                    continue

                # If value is a list with 2 elements, treat as range
                if isinstance(value, list) and len(value) == 2:
                    if all(isinstance(v, int) for v in value):
                        method_params[key] = random.randint(value[0], value[1])
                    else:
                        method_params[key] = random.uniform(float(value[0]), float(value[1]))
                else:
                    method_params[key] = value

            params[method_name] = method_params

        return params

    def _process_video(self, input_path: Path, output_path: Path, transform_params: Dict[str, Any]) -> None:
        """Process video with transformations.

        Args:
            input_path: Input video path
            output_path: Output video path
            transform_params: Transformation parameters
        """
        # Load video
        clip = VideoFileClip(str(input_path))

        # Apply video-level transformations
        if 'speed' in transform_params:
            speed_factor = transform_params['speed']['factor']
            clip = clip.speedx(speed_factor)

        if 'brightness' in transform_params:
            brightness_factor = transform_params['brightness']['factor']
            clip = clip.fl_image(lambda img: self._adjust_brightness(img, brightness_factor))

        if 'contrast' in transform_params:
            contrast_factor = transform_params['contrast']['factor']
            clip = clip.fl_image(lambda img: self._adjust_contrast(img, contrast_factor))

        if 'saturation' in transform_params:
            saturation_factor = transform_params['saturation']['factor']
            clip = clip.fl_image(lambda img: self._adjust_saturation(img, saturation_factor))

        if 'hue' in transform_params:
            hue_shift = transform_params['hue']['shift']
            clip = clip.fl_image(lambda img: self._adjust_hue(img, hue_shift))

        # Apply frame-level effects (noise, sparkles, etc.)
        if any(key in transform_params for key in ['noise', 'sparkles', 'lens_flare']):
            clip = clip.fl_image(lambda img: self._apply_frame_effects(img, transform_params))

        # Write output
        clip.write_videofile(
            str(output_path),
            codec='libx264',
            audio_codec='aac',
            temp_audiofile=str(output_path.parent / f'temp_audio_{output_path.stem}.m4a'),
            remove_temp=True,
            logger=None  # Suppress moviepy logger
        )

        clip.close()

    def _adjust_brightness(self, frame: np.ndarray, factor: float) -> np.ndarray:
        """Adjust frame brightness."""
        return np.clip(frame * factor, 0, 255).astype(np.uint8)

    def _adjust_contrast(self, frame: np.ndarray, factor: float) -> np.ndarray:
        """Adjust frame contrast."""
        mean = np.mean(frame)
        return np.clip((frame - mean) * factor + mean, 0, 255).astype(np.uint8)

    def _adjust_saturation(self, frame: np.ndarray, factor: float) -> np.ndarray:
        """Adjust frame saturation."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * factor, 0, 255)
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

    def _adjust_hue(self, frame: np.ndarray, shift: int) -> np.ndarray:
        """Adjust frame hue."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
        hsv[:, :, 0] = (hsv[:, :, 0].astype(np.int16) + shift) % 180
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

    def _apply_frame_effects(self, frame: np.ndarray, transform_params: Dict[str, Any]) -> np.ndarray:
        """Apply frame-level effects like noise, sparkles, etc."""
        # Convert to PIL Image
        img = Image.fromarray(frame)

        # Apply noise
        if 'noise' in transform_params:
            intensity = (transform_params['noise']['intensity'], transform_params['noise']['intensity'] + 1)
            img = add_noise(img, intensity)

        # Apply sparkles (less frequently for performance)
        if 'sparkles' in transform_params and random.random() < 0.3:  # Apply to 30% of frames
            params = transform_params['sparkles']
            img = add_sparkles(
                img,
                count=(params.get('count', 5), params.get('count', 5) + 5),
                size=(params.get('size', 2), params.get('size', 2) + 1)
            )

        # Apply lens flare (even less frequently)
        if 'lens_flare' in transform_params and random.random() < 0.1:  # Apply to 10% of frames
            intensity = (transform_params['lens_flare']['intensity'],
                        transform_params['lens_flare']['intensity'] + 0.1)
            img = add_lens_flare(img, intensity)

        # Convert back to numpy array
        return np.array(img)


def create_default_video_preset() -> Dict[str, Any]:
    """Create default video uniquification preset.

    Returns:
        Default preset configuration
    """
    return {
        "methods": [
            {
                "name": "speed",
                "enabled": True,
                "factor": [0.98, 1.02]  # Slight speed variation
            },
            {
                "name": "brightness",
                "enabled": True,
                "factor": [0.95, 1.05]
            },
            {
                "name": "contrast",
                "enabled": True,
                "factor": [0.95, 1.05]
            },
            {
                "name": "saturation",
                "enabled": True,
                "factor": [0.95, 1.05]
            },
            {
                "name": "hue",
                "enabled": True,
                "shift": [-3, 3]
            },
            {
                "name": "noise",
                "enabled": True,
                "intensity": [3, 8]
            },
            {
                "name": "sparkles",
                "enabled": False,  # Disabled by default for performance
                "count": [3, 10],
                "size": [1, 3]
            },
            {
                "name": "lens_flare",
                "enabled": False,  # Disabled by default for performance
                "intensity": [0.2, 0.5]
            }
        ]
    }

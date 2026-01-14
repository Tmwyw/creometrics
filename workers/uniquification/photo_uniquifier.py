"""Photo uniquification worker."""

import random
from pathlib import Path
from typing import List, Dict, Any
from PIL import Image
import logging

from .methods import METHOD_REGISTRY

logger = logging.getLogger(__name__)


class PhotoUniquifier:
    """Photo uniquification engine."""

    def __init__(self, preset_config: Dict[str, Any]):
        """Initialize photo uniquifier.

        Args:
            preset_config: Preset configuration with methods and parameters
        """
        self.preset_config = preset_config
        self.methods = preset_config.get('methods', [])

    def uniquify(self, input_path: Path, output_dir: Path, count: int = 1) -> List[Path]:
        """Generate uniquified copies of a photo.

        Args:
            input_path: Path to input image
            output_dir: Directory to save output images
            count: Number of copies to generate

        Returns:
            List of paths to generated images
        """
        logger.info(f"Uniquifying photo: {input_path.name}, count: {count}")

        # Load original image
        try:
            original_image = Image.open(input_path)
            original_image = original_image.convert('RGB')  # Ensure RGB mode
        except Exception as e:
            logger.error(f"Failed to load image: {e}")
            raise

        output_paths = []
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique copies
        for i in range(count):
            try:
                # Start with copy of original
                image = original_image.copy()

                # Apply enabled methods with random parameters
                for method_config in self.methods:
                    if not method_config.get('enabled', False):
                        continue

                    method_name = method_config.get('name')
                    if method_name not in METHOD_REGISTRY:
                        logger.warning(f"Unknown method: {method_name}")
                        continue

                    method_func = METHOD_REGISTRY[method_name]

                    # Prepare parameters by randomly selecting from ranges
                    params = self._prepare_parameters(method_config)

                    # Apply method
                    try:
                        image = method_func(image, **params)
                    except Exception as e:
                        logger.error(f"Error applying method {method_name}: {e}")
                        # Continue with other methods

                # Save result
                output_path = output_dir / f"{input_path.stem}_unique_{i+1}{input_path.suffix}"
                image.save(output_path, quality=95)
                output_paths.append(output_path)

                logger.info(f"Generated unique copy {i+1}/{count}: {output_path.name}")

            except Exception as e:
                logger.error(f"Error generating copy {i+1}: {e}")
                # Continue with next copy

        return output_paths

    def _prepare_parameters(self, method_config: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare parameters for a method by selecting random values from ranges.

        Args:
            method_config: Method configuration

        Returns:
            Dictionary of parameters
        """
        params = {}

        for key, value in method_config.items():
            if key in ['name', 'enabled']:
                continue

            # If value is a list with 2 elements, treat as range
            if isinstance(value, list) and len(value) == 2:
                # Determine if range is for int or float
                if all(isinstance(v, int) for v in value):
                    params[key] = random.randint(value[0], value[1])
                else:
                    params[key] = random.uniform(float(value[0]), float(value[1]))
            else:
                # Use value as-is
                params[key] = value

        return params


def create_default_photo_preset() -> Dict[str, Any]:
    """Create default photo uniquification preset.

    Returns:
        Default preset configuration
    """
    return {
        "methods": [
            {
                "name": "noise",
                "enabled": True,
                "intensity": [5, 15]
            },
            {
                "name": "sparkles",
                "enabled": True,
                "count": [10, 30],
                "size": [2, 5]
            },
            {
                "name": "lens_flare",
                "enabled": True,
                "intensity": [0.3, 0.7]
            },
            {
                "name": "rotate",
                "enabled": True,
                "angle": [-3, 3]
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
                "name": "hue",
                "enabled": True,
                "shift": [-5, 5]
            },
            {
                "name": "blur",
                "enabled": False,
                "radius": [0.5, 1.5]
            }
        ]
    }

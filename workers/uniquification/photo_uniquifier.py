"""Photo uniquification worker."""

import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont, ImageOps
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
        self.intensity = preset_config.get('intensity', 'low')
        logger.info(f"[INIT] Intensity: {self.intensity}")
        logger.info(f"[INIT] Raw methods from config: {preset_config.get('methods', [])}")
        self.methods = self._apply_intensity_multiplier(preset_config.get('methods', []))
        logger.info(f"[INIT] Methods after intensity multiplier: {self.methods}")
        self.file_format = preset_config.get('file_format', 'jpeg')
        self.flip_horizontal = preset_config.get('flip_horizontal', False)
        self.overlay_text = preset_config.get('overlay_text')
        self.overlay_photo_path = preset_config.get('overlay_photo_path')
        self.overlay_position = preset_config.get('overlay_position', 'center')
        self.overlay_opacity = preset_config.get('overlay_opacity', 100)

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
                # Set seed based on copy number for reproducibility
                # Each copy gets different randomization, but same copy number = same result
                random.seed(i + hash(input_path.name))

                # Start with copy of original
                image = original_image.copy()

                logger.info(f"[UNIQUIFY] Copy {i+1}/{count}: Starting with {len(self.methods)} methods")

                # Apply flip if needed
                if self.flip_horizontal:
                    image = ImageOps.mirror(image)
                    logger.info(f"[UNIQUIFY] Applied horizontal flip")

                # Apply enabled methods with random parameters
                for method_config in self.methods:
                    if not method_config.get('enabled', False):
                        logger.info(f"[UNIQUIFY] Skipping disabled method: {method_config.get('name')}")
                        continue

                    method_name = method_config.get('name')
                    if method_name not in METHOD_REGISTRY:
                        logger.warning(f"[UNIQUIFY] Unknown method: {method_name}")
                        continue

                    method_func = METHOD_REGISTRY[method_name]

                    # Prepare parameters by randomly selecting from ranges
                    params = self._prepare_parameters(method_config)
                    logger.info(f"[UNIQUIFY] Applying {method_name} with params: {params}")

                    # Apply method
                    try:
                        image = method_func(image, **params)
                        logger.info(f"[UNIQUIFY] Successfully applied {method_name}")
                    except Exception as e:
                        logger.error(f"[UNIQUIFY] Error applying method {method_name}: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                        # Continue with other methods

                # Apply text overlay if needed
                if self.overlay_text:
                    image = self._apply_text_overlay(image, self.overlay_text)

                # Apply photo overlay if needed
                if self.overlay_photo_path:
                    image = self._apply_photo_overlay(
                        image,
                        self.overlay_photo_path,
                        self.overlay_position,
                        self.overlay_opacity
                    )

                # Determine file extension based on format
                ext_map = {'jpeg': '.jpg', 'png': '.png', 'webp': '.webp'}
                ext = ext_map.get(self.file_format, '.jpg')

                # Save result
                output_path = output_dir / f"{input_path.stem}_unique_{i+1}{ext}"

                # Save with appropriate format WITHOUT metadata
                if self.file_format == 'jpeg':
                    image.save(output_path, 'JPEG', quality=95, exif=b'')
                elif self.file_format == 'png':
                    image.save(output_path, 'PNG', exif=b'')
                elif self.file_format == 'webp':
                    image.save(output_path, 'WEBP', quality=95, exif=b'')

                output_paths.append(output_path)

                logger.info(f"Generated unique copy {i+1}/{count}: {output_path.name}")

            except Exception as e:
                logger.error(f"Error generating copy {i+1}: {e}")
                # Continue with next copy

        return output_paths

    def _prepare_parameters(self, method_config: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare parameters for a method - select random value from range once.

        This ensures consistent intensity behavior: each copy uses the same
        randomized parameters, making intensity differences visible.

        Args:
            method_config: Method configuration

        Returns:
            Dictionary of parameters with ranges converted to single values
        """
        params = {}

        for key, value in method_config.items():
            if key in ['name', 'enabled']:
                continue

            # If value is a list with 2 elements, randomly select within range
            if isinstance(value, list) and len(value) == 2:
                if all(isinstance(v, int) for v in value):
                    params[key] = random.randint(value[0], value[1])
                else:
                    params[key] = random.uniform(float(value[0]), float(value[1]))
            else:
                # Use value as-is
                params[key] = value

        return params

    def _apply_intensity_multiplier(self, methods: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply intensity multiplier to method parameters.

        Args:
            methods: List of method configurations

        Returns:
            Modified list of method configurations
        """
        # Intensity multipliers - subtle to moderate changes
        multipliers = {
            'low': 0.5,      # Half of base values for very subtle changes
            'medium': 1.0,   # Use base values as-is
            'high': 1.3      # 30% increase for noticeable but not destructive changes
        }

        multiplier = multipliers.get(self.intensity, 1.5)

        # Methods that should NOT be scaled (always use base values)
        no_scale_methods = {'brightness', 'contrast', 'hue', 'blur'}

        modified_methods = []
        for method in methods:
            method_copy = method.copy()
            method_name = method.get('name')

            # Skip scaling for certain methods
            if method_name in no_scale_methods:
                modified_methods.append(method_copy)
                continue

            # Apply multiplier to numeric parameters
            for key, value in method_copy.items():
                if key in ['name', 'enabled']:
                    continue

                if isinstance(value, list) and len(value) == 2:
                    # Apply multiplier to range values
                    method_copy[key] = [
                        type(value[0])(value[0] * multiplier),
                        type(value[1])(value[1] * multiplier)
                    ]
                elif isinstance(value, (int, float)):
                    method_copy[key] = type(value)(value * multiplier)

            modified_methods.append(method_copy)

        return modified_methods

    def _apply_text_overlay(self, image: Image.Image, text: str) -> Image.Image:
        """Apply text overlay to image.

        Args:
            image: Input image
            text: Text to overlay

        Returns:
            Image with text overlay
        """
        try:
            # Create RGBA image for transparency support
            if image.mode != 'RGBA':
                image = image.convert('RGBA')

            # Create overlay layer
            overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)

            # Use default font (try to load a better one if available)
            try:
                # Try to load a TrueType font - bigger size for better visibility
                font_size = max(30, int(image.height * 0.08))
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                # Fallback to default font
                font = ImageFont.load_default()

            # Get text size
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # Position text at bottom center with some padding
            x = (image.width - text_width) // 2
            y = image.height - text_height - 40

            # Draw semi-transparent black background for text
            padding = 20
            draw.rectangle(
                [x - padding, y - padding, x + text_width + padding, y + text_height + padding],
                fill=(0, 0, 0, 180)
            )

            # Draw text with thick shadow for better visibility
            shadow_offset = 3
            # Multiple shadow layers for stronger effect
            for offset in range(1, shadow_offset + 1):
                draw.text((x + offset, y + offset), text, font=font, fill=(0, 0, 0, 255))

            # Draw main text in white
            draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))

            # Composite overlay onto image
            image = Image.alpha_composite(image, overlay)

            # Convert back to RGB
            image = image.convert('RGB')

            return image
        except Exception as e:
            logger.error(f"Error applying text overlay: {e}")
            return image

    def _apply_photo_overlay(
        self,
        base_image: Image.Image,
        overlay_path: str,
        position: str,
        opacity: int
    ) -> Image.Image:
        """Apply photo overlay to image.

        Args:
            base_image: Base image
            overlay_path: Path to overlay image
            position: Position (top_left, top_right, bottom_left, bottom_right, center)
            opacity: Opacity (0-100)

        Returns:
            Image with photo overlay
        """
        try:
            # Load overlay image
            overlay = Image.open(overlay_path)
            overlay = overlay.convert('RGBA')

            # Resize overlay to 30% of base image size
            overlay_width = int(base_image.width * 0.3)
            overlay_height = int(overlay.height * (overlay_width / overlay.width))
            overlay = overlay.resize((overlay_width, overlay_height), Image.Resampling.LANCZOS)

            # Adjust opacity
            alpha = overlay.split()[3]
            alpha = alpha.point(lambda p: int(p * (opacity / 100)))
            overlay.putalpha(alpha)

            # Calculate position
            if position == 'top_left':
                x, y = 20, 20
            elif position == 'top_right':
                x, y = base_image.width - overlay_width - 20, 20
            elif position == 'bottom_left':
                x, y = 20, base_image.height - overlay_height - 20
            elif position == 'bottom_right':
                x, y = base_image.width - overlay_width - 20, base_image.height - overlay_height - 20
            else:  # center
                x = (base_image.width - overlay_width) // 2
                y = (base_image.height - overlay_height) // 2

            # Convert base to RGBA if needed
            if base_image.mode != 'RGBA':
                base_image = base_image.convert('RGBA')

            # Paste overlay
            base_image.paste(overlay, (x, y), overlay)

            # Convert back to RGB
            base_image = base_image.convert('RGB')

            return base_image
        except Exception as e:
            logger.error(f"Error applying photo overlay: {e}")
            return base_image


def create_default_photo_preset() -> Dict[str, Any]:
    """Create default photo uniquification preset.

    Returns:
        Default preset configuration
    """
    return {
        "methods": [
            # THREE CORE EFFECTS - all applied together, scaled by intensity
            # Effect 1: NOISE (grain texture like left image)
            {
                "name": "noise",
                "enabled": True,
                "intensity": [30, 80]  # Visible grain - scales with intensity
            },
            # Effect 2: SPARKLES (star points like center image)
            {
                "name": "sparkles",
                "enabled": True,
                "count": [60, 150],  # Star count - scales with intensity
                "size": [4, 10]  # Star size
            },
            # Effect 3: GLOW (soft light spots like right image)
            {
                "name": "glow",
                "enabled": True,
                "count": [8, 20],  # Glow spots count - scales with intensity
                "intensity": [0.3, 0.6]  # Glow opacity
            },
            # SUBTLE ADJUSTMENTS - always minimal, don't interfere with content
            {
                "name": "brightness",
                "enabled": True,
                "factor": [1.0, 1.03]  # ONLY brighten, NEVER darken (0% to +3%)
            },
            {
                "name": "contrast",
                "enabled": True,
                "factor": [0.98, 1.02]  # Very subtle contrast change (±2%)
            },
            {
                "name": "hue",
                "enabled": True,
                "shift": [-3, 3]  # Minimal color shift (±3 degrees)
            },
            {
                "name": "blur",
                "enabled": True,
                "radius": [0.1, 0.3]  # Barely noticeable blur
            },
            # DISABLED - too distracting or changes composition
            {
                "name": "lens_flare",
                "enabled": False,
                "intensity": [0.3, 0.7]  # Disabled - creates annoying circles
            },
            {
                "name": "crop",
                "enabled": False,
                "crop_percent": [1, 3]
            }
        ]
    }

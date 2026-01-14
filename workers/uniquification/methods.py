"""Uniquification methods for images and videos."""

import random
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw
from typing import Tuple, List


def add_noise(image: Image.Image, intensity: Tuple[int, int] = (5, 15)) -> Image.Image:
    """Add random noise to image.

    Args:
        image: Input image
        intensity: Range of noise intensity (min, max)

    Returns:
        Image with added noise
    """
    img_array = np.array(image)
    noise_intensity = random.randint(*intensity)

    # Generate noise
    noise = np.random.randint(-noise_intensity, noise_intensity + 1, img_array.shape, dtype=np.int16)

    # Add noise to image
    noisy_array = np.clip(img_array.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    return Image.fromarray(noisy_array)


def add_sparkles(
    image: Image.Image,
    count: Tuple[int, int] = (10, 30),
    size: Tuple[int, int] = (2, 5),
    colors: List[Tuple[int, int, int, int]] = None
) -> Image.Image:
    """Add sparkle/star effects to image.

    Args:
        image: Input image
        count: Range of sparkles count (min, max)
        size: Range of sparkle size (min, max)
        colors: List of possible RGBA colors for sparkles

    Returns:
        Image with sparkles
    """
    if colors is None:
        colors = [
            (255, 255, 255, 200),  # White
            (255, 255, 150, 180),  # Light yellow
            (200, 200, 255, 180),  # Light blue
        ]

    img = image.copy()
    draw = ImageDraw.Draw(img, 'RGBA')
    width, height = img.size

    sparkle_count = random.randint(*count)

    for _ in range(sparkle_count):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        sparkle_size = random.randint(*size)
        color = random.choice(colors)

        # Draw a star shape
        # Center point
        draw.ellipse(
            [x - sparkle_size, y - sparkle_size, x + sparkle_size, y + sparkle_size],
            fill=color
        )

        # Add rays
        ray_length = sparkle_size * 2
        # Horizontal ray
        draw.line([x - ray_length, y, x + ray_length, y], fill=color, width=1)
        # Vertical ray
        draw.line([x, y - ray_length, x, y + ray_length], fill=color, width=1)
        # Diagonal rays
        draw.line([x - ray_length, y - ray_length, x + ray_length, y + ray_length], fill=color, width=1)
        draw.line([x - ray_length, y + ray_length, x + ray_length, y - ray_length], fill=color, width=1)

    return img


def add_lens_flare(
    image: Image.Image,
    intensity: Tuple[float, float] = (0.3, 0.7),
    position: Tuple[str, str] = None
) -> Image.Image:
    """Add lens flare effect to image.

    Args:
        image: Input image
        intensity: Range of flare intensity (min, max)
        position: Position of flare (e.g., ('top', 'left'))

    Returns:
        Image with lens flare
    """
    img = image.copy().convert('RGBA')
    width, height = img.size

    # Create flare layer
    flare = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(flare, 'RGBA')

    # Determine position
    if position is None:
        h_pos = random.choice(['left', 'center', 'right'])
        v_pos = random.choice(['top', 'center', 'bottom'])
    else:
        v_pos, h_pos = position

    # Calculate center coordinates
    if h_pos == 'left':
        x = width // 4
    elif h_pos == 'right':
        x = 3 * width // 4
    else:
        x = width // 2

    if v_pos == 'top':
        y = height // 4
    elif v_pos == 'bottom':
        y = 3 * height // 4
    else:
        y = height // 2

    # Add randomness to position
    x += random.randint(-width // 10, width // 10)
    y += random.randint(-height // 10, height // 10)

    flare_intensity = random.uniform(*intensity)
    alpha = int(255 * flare_intensity)

    # Draw multiple circles for flare effect
    max_radius = min(width, height) // 2
    for i in range(5):
        radius = max_radius // (i + 1)
        color_alpha = alpha // (i + 2)
        color = (255, 255, 200, color_alpha)  # Yellowish white

        draw.ellipse(
            [x - radius, y - radius, x + radius, y + radius],
            fill=color
        )

    # Composite flare onto image
    result = Image.alpha_composite(img, flare)

    return result.convert(image.mode)


def rotate_image(image: Image.Image, angle: Tuple[float, float] = (-3, 3)) -> Image.Image:
    """Rotate image by random angle.

    Args:
        image: Input image
        angle: Range of rotation angle in degrees (min, max)

    Returns:
        Rotated image
    """
    rotation_angle = random.uniform(*angle)
    return image.rotate(rotation_angle, expand=False, fillcolor='white')


def adjust_brightness(image: Image.Image, factor: Tuple[float, float] = (0.95, 1.05)) -> Image.Image:
    """Adjust image brightness.

    Args:
        image: Input image
        factor: Range of brightness factor (min, max). 1.0 is original

    Returns:
        Image with adjusted brightness
    """
    brightness_factor = random.uniform(*factor)
    enhancer = ImageEnhance.Brightness(image)
    return enhancer.enhance(brightness_factor)


def adjust_contrast(image: Image.Image, factor: Tuple[float, float] = (0.95, 1.05)) -> Image.Image:
    """Adjust image contrast.

    Args:
        image: Input image
        factor: Range of contrast factor (min, max). 1.0 is original

    Returns:
        Image with adjusted contrast
    """
    contrast_factor = random.uniform(*factor)
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(contrast_factor)


def adjust_hue(image: Image.Image, shift: Tuple[int, int] = (-5, 5)) -> Image.Image:
    """Adjust image hue.

    Args:
        image: Input image
        shift: Range of hue shift in degrees (min, max)

    Returns:
        Image with adjusted hue
    """
    img_array = np.array(image.convert('HSV'))
    hue_shift = random.randint(*shift)

    # Shift hue channel
    img_array[:, :, 0] = (img_array[:, :, 0].astype(np.int16) + hue_shift) % 256

    result = Image.fromarray(img_array, 'HSV')
    return result.convert(image.mode)


def apply_blur(image: Image.Image, radius: Tuple[float, float] = (0.5, 2.0)) -> Image.Image:
    """Apply subtle blur to image.

    Args:
        image: Input image
        radius: Range of blur radius (min, max)

    Returns:
        Blurred image
    """
    blur_radius = random.uniform(*radius)
    return image.filter(ImageFilter.GaussianBlur(radius=blur_radius))


# Method registry for dynamic execution
METHOD_REGISTRY = {
    'noise': add_noise,
    'sparkles': add_sparkles,
    'lens_flare': add_lens_flare,
    'rotate': rotate_image,
    'brightness': adjust_brightness,
    'contrast': adjust_contrast,
    'hue': adjust_hue,
    'blur': apply_blur,
}

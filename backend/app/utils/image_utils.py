"""
Image Utilities

Helper functions for image manipulation.
"""

from typing import Tuple
from PIL import Image


def get_image_dimensions(image_path: str) -> Tuple[int, int]:
    """Get width and height of an image."""
    with Image.open(image_path) as img:
        return img.size


def resize_image(image: Image.Image, max_size: int = 2048) -> Image.Image:
    """
    Resize image if it exceeds max_size while maintaining aspect ratio.

    Args:
        image: PIL Image.
        max_size: Maximum dimension (width or height).

    Returns:
        Resized PIL Image.
    """
    width, height = image.size
    if max(width, height) <= max_size:
        return image

    ratio = max_size / max(width, height)
    new_size = (int(width * ratio), int(height * ratio))
    return image.resize(new_size, Image.LANCZOS)


def convert_to_rgb(image: Image.Image) -> Image.Image:
    """Convert image to RGB mode (removes alpha channel if present)."""
    if image.mode != "RGB":
        return image.convert("RGB")
    return image

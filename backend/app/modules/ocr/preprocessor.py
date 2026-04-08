"""
Image Preprocessor

Handles image preprocessing for OCR:
- PDF to image conversion (via pdf2image + Poppler)
- Noise removal
- Skew correction
- Binarization
- Contrast enhancement
"""

import os
import tempfile
from typing import List, Tuple

from PIL import Image, ImageFilter, ImageEnhance


class ImagePreprocessor:
    """
    Preprocesses document images to improve OCR accuracy.

    Saves processed images to a temporary directory on disk and returns
    their file paths (required by TextExtractor, which encodes images
    from disk as base64).

    Returns:
        (image_paths, temp_dir) — caller is responsible for deleting
        temp_dir after use (OCRService already does this in its finally block).
    """

    async def preprocess(
        self, file_path: str, file_type: str
    ) -> Tuple[List[str], str]:
        """
        Preprocess a document file into clean images saved to disk.

        Args:
            file_path: Path to the source file.
            file_type: MIME type (e.g. "application/pdf").

        Returns:
            Tuple of (list_of_image_paths, temp_directory_path).
        """
        temp_dir = tempfile.mkdtemp(prefix="ocr_pages_")

        # Convert source file → PIL images
        if "pdf" in file_type:
            pil_images = await self._pdf_to_images(file_path)
        else:
            pil_images = [Image.open(file_path)]

        # Apply preprocessing pipeline and save each page to disk
        image_paths: List[str] = []
        for i, img in enumerate(pil_images):
            img = self._convert_to_grayscale(img)
            img = self._remove_noise(img)
            img = self._enhance_contrast(img)
            img = self._binarize(img)

            out_path = os.path.join(temp_dir, f"page_{i + 1:04d}.jpg")
            img.save(out_path, format="JPEG", quality=95)
            image_paths.append(out_path)

        return image_paths, temp_dir

    # ------------------------------------------------------------------ #
    #  PDF → PIL images                                                    #
    # ------------------------------------------------------------------ #

    async def _pdf_to_images(self, pdf_path: str) -> List[Image.Image]:
        """
        Convert every PDF page to a PIL Image using pdf2image + Poppler.

        Requires:
            pip install pdf2image
            Poppler binaries on PATH  (https://github.com/oschwartz10612/poppler-windows/releases)
        """
        try:
            from pdf2image import convert_from_path
            pages = convert_from_path(pdf_path, dpi=300)
            return pages
        except ImportError:
            raise RuntimeError(
                "pdf2image is not installed. Run: pip install pdf2image\n"
                "Also ensure Poppler is installed and its bin/ folder is on PATH."
            )
        except Exception as e:
            raise RuntimeError(f"PDF conversion failed for '{pdf_path}': {e}") from e

    # ------------------------------------------------------------------ #
    #  Image transforms                                                    #
    # ------------------------------------------------------------------ #

    def _convert_to_grayscale(self, image: Image.Image) -> Image.Image:
        """Convert image to grayscale."""
        return image.convert("L")

    def _remove_noise(self, image: Image.Image) -> Image.Image:
        """Apply median filter to remove noise."""
        return image.filter(ImageFilter.MedianFilter(size=3))

    def _enhance_contrast(self, image: Image.Image) -> Image.Image:
        """Enhance image contrast for better text visibility."""
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(1.5)

    def _binarize(self, image: Image.Image, threshold: int = 128) -> Image.Image:
        """
        Apply binary thresholding.
        Converts to black & white using the given threshold.
        """
        return image.point(lambda p: 255 if p > threshold else 0, "L")
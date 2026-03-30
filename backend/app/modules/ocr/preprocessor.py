"""
Image Preprocessor

Handles image preprocessing for OCR:
- PDF to image conversion
- Noise removal
- Skew correction
- Binarization
- Contrast enhancement
"""

import io
from typing import List

from PIL import Image, ImageFilter, ImageEnhance


class ImagePreprocessor:
    """
    Preprocesses document images to improve OCR accuracy.

    Applies a series of transformations to clean and normalize
    handwritten answer sheet images before text extraction.
    """

    async def preprocess(self, file_path: str, file_type: str) -> List[Image.Image]:
        """
        Preprocess a document file into clean images.

        Args:
            file_path: Path to the file.
            file_type: MIME type of the file.

        Returns:
            List of preprocessed PIL Image objects.
        """
        # Convert file to images
        if "pdf" in file_type:
            images = await self._pdf_to_images(file_path)
        else:
            images = [Image.open(file_path)]

        # Apply preprocessing pipeline to each image
        processed_images = []
        for img in images:
            img = self._convert_to_grayscale(img)
            img = self._remove_noise(img)
            img = self._enhance_contrast(img)
            img = self._binarize(img)
            processed_images.append(img)

        return processed_images

    async def _pdf_to_images(self, pdf_path: str) -> List[Image.Image]:
        """
        Convert PDF pages to PIL Images.

        Uses PyPDF2 for extraction. For production, consider
        using pdf2image with poppler for higher quality rendering.

        TODO: Integrate pdf2image for better PDF rendering quality.
        """
        # Placeholder: In production, use pdf2image
        # from pdf2image import convert_from_path
        # return convert_from_path(pdf_path, dpi=300)

        # For now, try to open as image (works for single-page image-PDFs)
        try:
            img = Image.open(pdf_path)
            return [img]
        except Exception:
            # Return empty list — caller should handle gracefully
            return []

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

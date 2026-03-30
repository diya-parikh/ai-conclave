"""
Text Extractor

Extracts text from preprocessed images using QWEN V3 Vision Model
via Hugging Face Transformers.
"""

import io
import base64
from typing import List

from PIL import Image

from app.core.config import settings


class TextExtractor:
    """
    Extracts text from handwritten answer sheet images using
    QWEN V3 Vision Language Model via Hugging Face Transformers.

    The model is loaded lazily on first use to avoid heavy
    memory allocation at startup.
    """

    def __init__(self):
        self._model = None
        self._processor = None

    def _load_model(self):
        """
        Lazy-load the QWEN V3 Vision model and processor.

        TODO: Implement actual model loading:
            from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
            self._processor = AutoProcessor.from_pretrained(settings.QWEN_MODEL)
            self._model = Qwen2VLForConditionalGeneration.from_pretrained(
                settings.QWEN_MODEL,
                torch_dtype="auto",
                device_map="auto",
            )
        """
        # Placeholder — model loading is deferred to implementation phase
        pass

    async def extract(self, images: List[Image.Image]) -> str:
        """
        Extract text from a list of preprocessed images.

        Sends each image to the QWEN V3 model with a prompt
        instructing it to read and transcribe handwritten text.

        Args:
            images: List of preprocessed PIL Image objects.

        Returns:
            Concatenated extracted text from all images.

        TODO: Implement actual QWEN V3 inference:
            1. Load model if not loaded
            2. For each image, create conversation with image + prompt
            3. Process with model and decode output
            4. Concatenate results
        """
        if not images:
            return ""

        # Placeholder implementation
        # In production, this calls the QWEN V3 model
        extracted_texts = []

        for i, image in enumerate(images):
            text = await self._extract_single(image, page_num=i + 1)
            extracted_texts.append(text)

        return "\n\n".join(extracted_texts)

    async def _extract_single(self, image: Image.Image, page_num: int = 1) -> str:
        """
        Extract text from a single image using QWEN V3.

        Args:
            image: Preprocessed PIL Image.
            page_num: Page number for context.

        Returns:
            Extracted text string.

        TODO: Implement the actual inference:
            prompt = (
                "You are reading a handwritten student answer sheet. "
                "Please transcribe all the handwritten text accurately. "
                "Preserve question numbers like Q1, Q2, etc. "
                "Output the text exactly as written."
            )
            messages = [
                {"role": "user", "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompt},
                ]}
            ]
            inputs = self._processor(messages, return_tensors="pt").to("cuda")
            output_ids = self._model.generate(**inputs, max_new_tokens=2048)
            return self._processor.decode(output_ids[0], skip_special_tokens=True)
        """
        # Placeholder — returns stub text for development
        return f"[Page {page_num} — QWEN V3 OCR extraction pending implementation]"

    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string."""
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

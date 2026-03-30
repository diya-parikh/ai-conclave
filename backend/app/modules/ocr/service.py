"""
OCR Service

Orchestrates the complete OCR pipeline:
1. Image preprocessing (noise removal, skew correction, binarization)
2. Text extraction via QWEN V3 Vision Model
3. Question-wise text segmentation

This is the main entry point for the OCR module.
"""

from typing import Dict

from app.modules.ocr.preprocessor import ImagePreprocessor
from app.modules.ocr.extractor import TextExtractor
from app.modules.ocr.segmenter import TextSegmenter


class OCRService:
    """
    Orchestrates the OCR pipeline for handwritten answer sheet processing.

    Usage:
        service = OCRService()
        result = await service.process("path/to/file.pdf", "application/pdf")
        # result = {"Q1": "answer text", "Q2": "answer text", ...}
    """

    def __init__(self):
        self.preprocessor = ImagePreprocessor()
        self.extractor = TextExtractor()
        self.segmenter = TextSegmenter()

    async def process(self, file_path: str, file_type: str) -> Dict[str, str]:
        """
        Process a document through the full OCR pipeline.

        Args:
            file_path: Path to the uploaded file.
            file_type: MIME type of the file.

        Returns:
            Dictionary mapping question IDs to extracted answer text.
            Example: {"Q1": "The CPU is...", "Q2": "An algorithm is..."}
        """
        # Step 1: Preprocess images
        # Convert PDF pages or images to preprocessed, clean images
        images = await self.preprocessor.preprocess(file_path, file_type)

        # Step 2: Extract text using Vision Model (QWEN V3)
        raw_text = await self.extractor.extract(images)

        # Step 3: Segment text into question-answer pairs
        structured_text = await self.segmenter.segment(raw_text)

        return structured_text

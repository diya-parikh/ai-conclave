"""
NLP Service

Orchestrates the lightweight NLP processing pipeline:
1. Text cleaning and normalization
2. Sentence tokenization & intelligent chunking
3. Semantic chunk typing/classification
4. Sentence-BERT embedding generation per chunk
"""

import json
from typing import Dict, List, Any, Union

from app.modules.nlp.cleaner import TextCleaner
from app.modules.nlp.chunker import TextChunker
from app.modules.nlp.classifier import ChunkClassifier
from app.modules.nlp.embeddings import EmbeddingGenerator


class NLPService:
    """
    Orchestrates the simplified text processing pipeline optimized for RAG.

    Takes structured JSON from OCR, cleans text, splits into semantic chunks,
    classifies chunks, and generates embeddings per chunk.
    """

    def __init__(self):
        self.cleaner = TextCleaner()
        self.chunker = TextChunker()
        self.classifier = ChunkClassifier()
        self.embedding_generator = EmbeddingGenerator()

    async def process(self, extracted_data: Union[str, List[Dict[str, Any]], Dict[str, str]]) -> Dict[str, Any]:
        """
        Process extracted text through the RAG-optimized NLP pipeline.

        Args:
            extracted_data: Module 1 output mapping format.

        Returns:
            Dict mapping question IDs to the original answer and evaluated chunks:
            {
                "Q1": {
                    "original_answer": "...",
                    "chunks": [
                        {
                            "chunk_id": "Q1_chunk_1",
                            "chunk": "...",
                            "embedding": [...],
                            "metadata": {
                                "question_id": "Q1",
                                "diagram_present": False,
                                "diagram_description": "",
                                "source": "student_answer",
                                "type": "definition"
                            }
                        }
                    ]
                }
            }
        """
        if isinstance(extracted_data, str):
            if extracted_data.endswith('.docx'):
                extracted_data = extracted_data.replace('.docx', '.json')
            if extracted_data.endswith('.json'):
                try:
                    with open(extracted_data, 'r', encoding='utf-8') as f:
                        records = json.load(f)
                except Exception:
                    records = []
            else:
                records = []
        elif isinstance(extracted_data, dict):
            records = [
                {
                    "question_id": k,
                    "answer": v,
                    "diagram_present": False,
                    "diagram_description": ""
                }
                for k, v in extracted_data.items()
            ]
        elif isinstance(extracted_data, list):
            records = extracted_data
        else:
            records = []

        processed_output = {}

        for record in records:
            question_id = record.get("question_id")
            answer_text = record.get("answer", "")
            diagram_present = record.get("diagram_present", False)
            diagram_description = record.get("diagram_description", "")

            if not question_id:
                continue

            # Step 1: Clean and normalize text
            cleaned_text = self.cleaner.clean(answer_text)

            # Assign question-level structure
            processed_output[question_id] = {
                "original_answer": cleaned_text,
                "chunks": []
            }

            # Step 2: Chunking
            chunks = self.chunker.chunk(cleaned_text)

            # Step 3: Generate embeddings per chunk
            if chunks:
                embeddings = await self.embedding_generator.generate_batch(chunks)
            else:
                embeddings = []

            # Step 4: Classification and Data Assembly
            for index, (chunk_text, embedding) in enumerate(zip(chunks, embeddings), start=1):
                chunk_type = self.classifier.classify(chunk_text)
                chunk_id = f"{question_id}_chunk_{index}"

                processed_output[question_id]["chunks"].append({
                    "chunk_id": chunk_id,
                    "chunk": chunk_text,
                    "embedding": embedding,
                    "metadata": {
                        "question_id": question_id,
                        "diagram_present": diagram_present,
                        "diagram_description": diagram_description,
                        "source": "student_answer",
                        "type": chunk_type
                    }
                })

        return processed_output

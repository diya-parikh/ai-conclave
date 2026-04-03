"""
Chunk Classifier

Provides lightweight, deterministic rule-based heuristics 
to assign semantic types to text chunks.
"""

import re

class ChunkClassifier:
    """
    Classifies a semantic chunk as 'steps', 'formula', 'definition', 
    'explanation', or 'mixed' based on keyword and symbol matching.
    """

    def classify(self, chunk_text: str) -> str:
        """
        Determines the semantic type of a chunk.

        Args:
            chunk_text: Cleaned text chunk.

        Returns:
            String representing the chunk type.
        """
        if not chunk_text:
            return "explanation"

        text_lower = chunk_text.lower()

        # Detect steps
        has_steps = bool(re.search(r'\b(step|steps|algorithm|procedure)\b', text_lower))

        # Detect formula (contains =, ^, +, or an isolated - sign)
        has_formula = bool(re.search(r'[=^+]', text_lower) or re.search(r'\s-\s', text_lower))

        # Detect definition ("is", "are", "refers to", "defined as", etc.)
        # Even if it doesn't strictly 'start' with these words, detecting them near the
        # subject usually indicates a definitional sentence.
        has_definition = bool(re.search(r'\b(is|are|refers to|defined as)\b', text_lower))

        # Tally the patterns detected
        detected = sum([has_steps, has_formula, has_definition])

        if detected > 1:
            return "mixed"
        elif has_steps:
            return "steps"
        elif has_formula:
            return "formula"
        elif has_definition:
            return "definition"
        else:
            return "explanation"

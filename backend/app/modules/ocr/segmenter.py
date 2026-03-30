"""
Text Segmenter

Segments raw OCR-extracted text into question-answer pairs.
Identifies question boundaries using pattern matching and
structures the output as a dictionary.
"""

import re
from typing import Dict


class TextSegmenter:
    """
    Segments raw OCR text into structured question-answer pairs.

    Detects question markers (Q1, Q2, Question 1, 1., 1), etc.)
    and splits the text accordingly.
    """

    # Patterns that identify question starts
    QUESTION_PATTERNS = [
        r"(?:^|\n)\s*(?:Q|q)\.?\s*(\d+)\s*[.:\-)]\s*",           # Q1, Q.1, q1:
        r"(?:^|\n)\s*(?:Question|question|QUESTION)\s*(\d+)\s*[.:\-)]\s*",  # Question 1
        r"(?:^|\n)\s*(?:Ans|ans|ANS|Answer|answer)\s*(\d+)\s*[.:\-)]\s*",   # Ans 1, Answer 1
        r"(?:^|\n)\s*(\d+)\s*[.)]\s+",                             # 1. or 1)
    ]

    async def segment(self, raw_text: str) -> Dict[str, str]:
        """
        Segment raw text into question-answer pairs.

        Args:
            raw_text: Raw text extracted from OCR.

        Returns:
            Dictionary mapping question IDs to answer text.
            Example: {"Q1": "The CPU processes...", "Q2": "An algorithm is..."}
        """
        if not raw_text or not raw_text.strip():
            return {}

        # Try to find question boundaries using patterns
        segments = self._find_question_boundaries(raw_text)

        # If no questions detected, treat entire text as Q1
        if not segments:
            segments = {"Q1": raw_text.strip()}

        # Clean up answer text
        cleaned_segments = {}
        for q_id, answer in segments.items():
            cleaned = answer.strip()
            if cleaned:
                cleaned_segments[q_id] = cleaned

        return cleaned_segments

    def _find_question_boundaries(self, text: str) -> Dict[str, str]:
        """
        Find question boundaries in text using pattern matching.

        Returns:
            Dictionary of question ID to answer text.
        """
        # Collect all matches with their positions
        matches = []

        for pattern in self.QUESTION_PATTERNS:
            for match in re.finditer(pattern, text):
                q_num = match.group(1)
                start_pos = match.end()
                matches.append({
                    "question_num": int(q_num),
                    "start_pos": start_pos,
                    "match_start": match.start(),
                })

        if not matches:
            return {}

        # Sort by position in text
        matches.sort(key=lambda m: m["match_start"])

        # Remove duplicates (same question number, keep first)
        seen = set()
        unique_matches = []
        for m in matches:
            if m["question_num"] not in seen:
                seen.add(m["question_num"])
                unique_matches.append(m)

        # Extract text between question boundaries
        segments = {}
        for i, match in enumerate(unique_matches):
            q_id = f"Q{match['question_num']}"

            # End position is start of next question, or end of text
            if i + 1 < len(unique_matches):
                end_pos = unique_matches[i + 1]["match_start"]
            else:
                end_pos = len(text)

            answer_text = text[match["start_pos"]:end_pos].strip()
            segments[q_id] = answer_text

        return segments

"""
Post Processor — Diagram-Aware (v4)

Key changes:
  • Recognises ALL student label styles including hyphenated forms:
      A-1  a-1  Q-1  q-1  Ans-1  ans-1  (and all dot/space/bare variants)
  • Window size is dynamic: ceil(total_pages / num_questions) + 1,
    clamped to [_MIN_WINDOW_SIZE, _MAX_WINDOW_SIZE].
  • Diagram attribution is strict — only <diagram> blocks Phase 2 copies
    verbatim into a question's text block are attributed to that question.
    The page-level meta fallback (source of cross-question mis-attribution)
    has been removed entirely.
  • JSON output schema per question:
      {
        "question_id":         str,
        "answer":              str,   ← Q+A text, diagram tags stripped
        "diagram_present":     bool,
        "diagram_description": str    ← evaluation descriptions for diagrams
                                        in this question; "" when none
      }
"""

import json
import re
import requests
from pathlib import Path
from typing import Dict, List, Tuple


class PostProcessor:
    LM_STUDIO_URL: str = "http://192.168.28.1:1234/v1/chat/completions"
    MODEL_NAME: str    = "qwen/qwen3-vl-4b"
    MAX_TOKENS: int    = 2048
    TEMPERATURE: float = 0

    WINDOW_SIZE: int = 6          # default; overridden dynamically in process()
    _MAX_WINDOW_SIZE: int = 12
    _MIN_WINDOW_SIZE: int = 2

    # Matches <diagram …> … </diagram> blocks
    _DIAGRAM_RE = re.compile(
        r'<diagram[^>]*>(.*?)</diagram>',
        re.DOTALL | re.IGNORECASE,
    )

    # ------------------------------------------------------------------ #
    #  Public entry point                                                  #
    # ------------------------------------------------------------------ #

    def process(
        self,
        docx_path: str,
        page_results: List[Tuple[str, Dict]],
    ) -> str:
        json_path   = Path(docx_path).with_suffix(".json")
        page_texts  = [text for text, _ in page_results]
        total_pages = len(page_texts)

        # ----------------------------------------------------------------
        # PHASE 1 — find the FIRST page each question appears on
        # ----------------------------------------------------------------
        print("\n[PostProcessor] Phase 1: Identifying first page of each question...")
        question_map = self._phase1_discover(page_texts)

        if not question_map:
            print("[PostProcessor] No questions found. Saving empty JSON.")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2, ensure_ascii=False)
            return str(json_path)

        num_questions = len(question_map)
        print(f"[PostProcessor] {num_questions} question(s) discovered across "
              f"{total_pages} page(s).")

        # Dynamic window: avg pages per question + 1 for overlap, clamped
        avg = max(1, total_pages / num_questions)
        window_size = max(self._MIN_WINDOW_SIZE,
                          min(int(round(avg)) + 1, self._MAX_WINDOW_SIZE))
        print(f"[PostProcessor] Dynamic window size: {window_size} page(s).")

        for qid, pg in sorted(question_map.items(), key=lambda kv: self._sort_key(kv[0])):
            print(f"  {qid} → first appears on page {pg}")

        # ----------------------------------------------------------------
        # PHASE 2 — extract each Q+A block with a focused sliding window
        # ----------------------------------------------------------------
        print("\n[PostProcessor] Phase 2: Extracting Q+A blocks (sliding window)...")

        sorted_questions = sorted(
            question_map.items(), key=lambda kv: self._sort_key(kv[0])
        )

        output_records: List[Dict] = []

        for idx, (qid, start_page) in enumerate(sorted_questions):
            # Hard stop = first page of the NEXT question (never read past it)
            if idx + 1 < len(sorted_questions):
                hard_stop = sorted_questions[idx + 1][1]
            else:
                hard_stop = total_pages + 1

            win_start = max(0, start_page - 1)
            win_end   = min(
                total_pages,
                min(win_start + window_size, hard_stop - 1),
            )
            if win_end <= win_start:
                win_end = min(win_start + 1, total_pages)

            window_text = self._build_window_text(page_texts, win_start, win_end)
            print(f"  [{qid}] Pages {win_start+1}–{win_end} ({len(window_text)} chars)...")

            raw_block = self._phase2_extract(qid, window_text)

            # Retry with expanded window (but never past hard_stop)
            if not raw_block:
                expanded_end = min(total_pages, min(win_end + 2, hard_stop - 1))
                if expanded_end > win_end:
                    print(f"  [{qid}] Retrying with expanded window "
                          f"(Pages {win_start+1}–{expanded_end})...")
                    window_text = self._build_window_text(
                        page_texts, win_start, expanded_end
                    )
                    raw_block = self._phase2_extract(qid, window_text)

            if raw_block:
                print(f"  [{qid}] ✓ {len(raw_block)} chars extracted.")
            else:
                raw_block = (
                    f"[Could not extract answer for {qid} — "
                    f"searched pages {win_start+1}–{win_end}]"
                )
                print(f"  [{qid}] ✗ No answer returned.")

            # Diagrams attributed ONLY to what Phase 2 extracted for this question.
            # No page-level meta fallback — that caused cross-question mis-attribution.
            diagram_descriptions = self._extract_diagram_descriptions(raw_block)
            clean_answer         = self._strip_diagram_tags(raw_block)

            record = {
                "question_id":         qid,
                "answer":              clean_answer.strip(),
                "diagram_present":     bool(diagram_descriptions),
                "diagram_description": "\n\n".join(diagram_descriptions),
            }
            output_records.append(record)

        # Sort naturally by question number
        output_records.sort(key=lambda r: self._sort_key(r["question_id"]))

        print(f"\n[PostProcessor] {len(output_records)} Q&A record(s) complete.")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(output_records, f, indent=2, ensure_ascii=False)

        print(f"[PostProcessor] Saved: {json_path}")
        return str(json_path)

    # ------------------------------------------------------------------ #
    #  Diagram helpers                                                     #
    # ------------------------------------------------------------------ #

    def _extract_diagram_descriptions(self, text: str) -> List[str]:
        """
        Return the inner content of every <diagram> block in `text`.
        Only what Phase 2 explicitly copied into this question's block is
        returned — never pulled from the page-level meta to prevent
        cross-question mis-attribution.
        """
        return [m.group(1).strip() for m in self._DIAGRAM_RE.finditer(text)]

    def _strip_diagram_tags(self, text: str) -> str:
        """Remove <diagram> … </diagram> blocks, leaving clean Q+A text."""
        return self._DIAGRAM_RE.sub("", text).strip()

    # ------------------------------------------------------------------ #
    #  Phase 1 — full document scan                                       #
    # ------------------------------------------------------------------ #

    def _phase1_discover(self, page_texts: List[str]) -> Dict[str, int]:
        numbered_pages = ""
        for i, text in enumerate(page_texts):
            # Strip diagram tags before sending to keep the prompt concise
            clean = self._strip_diagram_tags(text)
            numbered_pages += f"\n=== PAGE {i+1} ===\n{clean.strip()}\n"

        prompt = f"""
                    You are given the full OCR text of a scanned exam/assignment document, already split by page.

                    Your task:
                    Identify EVERY top-level question or answer block and determine the page number where it FIRST appears.

                    -------------------------
                    LABEL VARIATIONS TO MATCH
                    -------------------------

                    Question labels may appear in many forms:

                    Standard:
                    Q1, Q1., Q1), Q1:, Q.1, Q-1, Q 1

                    Numbered:
                    1., 1), (1), 1:

                    Section-based:
                    8.1, 8.2, 8.3, 8.4  (use LAST number → Q1, Q2, Q3, Q4)

                    Answer formats (must also be treated as questions):
                    A1, A.1, A-1, A 1, A1., A1)
                    a1, a.1, a-1, a 1
                    Ans1, Ans.1, Ans-1, Ans 1
                    ans1, ans.1, ans-1, ans 1

                    IMPORTANT:
                    Students often write A-2, A-3 etc. → treat these EXACTLY as Q2, Q3.

                    -------------------------
                    CRITICAL RULES
                    -------------------------

                    1. Canonical Mapping:
                    Convert ALL detected labels into format:
                    Q1, Q2, Q3, ...

                    Examples:
                    A-2, a-2, Ans-2, ans 2, A2 → Q2
                    Q-3, q-3, Q3 → Q3
                    8.4 → Q4 (use LAST number)

                    2. Sub-parts Handling:
                    DO NOT treat sub-parts as separate questions.

                    3. Page Mapping:
                    - Use the FIRST page where the label appears
                    - Page numbers are given as:
                    === PAGE N ===

                    4. Multiple questions can start on the same page → include all

                    5. Completeness:
                    a. Ensure NO question is missed
                    b. Ensure all the content of every answer is present in the JSON.

                    -------------------------
                    OUTPUT FORMAT (STRICT)
                    -------------------------

                    Return ONLY a valid JSON array.
                    Format:
                    [
                    {{"id": "Q1", "page": 1}},
                    {{"id": "Q2", "page": 2}}
                    ]

                    -------------------------
                    DOCUMENT TEXT
                    -------------------------

                    {numbered_pages}
                """

        raw = self._call_qwen(prompt)
        return self._parse_question_map(raw)

    def _parse_question_map(self, raw: str) -> Dict[str, int]:
        clean = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
        try:
            items = json.loads(clean)
        except json.JSONDecodeError:
            m = re.search(r"\[.*?\]", clean, re.DOTALL)
            if m:
                try:
                    items = json.loads(m.group())
                except json.JSONDecodeError:
                    print("  [Phase 1] Could not parse Qwen response.")
                    return {}
            else:
                return {}

        if not isinstance(items, list):
            return {}

        result: Dict[str, int] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            raw_id = str(item.get("id", "")).strip()
            qid    = self._normalise_key(raw_id)
            try:
                page = max(1, int(item.get("page", 1)))
            except (ValueError, TypeError):
                page = 1
            if qid:
                if qid not in result or page < result[qid]:
                    result[qid] = page

        return result

    # ------------------------------------------------------------------ #
    #  Phase 2 — focused single-question extraction                       #
    # ------------------------------------------------------------------ #

    def _phase2_extract(self, qid: str, window_text: str) -> str:
        bare_number = re.sub(r"[^\d]", "", qid)
        n = int(bare_number)

        # Every surface form a student might write for question/answer N
        label_variants = (
            f"Q{n}  /  Q.{n}  /  Q-{n}  /  Q {n}  /  Q{n}.  /  Q{n})  /  Q{n}:\n"
            f"  A{n}  /  A.{n}  /  A-{n}  /  A {n}  /  A{n}.  /  A{n})\n"
            f"  a{n}  /  a.{n}  /  a-{n}  /  a {n}\n"
            f"  Ans{n}  /  Ans.{n}  /  Ans-{n}  /  Ans {n}\n"
            f"  ans{n}  /  ans.{n}  /  ans-{n}  /  ans {n}\n"
            f"  {n}.  /  {n})  /  ({n})"
        )

        # Every surface form for the NEXT question — used as the stop signal
        m = n + 1
        next_label_variants = (
            f"Q{m}  /  Q.{m}  /  Q-{m}  /  Q {m}  /  Q{m}.  /  Q{m})\n"
            f"  A{m}  /  A.{m}  /  A-{m}  /  A {m}  /  A{m}.  /  A{m})\n"
            f"  a{m}  /  a.{m}  /  a-{m}  /  a {m}\n"
            f"  Ans{m}  /  Ans.{m}  /  Ans-{m}  /  Ans {m}\n"
            f"  ans{m}  /  ans.{m}  /  ans-{m}  /  ans {m}\n"
            f"  {m}.  /  {m})  /  ({m})"
        )

        prompt = f"""
                    You are given OCR text from consecutive pages of a scanned exam document.
                    The text may contain <diagram> ... </diagram> blocks.

                    -------------------------
                    TASK
                    -------------------------

                    Extract the COMPLETE answer block for Question {n}.

                    -------------------------
                    IMPORTANT CONTEXT
                    -------------------------

                    - The examiner may label the question as: Q{n}
                    - The student's answer may be labelled differently, such as:
                    A-{n}, A{n}, Ans-{n}, Ans{n}, a{n}, a-{n}, etc.

                    - BOTH the question label AND student answer label belong to the SAME block.

                    - You must extract EVERYTHING from:
                    → the FIRST occurrence of any label for {n}
                    → UNTIL the FIRST occurrence of any label for {m}

                    -------------------------
                    LABEL VARIATIONS
                    -------------------------

                    All valid labels for Question/Answer {n}:
                    {label_variants}

                    Stop extraction when you encounter ANY label for Question/Answer {m}:
                    {next_label_variants}

                    -------------------------
                    RULES (STRICT)
                    -------------------------

                    1. Start from the FIRST occurrence of any valid label for {n}
                    2. Include ALL sub-parts (a), b), i), ii), etc.
                    3. Include the FULL student answer (no truncation)
                    4. Preserve ALL <diagram> ... </diagram> blocks exactly as they appear
                    5. STOP immediately when a label for {m} appears
                    6. Do NOT include any content from the next question
                    7. If NO label for {n} is found, return EXACTLY:
                    NOT_FOUND

                    -------------------------
                    OUTPUT FORMAT
                    -------------------------

                    - Return ONLY the extracted text block
                    - NO explanations
                    - NO markdown
                    - NO extra text

                    -------------------------
                    DOCUMENT TEXT
                    -------------------------

                    {window_text}
                """

        raw = self._call_qwen(prompt)
        if not raw or raw.strip().upper() == "NOT_FOUND":
            return ""
        return raw.strip()

    # ------------------------------------------------------------------ #
    #  Shared helpers                                                      #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _build_window_text(
        page_texts: List[str], win_start: int, win_end: int
    ) -> str:
        parts = []
        for i in range(win_start, win_end):
            parts.append(f"=== PAGE {i+1} ===\n{page_texts[i].strip()}")
        return "\n\n".join(parts)

    def _call_qwen(self, prompt: str) -> str:
        payload = {
            "model":       self.MODEL_NAME,
            "temperature": self.TEMPERATURE,
            "max_tokens":  self.MAX_TOKENS,
            "messages": [{"role": "user", "content": prompt}],
        }
        try:
            response = requests.post(
                self.LM_STUDIO_URL, json=payload, timeout=180
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
            return content.strip()
        except Exception as e:
            print(f"    [Qwen error] {e}")
            return ""

    @staticmethod
    def _normalise_key(key: str) -> str:
        """
        Normalise any student label into canonical form Q<N>.

        Handles (case-insensitive):
          Q1  Q.1  Q-1  Q 1  Q1.  Q1)  Q1:
          A1  A.1  A-1  A 1  (answer labels treated same as question labels)
          a1  a.1  a-1  a 1
          Ans1  Ans.1  Ans-1  Ans 1  ans …
          1.  1)  (1)  1:          (bare numbers)
          8.1  8.2  8.3            (section-dot-number → last number)
        """
        key = key.strip()

        # section-dot-number: e.g. "8.4" → Q4
        section_dot = re.match(r"^\d+\.(\d+)$", key)
        if section_dot:
            return f"Q{int(section_dot.group(1))}"

        # Strip "Ans" / "ans" prefix (with any trailing separator: space . - )
        key = re.sub(r"^[Aa][Nn][Ss][\s.\-]*", "", key).strip()

        # Strip leading Q/q/A/a followed by any separator (space, dot, hyphen)
        key = re.sub(r"^[QqAa][\s.\-]*", "", key).strip()

        # Strip surrounding brackets / punctuation that may still be there
        key = key.lstrip("(").rstrip(").:")

        # Now key should be just the number (possibly with trailing garbage)
        if not key:
            return ""

        # Prefix Q and uppercase
        canonical = "Q" + key.upper()
        m = re.match(r"(Q\d+)", canonical)
        return m.group(1) if m else ""

    @staticmethod
    def _sort_key(qid: str) -> int:
        m = re.search(r"\d+", qid)
        return int(m.group()) if m else 0
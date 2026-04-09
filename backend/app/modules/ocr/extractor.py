"""
Text + Diagram Extractor (Unified)

Single Qwen-Vision call per page that simultaneously:
  • Transcribes all visible text (OCR), enforcing question/answer label line breaks
  • Detects diagrams / figures / tables / graphs
  • Produces a structured 5-field evaluation description per diagram inline
    using <diagram> … </diagram> tags (no reconstruction / ASCII art)

meta schema per page:
    {
        "diagram_present": bool,
        "diagrams": [
            {
                "index":       int,  # 1-based order on this page
                "description": str   # full evaluation block inside <diagram> tag
            },
            ...
        ]
    }
"""

import re
import requests
from typing import List, Tuple, Dict


# ------------------------------------------------------------------ #
#  Prompt used for each page                                          #
# ------------------------------------------------------------------ #

_PAGE_PROMPT = """You are an expert OCR engine with advanced visual understanding \
and diagram evaluation capability.

Your task for this page image:

1. TRANSCRIBE every word, number, symbol, and line of text exactly as written.
   Do NOT skip, summarise, or paraphrase anything.

   QUESTION / ANSWER LABEL FORMATTING RULE (apply before anything else):
   Whenever you encounter a question or answer label in ANY of these forms —
     Q1  Q1.  Q1)  Q-1  Q.1  Q 1
     A1  A1.  A1)  A-1  A.1  A 1
     a1  a1.  a1)  a-1  a.1  a 1
     Ans1  Ans.1  Ans-1  Ans 1
     1.   1)   (1)   8.1  8.2  (section-dot-number)
   — ALWAYS place that label on its OWN line. Insert a newline BEFORE the label
   and start the answer/question text on the NEXT line. Never run a label and
   its content together on the same line.

   Example: image shows "some text  A-2. Backpropagation is …"
   Transcribe as:
     some text
     A-2.
     Backpropagation is …

2. DETECT diagrams, figures, graphs, tables, circuit diagrams, flowcharts,
   geometric figures, or any non-text visual element.

3. For EACH diagram / figure found, insert a structured evaluation block at the
   exact position in the text where it appears, using this format:

   <diagram index="N">
   Type: <e.g. circuit diagram / bar graph / geometric figure / table / flowchart>

   Key Labels:
   <List every visible label, component name, node, axis title, legend entry, or
   annotation. Note whether all required components are present and correctly named.
   Flag any missing or mislabelled elements.>

   Connections Between Elements:
   <Describe how elements are connected — lines, arrows, edges, wires, branches.
   Identify what connects to what and the nature of each connection (directed /
   undirected, solid / dashed, single / double, etc.).>

   Directionality:
   <Describe the flow direction indicated by arrows or other directional markers.
   State whether the direction is correct for the diagram type and context.>

   Relative Positioning:
   <Describe the spatial arrangement — left-to-right flow, top-down hierarchy,
   input → process → output layout, radial structure, etc. Note whether the
   layout matches the expected convention for this diagram type.>

   Neatness / Presentation:
   <Assess overall cleanliness and readability — straight lines, legible labels,
   consistent spacing, absence of clutter or overlapping elements.>
   </diagram>

   Replace N with the diagram's order on this page (1, 2, 3 …).

4. If there are NO diagrams on this page, output only the transcribed text.

Return ONLY the structured content described above — no extra commentary,
no markdown fences, no preamble.
"""


class TextExtractor:
    LM_STUDIO_URL: str = "http://127.0.0.1:1234/v1/chat/completions"
    MODEL_NAME: str    = "qwen/qwen3-vl-4b"
    MAX_TOKENS: int    = 4096          # diagram evaluation descriptions can be verbose
    TEMPERATURE: float = 0

    # Regex to find <diagram …> … </diagram> blocks
    _DIAGRAM_RE = re.compile(
        r'<diagram[^>]*index=["\']?(\d+)["\']?[^>]*>(.*?)</diagram>',
        re.DOTALL | re.IGNORECASE,
    )

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    async def extract(self, image_paths: List[str]) -> List[Tuple[str, Dict]]:
        """
        Returns List of (structured_page_text, meta_dict).

        structured_page_text — raw model output with <diagram> blocks inline.
        meta_dict            — parsed diagram info (see module docstring).
        """
        if not image_paths:
            return []

        results: List[Tuple[str, Dict]] = []
        for i, image_path in enumerate(image_paths):
            print(f"  [Page {i + 1}] Extracting text + diagrams...")
            structured_text = self._extract_page(image_path)
            meta = self._parse_meta(structured_text)
            diagram_count = len(meta["diagrams"])
            if diagram_count:
                print(f"  [Page {i + 1}] ✓ {diagram_count} diagram(s) detected.")
            results.append((structured_text, meta))

        return results

    # ------------------------------------------------------------------ #
    #  Core extraction                                                     #
    # ------------------------------------------------------------------ #

    def _extract_page(self, image_path: str) -> str:
        payload = self._build_payload(image_path)
        response = requests.post(self.LM_STUDIO_URL, json=payload, timeout=300)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip()
        # Strip Qwen3 <think> reasoning blocks
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
        return content.strip()

    def _build_payload(self, image_path: str) -> dict:
        image_base64 = self._encode_image(image_path)
        return {
            "model":       self.MODEL_NAME,
            "temperature": self.TEMPERATURE,
            "max_tokens":  self.MAX_TOKENS,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": _PAGE_PROMPT},
                    {"type": "image_url",
                     "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
                ],
            }],
        }

    # ------------------------------------------------------------------ #
    #  Meta parsing                                                        #
    # ------------------------------------------------------------------ #

    def _parse_meta(self, structured_text: str) -> Dict:
        diagrams = []
        for match in self._DIAGRAM_RE.finditer(structured_text):
            index = int(match.group(1))
            description = match.group(2).strip()
            diagrams.append({"index": index, "description": description})

        diagrams.sort(key=lambda d: d["index"])

        return {
            "diagram_present": bool(diagrams),
            "diagrams":        diagrams,
        }

    # ------------------------------------------------------------------ #
    #  Utility                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _encode_image(image_path: str) -> str:
        import base64
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
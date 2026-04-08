"""
model_answer_to_json.py
=======================
Converts a model-answer .docx into a JSON list of records.

Each record:
  {
    "question_id":         str,   ← canonical Q<N> form via qid_utils
    "answer":              str,
    "diagram_present":     bool,
    "diagram_description": dict
  }

question_id is always normalised through qid_utils.normalise_qid so it is
guaranteed to be in the same Q<N> form that the OCR postprocessor produces.
"""

from docx import Document
import json
import re

# Shared normaliser — single source of truth for all three pipeline stages
from qid_utils import normalise_qid


# ---------------------------------------------------------------------------
# Section splitting
# ---------------------------------------------------------------------------

# Matches the start of any answer block the teacher might write:
#   A1.  A 1.  A-1.  A.1  Ans1.  Ans 1.  Ans-1.  Ans.1
#   (all case-insensitive, dot/colon/space after the number is optional)
_ANSWER_LABEL_RE = re.compile(
    r"(?=(?:Ans|A)[\s.\-]*\d+[\s.:)])",
    re.IGNORECASE,
)


def split_into_sections(doc: Document) -> list[str]:
    full_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    sections = _ANSWER_LABEL_RE.split(full_text)
    return [s.strip() for s in sections if s.strip()]


# ---------------------------------------------------------------------------
# Question ID extraction
# ---------------------------------------------------------------------------

def extract_question_id(section_text: str) -> str | None:
    """
    Pull the first answer/question label from the section text and
    return its canonical Q<N> form via the shared normaliser.

    Returns None if no recognisable label is found.
    """
    # Look for any A-label at the very start of the block
    m = re.search(
        r"(?:Ans|A)[\s.\-]*(\d+)|Q[\s.\-]*(\d+)",
        section_text[:80],          # only scan the first ~80 chars
        re.IGNORECASE,
    )
    if m:
        number = m.group(1) or m.group(2)
        return f"Q{int(number)}"

    # Fallback: let the full normaliser try the whole first line
    first_line = section_text.splitlines()[0] if section_text else ""
    return normalise_qid(first_line)


# ---------------------------------------------------------------------------
# Diagram extraction
# ---------------------------------------------------------------------------

def parse_diagram_structure(diagram_text: str) -> dict:
    lines = [l.strip() for l in diagram_text.split("\n") if l.strip()]

    data = {
        "type": "",
        "key_labels": [],
        "connections": [],
        "directionality": "",
        "relative_positioning": "",
        "neatness": "",
    }

    current_section = None

    for line in lines:
        lower = line.lower()

        if lower.startswith("type:"):
            data["type"] = line.split(":", 1)[1].strip()
            current_section = None
        elif "key labels" in lower:
            current_section = "key_labels"
        elif "connections" in lower:
            current_section = "connections"
        elif "directionality" in lower:
            current_section = "directionality"
        elif "relative positioning" in lower:
            current_section = "relative_positioning"
        elif "neatness" in lower:
            current_section = "neatness"
        else:
            if current_section == "key_labels":
                data["key_labels"].append(line)
            elif current_section == "connections":
                data["connections"].append(line)
            elif current_section in ("directionality", "relative_positioning", "neatness"):
                data[current_section] += " " + line

    # Strip leading whitespace from accumulated string fields
    for k in ("directionality", "relative_positioning", "neatness"):
        data[k] = data[k].strip()

    return data


def extract_diagram_description(text: str) -> tuple[bool, dict]:
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if "diagram" in line.lower():
            diagram_text = "\n".join(lines[i + 1:]).strip()
            structured = parse_diagram_structure(diagram_text)
            return True, structured
    return False, {}


# ---------------------------------------------------------------------------
# Main processor
# ---------------------------------------------------------------------------

def process_docx(file_path: str) -> list[dict]:
    """
    Parse a model-answer .docx and return a list of records.

    question_id is always in canonical Q<N> form.
    Records whose question_id cannot be determined are logged and skipped.
    """
    doc = Document(file_path)
    sections = split_into_sections(doc)

    result = []
    seen_ids: set[str] = set()

    for section in sections:
        qid = extract_question_id(section)

        if qid is None:
            print(f"  [model_answer_to_json] WARNING: could not determine question_id "
                  f"for section starting: {section[:60]!r} — skipping.")
            continue

        if qid in seen_ids:
            print(f"  [model_answer_to_json] WARNING: duplicate id {qid} — "
                  f"keeping first occurrence.")
            continue
        seen_ids.add(qid)

        diagram_present, diagram_description = extract_diagram_description(section)

        result.append({
            "question_id":         qid,
            "answer":              section,
            "diagram_present":     diagram_present,
            "diagram_description": diagram_description,
        })

    result.sort(key=lambda r: int(r["question_id"][1:]))   # Q1 < Q2 < Q10
    return result


# ---------------------------------------------------------------------------
# Save helper
# ---------------------------------------------------------------------------

def save_to_json(data: list[dict], output_file: str) -> None:
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    src  = sys.argv[1] if len(sys.argv) > 1 else "modelanswer-dl.docx"
    dest = sys.argv[2] if len(sys.argv) > 2 else "output.json"
    data = process_docx(src)
    save_to_json(data, dest)
    print(f"✅ Done! {len(data)} question(s) → {dest}")
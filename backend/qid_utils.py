"""
qid_utils.py — Shared Question-ID Normalisation
================================================

Single source of truth for converting any label a student or teacher
might write into the canonical form  Q<N>  (e.g. Q1, Q2, Q3 …).

Import this module in:
  • app/modules/ocr/postprocessor.py   (Stage 1 – student OCR)
  • app/modules/ocr/model_answer_to_json.py  (model-answer parser)
  • pipeline.py                         (aggregation / lookup)

Handled forms (all case-insensitive):
  Q1   Q.1   Q-1   Q 1   Q1.   Q1)   Q1:
  A1   A.1   A-1   A 1   A1.   A1)
  a1   a.1   a-1   a 1
  Ans1   Ans.1   Ans-1   Ans 1
  ans1   ans.1   ans-1   ans 1
  1.   1)   (1)   1:          ← bare numbers
  8.1  8.2  8.3              ← section-dot-number → last number
"""

from __future__ import annotations

import re
from typing import Optional


# ---------------------------------------------------------------------------
# Core normaliser
# ---------------------------------------------------------------------------

def normalise_qid(raw: str) -> Optional[str]:
    """
    Convert any question/answer label into canonical  Q<N>  form.

    Returns None if no number can be extracted.

    Examples
    --------
    >>> normalise_qid("A-3")    → "Q3"
    >>> normalise_qid("Ans 2")  → "Q2"
    >>> normalise_qid("8.4")    → "Q4"
    >>> normalise_qid("(1)")    → "Q1"
    >>> normalise_qid("Q1.")    → "Q1"
    >>> normalise_qid("UNKNOWN")→  None
    """
    key = raw.strip()
    if not key:
        return None

    # ── section-dot-number:  8.4  →  Q4  (use the LAST number) ──────────
    section_dot = re.match(r"^\d+\.(\d+)$", key)
    if section_dot:
        return f"Q{int(section_dot.group(1))}"

    # ── strip "Ans" / "ans" prefix (any trailing separator) ─────────────
    key = re.sub(r"^[Aa][Nn][Ss][\s.\-]*", "", key).strip()

    # ── strip leading Q/q/A/a (any trailing separator) ───────────────────
    key = re.sub(r"^[QqAa][\s.\-]*", "", key).strip()

    # ── strip surrounding brackets / trailing punctuation ────────────────
    key = key.lstrip("(").rstrip(").:, ")

    if not key:
        return None

    # ── extract the leading integer ───────────────────────────────────────
    m = re.match(r"(\d+)", key)
    if not m:
        return None

    return f"Q{int(m.group(1))}"


def sort_key(qid: str) -> int:
    """Numeric sort key for Q-IDs so Q2 < Q10."""
    m = re.search(r"\d+", qid)
    return int(m.group()) if m else 0


# ---------------------------------------------------------------------------
# Index builder — used by pipeline.py for O(1) lookup
# ---------------------------------------------------------------------------

def build_index(records: list[dict], id_field: str = "question_id") -> dict[str, dict]:
    """
    Build a dict keyed by *normalised* question_id.

    Duplicate IDs (after normalisation) keep the LAST record,
    which mirrors typical document order.

    Parameters
    ----------
    records  : list of dicts each containing `id_field`
    id_field : the key inside each dict that holds the question ID string

    Returns
    -------
    { "Q1": {...}, "Q2": {...}, ... }
    """
    index: dict[str, dict] = {}
    for rec in records:
        raw_id = str(rec.get(id_field, "")).strip()
        qid = normalise_qid(raw_id)
        if qid:
            index[qid] = rec
        else:
            print(f"  [qid_utils] WARNING: could not normalise id={raw_id!r} — record skipped in index")
    return index


# ---------------------------------------------------------------------------
# Diagnostic helper — call this in tests to spot mismatches early
# ---------------------------------------------------------------------------

def check_alignment(
    student_records: list[dict],
    model_records: list[dict],
    student_id_field: str = "question_id",
    model_id_field: str = "question_id",
) -> dict:
    """
    Compare question IDs from both sources and report mismatches.

    Returns a dict with keys:
      matched        – IDs present in both (will be evaluated)
      student_only   – IDs in student answer but not in model answer
      model_only     – IDs in model answer but not in student answer
    """
    student_ids = {
        normalise_qid(str(r.get(student_id_field, "")))
        for r in student_records
    } - {None}

    model_ids = {
        normalise_qid(str(r.get(model_id_field, "")))
        for r in model_records
    } - {None}

    matched      = sorted(student_ids & model_ids, key=sort_key)
    student_only = sorted(student_ids - model_ids, key=sort_key)
    model_only   = sorted(model_ids - student_ids, key=sort_key)

    report = {
        "matched":      matched,
        "student_only": student_only,
        "model_only":   model_only,
    }

    # Print a readable summary
    print("\n  [qid_utils] ID alignment check:")
    print(f"    Matched      ({len(matched)}): {matched}")
    if student_only:
        print(f"    Student-only ({len(student_only)}): {student_only}  ← no model answer — will be skipped")
    if model_only:
        print(f"    Model-only   ({len(model_only)}): {model_only}  ← model answer with no student response")
    if not student_only and not model_only:
        print("    ✓ Perfect alignment — all IDs match.")

    return report
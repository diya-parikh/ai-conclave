"""
pipeline.py — End-to-End Evaluation Pipeline Orchestrator
==========================================================

Entry point for the full automated grading flow:

    OCR  ──►  NLP  ──►  Evaluation  ──►  Aggregated Report

Usage
-----
    # From code
    from pipeline import run_pipeline
    result = await run_pipeline(
        student_pdf_path   = "inputs/student.pdf",
        model_answer_path  = "inputs/model_answer.docx",   # or .json
        max_marks_per_q    = 10.0,
        max_diagram_marks  = 4.0,
    )

    # CLI
    python pipeline.py student.pdf model_answer.docx
    python pipeline.py student.pdf model_answer.json --max-marks 10 --max-diagram 4
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Path bootstrap
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT))

# ---------------------------------------------------------------------------
# Shared ID utilities  ← single source of truth for all Q-ID handling
# ---------------------------------------------------------------------------
from qid_utils import normalise_qid, build_index, check_alignment, sort_key

# ---------------------------------------------------------------------------
# Stage imports
# ---------------------------------------------------------------------------
from app.modules.ocr.service import OCRService
from app.modules.nlp.service import NLPService
from app.modules.evaluation.service import evaluate
from app.modules.evaluation.model_answer_to_json import process_docx


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class QuestionResult:
    question_id: str
    max_marks: float
    max_diagram_marks: float

    marks_awarded: float = 0.0
    diagram_score: float = 0.0
    final_grade: float = 0.0

    rationale: str = ""
    concept_coverage: List[str] = field(default_factory=list)
    missing_points: List[str] = field(default_factory=list)
    contradictions: List[Any] = field(default_factory=list)
    chain_of_thought: str = ""
    shap_attribution: Dict[str, float] = field(default_factory=dict)
    parameter_scores: Dict[str, float] = field(default_factory=dict)
    parameter_feedback: Dict[str, str] = field(default_factory=dict)

    num_chunks: int = 0
    chunk_types: List[str] = field(default_factory=list)

    error: Optional[str] = None


@dataclass
class PipelineResult:
    student_pdf: str
    model_answer_source: str
    total_questions: int
    evaluated_questions: int

    total_marks_awarded: float = 0.0
    total_max_marks: float = 0.0
    total_diagram_marks: float = 0.0
    total_max_diagram_marks: float = 0.0
    overall_percentage: float = 0.0
    grade_band: str = ""

    questions: List[QuestionResult] = field(default_factory=list)
    xai_report: str = ""
    elapsed_seconds: float = 0.0

    unmatched_student_ids: List[str] = field(default_factory=list)
    unmatched_model_ids: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_model_answers(path: str) -> List[Dict]:
    p = Path(path)
    if p.suffix.lower() == ".json":
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    elif p.suffix.lower() == ".docx":
        return process_docx(path)
    else:
        raise ValueError(f"Unsupported model answer format: {p.suffix!r}. Use .json or .docx")


def _normalise_records(records: List[Dict], source_label: str) -> List[Dict]:
    """
    Return a new list where every record's question_id is in canonical Q<N> form.
    Records with unresolvable IDs are logged and dropped.
    """
    out = []
    for rec in records:
        raw_id = str(rec.get("question_id", "")).strip()
        canonical = normalise_qid(raw_id)
        if canonical is None:
            print(f"  [{source_label}] WARNING: cannot normalise id={raw_id!r} — record skipped.")
            continue
        out.append({**rec, "question_id": canonical})
    return out


def _grade_band(pct: float) -> str:
    if pct >= 90: return "O (Outstanding)"
    if pct >= 75: return "A+ (Excellent)"
    if pct >= 60: return "A (Good)"
    if pct >= 50: return "B (Average)"
    if pct >= 40: return "C (Pass)"
    return "F (Fail)"


def _build_xai_report(result: PipelineResult) -> str:
    lines: List[str] = []
    sep = "=" * 70

    lines += [
        sep, "  EXPLAINABLE AI EVALUATION REPORT", sep,
        f"  Student PDF   : {result.student_pdf}",
        f"  Model Answer  : {result.model_answer_source}",
        f"  Questions     : {result.total_questions} detected, "
        f"{result.evaluated_questions} evaluated",
    ]
    if result.unmatched_student_ids:
        lines.append(f"  Skipped (no model answer) : {result.unmatched_student_ids}")
    if result.unmatched_model_ids:
        lines.append(f"  Model-only (no student Q) : {result.unmatched_model_ids}")

    lines += [
        "",
        "  ── AGGREGATE SCORES ──",
        f"  Text Marks    : {result.total_marks_awarded:.2f} / {result.total_max_marks:.2f}",
        f"  Diagram Marks : {result.total_diagram_marks:.2f} / {result.total_max_diagram_marks:.2f}",
        f"  Overall %     : {result.overall_percentage:.1f}%",
        f"  Grade Band    : {result.grade_band}",
        sep,
    ]

    for qr in result.questions:
        lines += [
            "",
            f"  ┌─ Question {qr.question_id} " + "─" * max(0, 60 - len(qr.question_id)),
            f"  │  Text  : {qr.marks_awarded:.1f} / {qr.max_marks:.1f}",
            f"  │  Diagram: {qr.diagram_score:.1f} / {qr.max_diagram_marks:.1f}",
            f"  │  Grade  : {qr.final_grade:.2f}",
            "  │",
        ]
        if qr.error:
            lines.append(f"  │  ⚠ Error: {qr.error}")
        else:
            if qr.rationale:
                lines.append("  │  Rationale:")
                for line in qr.rationale.splitlines():
                    lines.append(f"  │    {line}")
            if qr.concept_coverage:
                lines.append("  │  Concepts Covered:")
                for c in qr.concept_coverage:
                    lines.append(f"  │    ✓  {c}")
            if qr.missing_points:
                lines.append("  │  Missing / Incomplete:")
                for m in qr.missing_points:
                    lines.append(f"  │    ✗  {m}")
            if qr.contradictions:
                lines.append("  │  Contradictions:")
                for c in qr.contradictions:
                    if isinstance(c, dict):
                        lines.append(f"  │    ⚠  {c.get('missing_point', c)}")
                        if c.get("reasoning"):
                            lines.append(f"  │       → {c['reasoning']}")
                    else:
                        lines.append(f"  │    ⚠  {c}")
            if qr.parameter_scores:
                lines.append("  │  Parameter Scores:")
                for param, score in qr.parameter_scores.items():
                    bar = "█" * int(score) + "░" * max(0, 10 - int(score))
                    lines.append(f"  │    {param:<30} {score:>4.1f}  {bar}")
            if qr.chain_of_thought:
                lines.append("  │  Reasoning Chain:")
                for line in str(qr.chain_of_thought).splitlines():
                    lines.append(f"  │    {line}")
            if qr.shap_attribution:
                lines.append("  │  SHAP Token Attribution (top 10):")
                top = sorted(qr.shap_attribution.items(), key=lambda x: -abs(x[1]))[:10]
                for tok, val in top:
                    bar = "█" * int(abs(val) * 300)
                    lines.append(f"  │    {tok:<22} {val:+.4f}  {bar}")
            if qr.num_chunks:
                lines.append(
                    f"  │  NLP Chunks: {qr.num_chunks}  "
                    f"(types: {', '.join(sorted(set(qr.chunk_types)))})"
                )
        lines.append(f"  └{'─' * 67}")

    lines += ["", sep, "  END OF REPORT", sep]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------

async def run_pipeline(
    student_pdf_path: str,
    model_answer_path: str,
    max_marks_per_q: float = 10.0,
    max_diagram_marks: float = 4.0,
    output_dir: Optional[str] = None,
) -> PipelineResult:
    t_start = time.perf_counter()

    pdf_stem = Path(student_pdf_path).stem
    if output_dir is None:
        output_dir = str(Path(student_pdf_path).parent / "pipeline_output")
    os.makedirs(output_dir, exist_ok=True)

    # ── Stage 1: OCR ────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  STAGE 1 — OCR")
    print("=" * 60)
    ocr_service = OCRService()
    raw_student = await ocr_service.process(student_pdf_path, "application/pdf")
    student_records = _normalise_records(raw_student, "OCR")
    print(f"  ✓ OCR complete: {len(student_records)} question(s) extracted.")

    stage1_path = os.path.join(output_dir, f"{pdf_stem}_ocr.json")
    with open(stage1_path, "w", encoding="utf-8") as f:
        json.dump(student_records, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Saved: {stage1_path}")

    # ── Stage 2: NLP ────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  STAGE 2 — NLP")
    print("=" * 60)
    nlp_output: Dict[str, Any] = await NLPService().process(student_records)
    print(f"  ✓ NLP complete: {len(nlp_output)} question(s) processed.")

    nlp_slim = {
        qid: {
            "original_answer": qdata["original_answer"],
            "chunks": [{k: v for k, v in c.items() if k != "embedding"}
                       for c in qdata["chunks"]],
        }
        for qid, qdata in nlp_output.items()
    }
    stage2_path = os.path.join(output_dir, f"{pdf_stem}_nlp.json")
    with open(stage2_path, "w", encoding="utf-8") as f:
        json.dump(nlp_slim, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Saved: {stage2_path}")

    # ── Load & normalise model answers ───────────────────────────────────
    print("\n" + "=" * 60)
    print("  Loading model answers …")
    print("=" * 60)
    raw_model = _load_model_answers(model_answer_path)
    # model_answer_to_json already normalises, but we defensively re-normalise
    model_records = _normalise_records(raw_model, "ModelAnswer")
    print(f"  ✓ {len(model_records)} model answer(s) loaded.")

    # ── Alignment check — runs before any evaluation so mismatches are
    #    visible immediately, not discovered question-by-question ──────────
    print("\n" + "=" * 60)
    print("  ID ALIGNMENT CHECK")
    print("=" * 60)
    alignment = check_alignment(student_records, model_records)

    student_index = build_index(student_records)
    model_index   = build_index(model_records)

    # ── Stage 3: Evaluation ─────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  STAGE 3 — EVALUATION")
    print("=" * 60)

    question_results: List[QuestionResult] = []

    # Stub entries for student-only questions (surfaced in report, not silently dropped)
    for qid in sorted(alignment["student_only"], key=sort_key):
        question_results.append(QuestionResult(
            question_id=qid,
            max_marks=max_marks_per_q,
            max_diagram_marks=max_diagram_marks,
            error="No model answer available — skipped.",
        ))
        print(f"  ⚠  {qid}: no model answer — skipped.")

    for qid in sorted(alignment["matched"], key=sort_key):
        student_rec = student_index[qid]
        model_rec   = model_index[qid]

        qr = QuestionResult(
            question_id=qid,
            max_marks=max_marks_per_q,
            max_diagram_marks=max_diagram_marks,
        )
        if qid in nlp_output:
            chunks = nlp_output[qid].get("chunks", [])
            qr.num_chunks  = len(chunks)
            qr.chunk_types = [c["metadata"].get("type", "") for c in chunks]

        print(f"\n  Evaluating {qid} …")
        try:
            ev = await evaluate(
                student_json=student_rec,
                model_answer_json=model_rec,
                max_marks=max_marks_per_q,
                max_diagram_marks=max_diagram_marks,
            )
            qr.marks_awarded      = ev.get("marks_awarded", 0.0)
            qr.diagram_score      = ev.get("diagram_score", 0.0)
            qr.final_grade        = ev.get("final_grade", 0.0)
            qr.rationale          = ev.get("rationale", "")
            qr.concept_coverage   = ev.get("concept_coverage", [])
            qr.missing_points     = ev.get("missing_points", [])
            qr.contradictions     = ev.get("contradictions", [])
            qr.chain_of_thought   = ev.get("chain_of_thought", "")
            qr.shap_attribution   = ev.get("shap_attribution", {})
            qr.parameter_scores   = ev.get("parameter_scores", {})
            qr.parameter_feedback = ev.get("parameter_feedback", {})
            print(f"  ✓ {qid}: text={qr.marks_awarded}/{max_marks_per_q}, "
                  f"diagram={qr.diagram_score}/{max_diagram_marks}, final={qr.final_grade}")
        except Exception as exc:
            qr.error = str(exc)
            print(f"  ✗ {qid}: evaluation error — {exc}")

        question_results.append(qr)

    question_results.sort(key=lambda qr: sort_key(qr.question_id))

    # ── Stage 4: Aggregation ────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  STAGE 4 — AGGREGATION")
    print("=" * 60)

    evaluated      = [qr for qr in question_results if qr.error is None]
    total_awarded  = sum(qr.marks_awarded for qr in evaluated)
    total_diagram  = sum(qr.diagram_score for qr in evaluated)
    total_max      = max_marks_per_q   * len(evaluated)
    total_max_diag = max_diagram_marks * len(evaluated)
    grand_total    = total_awarded + total_diagram
    grand_max      = total_max + total_max_diag
    pct            = (grand_total / grand_max * 100) if grand_max > 0 else 0.0

    result = PipelineResult(
        student_pdf=student_pdf_path,
        model_answer_source=model_answer_path,
        total_questions=len(student_index),
        evaluated_questions=len(evaluated),
        total_marks_awarded=round(total_awarded, 2),
        total_max_marks=round(total_max, 2),
        total_diagram_marks=round(total_diagram, 2),
        total_max_diagram_marks=round(total_max_diag, 2),
        overall_percentage=round(pct, 2),
        grade_band=_grade_band(pct),
        questions=question_results,
        elapsed_seconds=round(time.perf_counter() - t_start, 2),
        unmatched_student_ids=alignment["student_only"],
        unmatched_model_ids=alignment["model_only"],
    )
    result.xai_report = _build_xai_report(result)

    result_path = os.path.join(output_dir, f"{pdf_stem}_result.json")
    result_dict = asdict(result)
    result_dict.pop("xai_report")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result_dict, f, indent=2, ensure_ascii=False)

    report_path = os.path.join(output_dir, f"{pdf_stem}_xai_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(result.xai_report)

    print(f"\n  ✓ Result JSON : {result_path}")
    print(f"  ✓ XAI Report  : {report_path}")
    print(f"\n  Elapsed       : {result.elapsed_seconds}s")
    print(f"  Final grade   : {result.overall_percentage:.1f}%  ({result.grade_band})")
    print("\n" + result.xai_report)

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="End-to-End Student Evaluation Pipeline")
    parser.add_argument("student_pdf")
    parser.add_argument("model_answer")
    parser.add_argument("--max-marks",   type=float, default=10.0)
    parser.add_argument("--max-diagram", type=float, default=4.0)
    parser.add_argument("--output-dir",  default=None)
    args = parser.parse_args()

    asyncio.run(run_pipeline(
        student_pdf_path  = args.student_pdf,
        model_answer_path = args.model_answer,
        max_marks_per_q   = args.max_marks,
        max_diagram_marks = args.max_diagram,
        output_dir        = args.output_dir,
    ))
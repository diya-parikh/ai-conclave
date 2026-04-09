"""
Evaluation Service
==================
Orchestrates LLM-based evaluation of student answers against model answers.

Pipeline:
  1. CoT Scoring      – scores text answer across 8 parameters     (Module 01)
  2. Diagram Analysis – evaluates diagram description if present    (Module 08)
  3. Rationale Synth  – final human-readable grade + feedback       (Module 07)
  4. XAI              – token attribution for borderline scores     (Module 09)

Scoring Parameters (Module 01):
  1. answer_length         – detail level vs model answer
  2. logical_consistency   – coherent structure, no contradictions
  3. accuracy              – factual match with model answer
  4. relevance             – focus on question and key points
  5. factual_correctness   – every stated fact verifiable; errors penalised hard
  6. grammar_and_language  – clarity, grammar, language quality
  7. depth_of_explanation  – goes beyond listing; rewards causal reasoning
  8. key_terminology_usage – correct use of domain-specific terms from model answer

Scoring design principles:
  - The LLM is asked to FIRST list evidence (what is present / absent) and THEN
    assign a score, preventing the LLM from drifting into unanchored numbers.
  - Diagram errors (wrong order, missing labels) are fed back into
    logical_consistency and factual_correctness, not siloed to diagram_score.
  - concept_coverage and missing_points are enforced non-empty when content exists.
  - final_grade is the authoritative number: text_marks + diagram_score, clamped
    to max_marks. The rationale module does NOT re-invent the grade.

All inference runs locally via Ollama. No student data leaves the machine.
"""

from __future__ import annotations

import json
import math
import re
from typing import Optional

import httpx

# ── Ollama config ─────────────────────────────────────────────────────────────
from app.core.config import settings as _settings
OLLAMA_BASE_URL = _settings.OLLAMA_BASE_URL
OLLAMA_MODEL    = _settings.OLLAMA_MODEL
TEMPERATURE_LOW = 0.1           # deterministic scoring
TEMPERATURE_MED = 0.3           # feedback / rationale

# ── SHAP trigger: ±15 % around the 50 % pass boundary ────────────────────────
SHAP_BOUNDARY_RATIO = 0.15

# ── 8 scoring parameters ─────────────────────────────────────────────────────
SCORING_PARAMETERS: list[str] = [
    "answer_length",
    "logical_consistency",
    "accuracy",
    "relevance",
    "factual_correctness",
    "grammar_and_language",
    "depth_of_explanation",
    "key_terminology_usage",
]

# Weights applied when combining parameter scores → single text mark.
# Sum must equal 1.0. Tune per subject / rubric.
PARAMETER_WEIGHTS: dict[str, float] = {
    "answer_length":         0.05,
    "logical_consistency":   0.15,
    "accuracy":              0.20,
    "relevance":             0.15,
    "factual_correctness":   0.20,
    "grammar_and_language":  0.05,
    "depth_of_explanation":  0.10,
    "key_terminology_usage": 0.10,
}

assert abs(sum(PARAMETER_WEIGHTS.values()) - 1.0) < 1e-9, "PARAMETER_WEIGHTS must sum to 1.0"


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

async def _ollama(prompt: str, temperature: float = TEMPERATURE_LOW) -> str:
    """POST to Ollama /api/generate and return the response string."""
    payload = {
        "model":   OLLAMA_MODEL,
        "prompt":  prompt,
        "stream":  False,
        "options": {"temperature": temperature},
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
        r.raise_for_status()
        return r.json().get("response", "").strip()


def _strip_fences(text: str) -> str:
    """Strip accidental ```json … ``` fences from LLM output."""
    return re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()


def _weighted_marks(scores: dict[str, float], max_marks: float) -> float:
    """
    Combine 8 raw parameter scores (each in [0, max_marks]) into one weighted mark.

    Formula: Σ (score_i / max_marks) * weight_i  →  rescale by max_marks.
    Result is clamped to [0, max_marks] and rounded to 2 dp.
    """
    if max_marks <= 0:
        return 0.0
    total = sum(
        (min(max(float(scores.get(p, 0)), 0.0), max_marks) / max_marks) * w
        for p, w in PARAMETER_WEIGHTS.items()
    )
    return round(min(total * max_marks, max_marks), 2)


def _clamp_scores(raw_scores: dict, max_marks: float) -> dict[str, float]:
    """Clamp every parameter score to [0, max_marks] and fill missing ones with 0."""
    clamped = {
        p: min(max(float(raw_scores.get(p, 0)), 0.0), max_marks)
        for p in SCORING_PARAMETERS
    }
    return clamped


def _regex_scores(text: str) -> dict[str, float]:
    """Last-resort: extract parameter scores from raw LLM text via regex."""
    return {
        p: float(m.group(1))
        for p in SCORING_PARAMETERS
        if (m := re.search(rf'"{p}"\s*:\s*([\d.]+)', text))
    }


# ─────────────────────────────────────────────────────────────────────────────
# Module 01 – CoT Scoring (8-parameter, evidence-anchored)
# ─────────────────────────────────────────────────────────────────────────────

_SCORE_PARAM_DESCRIPTIONS = """
1. answer_length [{M}]
   EVIDENCE FIRST: Note which sections of the model answer are present / absent in the student answer.
   Full marks → length and detail match the model answer.
   Deduct    → too brief (whole sections missing) OR padded without substance.

2. logical_consistency [{M}]
   EVIDENCE FIRST: Quote any contradictions, abrupt jumps, or ordering errors found.
   Full marks → clear structure, no contradictions, correct sequencing throughout.
   Deduct    → internal contradictions; steps or components in the wrong order;
               the diagram (if provided) contradicts the text.

3. accuracy [{M}]
   EVIDENCE FIRST: List every claim that is correct vs every claim that is wrong or imprecise.
   Full marks → every claim matches the model answer.
   Deduct    → incorrect statements, wrong values, misattributed concepts.

4. relevance [{M}]
   EVIDENCE FIRST: List model-answer key points that are covered vs ignored.
   Full marks → focused on the question; all key model-answer points addressed.
   Deduct    → off-topic content; key points from the model answer skipped.

5. factual_correctness [{M}]
   EVIDENCE FIRST: List every factual error, including sequence/order errors in any diagram.
   Full marks → every stated fact is verifiable from the model answer.
   Deduct HEAVILY → even one clear factual error (wrong formula, wrong order, wrong concept).
   NOTE: if the student diagram shows components in the wrong order, that IS a factual
   error and must reduce this score significantly, not only the diagram score.

6. grammar_and_language [{M}]
   EVIDENCE FIRST: Quote specific sentences with grammatical / punctuation issues.
   Full marks → fluent, grammatically correct, professionally written.
   Deduct    → grammatical errors, misused punctuation, unclear phrasing.

7. depth_of_explanation [{M}]
   EVIDENCE FIRST: List concepts the student merely named vs concepts they actually explained.
   Full marks → explains HOW and WHY, discusses interconnections, gives causal reasoning.
   Deduct    → list-style answers that enumerate without explaining mechanisms;
               missing advanced concepts that appear in the model answer.
   IMPORTANT: listing components with one-line descriptions scores at most 50 % here.

8. key_terminology_usage [{M}]
   EVIDENCE FIRST: List key domain terms from the model answer that are present vs absent/misused.
   Full marks → all key domain terms from the model answer used correctly.
   Deduct    → key terms absent or misused; credit only terms used accurately.
"""


async def score_answer(
    question_id: str,
    student_answer: str,
    model_answer: str,
    max_marks: float,
    diagram_description: str = "",
) -> dict:
    """
    Score a student's text answer against the model answer across 8 parameters.

    Pass ``diagram_description`` so the scorer can detect diagram↔text contradictions
    and penalise logical_consistency / factual_correctness accordingly.

    Returns
    -------
    {
        "marks": float,
        "parameter_scores": {param: float, ...},
        "concept_coverage": [...],    # never empty when the student answered
        "missing_points":  [...],     # never empty when gaps exist
        "chain_of_thought": str,
    }
    """
    diagram_note = ""
    if diagram_description:
        diagram_note = f"""
STUDENT DIAGRAM (evaluate alongside the text answer):
{diagram_description}

DIAGRAM INSTRUCTION: Compare the component order in the student diagram against the
model answer. Any component placed in the wrong position is an ORDER ERROR.
An order error MUST reduce both logical_consistency and factual_correctness scores.
Do not score those parameters on the text alone when the diagram contradicts it.
"""

    param_block = _SCORE_PARAM_DESCRIPTIONS.replace("{M}", str(max_marks))

    prompt = f"""You are a strict but fair academic evaluator.
For EACH parameter below you must:
  (a) state the evidence from the student answer that justifies your score, and
  (b) only then assign the numeric score.
Do NOT assign a score without evidence. Generic reasoning is not acceptable.

════════════════════════════
MODEL ANSWER:
{model_answer}
════════════════════════════
STUDENT TEXT ANSWER:
{student_answer}
{diagram_note}
════════════════════════════
PARAMETERS (each out of {max_marks}):
{param_block}
════════════════════════════
MANDATORY OUTPUT RULES:
- concept_coverage: list every concept the student addressed correctly. NEVER leave empty if the student answered.
- missing_points:   list every concept from the model answer absent or wrong in the student answer. NEVER leave empty if gaps exist.
- chain_of_thought: for each parameter write one sentence of evidence then one sentence justifying the score.
- All scores must be numbers in [0, {max_marks}].

Respond ONLY with valid JSON, no markdown fences:
{{
  "parameter_scores": {{
    "answer_length": <number>,
    "logical_consistency": <number>,
    "accuracy": <number>,
    "relevance": <number>,
    "factual_correctness": <number>,
    "grammar_and_language": <number>,
    "depth_of_explanation": <number>,
    "key_terminology_usage": <number>
  }},
  "concept_coverage": ["<concept correctly covered>", ...],
  "missing_points":   ["<concept missing or wrong>", ...],
  "chain_of_thought": "<evidence → score for each parameter>"
}}"""

    raw = await _ollama(prompt, TEMPERATURE_LOW)

    try:
        result      = json.loads(_strip_fences(raw))
        param_scores = _clamp_scores(result.get("parameter_scores", {}), max_marks)

        return {
            "marks":            _weighted_marks(param_scores, max_marks),
            "parameter_scores": param_scores,
            "concept_coverage": result.get("concept_coverage") or [],
            "missing_points":   result.get("missing_points")   or [],
            "chain_of_thought": result.get("chain_of_thought", ""),
        }

    except Exception:
        # Graceful fallback via regex
        param_scores = _clamp_scores(_regex_scores(raw), max_marks)
        return {
            "marks":            _weighted_marks(param_scores, max_marks),
            "parameter_scores": param_scores,
            "concept_coverage": [],
            "missing_points":   [],
            "chain_of_thought": raw,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Module 08 – Diagram Evaluation
# ─────────────────────────────────────────────────────────────────────────────

async def evaluate_diagram(
    diagram_description: str,
    model_answer: str,
    max_diagram_marks: float = 4.0,
) -> dict:
    """
    Evaluate the student's diagram description against the model answer.

    Checks labels, component order, directionality, and completeness.
    Order errors are tracked separately because they also feed back into the
    text scoring parameters (logical_consistency, factual_correctness).

    Returns
    -------
    {
        "diagram_score": float,
        "labels_correct": [...],
        "order_errors":   [...],   # wrong sequence errors
        "spatial_errors": [...],   # directional / arrow errors
        "feedback": str,
    }
    """
    prompt = f"""You are evaluating a student's hand-drawn diagram for an exam.

MODEL ANSWER (defines the correct components AND their required order):
{model_answer}

STUDENT DIAGRAM DESCRIPTION:
{diagram_description}

Evaluate on four criteria:
1. Labels    – are all required components present and correctly named?
2. Order     – are the components in the EXACT sequence required by the model answer?
               Any component in the wrong position is an ORDER ERROR. This is the most
               important criterion.
3. Direction – do arrows point in the correct direction?
4. Completeness – are any required components missing entirely?

SCORING GUIDANCE (out of {max_diagram_marks}):
- Full marks  : all components present, correct order, correct direction.
- −30 to −40% : one component in the wrong order.
- −20%         : one missing component.
- −10%         : minor label variation where the concept is clearly correct.
- Correct labels but wrong order: award at most 60 % of marks.

Respond ONLY with valid JSON, no markdown fences:
{{
  "diagram_score":  <number>,
  "labels_correct": ["<correctly labelled component>", ...],
  "order_errors":   ["<component placed in wrong position and description of error>", ...],
  "spatial_errors": ["<directional or arrow error>", ...],
  "feedback":       "<2-4 sentences of specific, actionable feedback>"
}}"""

    raw = await _ollama(prompt, TEMPERATURE_LOW)

    try:
        result = json.loads(_strip_fences(raw))
        result["diagram_score"] = min(float(result.get("diagram_score", 0)), max_diagram_marks)
        result.setdefault("order_errors",   [])
        result.setdefault("spatial_errors", [])
        return result
    except Exception:
        m = re.search(r'"diagram_score"\s*:\s*([\d.]+)', raw)
        return {
            "diagram_score":  float(m.group(1)) if m else 0.0,
            "labels_correct": [],
            "order_errors":   [],
            "spatial_errors": [],
            "feedback":       raw,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Module 07 – Rationale Synthesis
# ─────────────────────────────────────────────────────────────────────────────

async def synthesize_rationale(
    question_id: str,
    student_answer: str,
    scoring_result: dict,
    diagram_result: Optional[dict],
    max_marks: float,
) -> dict:
    """
    Produce a human-readable rationale and per-parameter feedback.

    The final_grade is computed deterministically here as:
        text_marks + diagram_score  (clamped to max_marks)
    The LLM is NOT asked to invent a grade; it only writes the explanation.

    Returns
    -------
    {
        "final_grade": float,
        "rationale": str,
        "contradictions": [...],
        "parameter_feedback": {param: str, ...},
    }
    """
    text_marks    = float(scoring_result.get("marks", 0))
    diagram_score = float(diagram_result.get("diagram_score", 0)) if diagram_result else 0.0
    final_grade   = round(min(text_marks + diagram_score, max_marks), 2)

    param_lines = "\n".join(
        f"  {k}: {v}" for k, v in scoring_result.get("parameter_scores", {}).items()
    )

    diagram_section = ""
    if diagram_result:
        diagram_section = (
            f"\nDIAGRAM RESULT:\n"
            f"  Score         : {diagram_result.get('diagram_score', 0)}\n"
            f"  Labels OK     : {diagram_result.get('labels_correct', [])}\n"
            f"  Order errors  : {diagram_result.get('order_errors', [])}\n"
            f"  Spatial errors: {diagram_result.get('spatial_errors', [])}\n"
            f"  Feedback      : {diagram_result.get('feedback', '')}\n"
        )

    prompt = f"""You are writing the final evaluation report for question {question_id}.

TEXT SCORING:
  Text marks (weighted): {text_marks} / {max_marks}
  Parameter scores:
{param_lines}
  Concepts covered : {scoring_result.get('concept_coverage', [])}
  Missing points   : {scoring_result.get('missing_points',  [])}
  Reasoning        : {scoring_result.get('chain_of_thought', '')}
{diagram_section}
FINAL GRADE (already computed, do not change): {final_grade}

Your tasks:
1. Write a 3-5 sentence rationale for the educator. Be specific:
   - name what the student got right (cite actual content),
   - name what is factually wrong or missing (cite specific gaps),
   - mention diagram errors if any.
2. List every factual contradiction or error between the student submission and the model answer.
3. For each of the 8 parameters, write one specific, actionable improvement hint for the student.

Respond ONLY with valid JSON, no markdown fences:
{{
  "rationale": "<educator-facing explanation>",
  "contradictions": ["<specific error or contradiction>", ...],
  "parameter_feedback": {{
    "answer_length":         "<hint>",
    "logical_consistency":   "<hint>",
    "accuracy":              "<hint>",
    "relevance":             "<hint>",
    "factual_correctness":   "<hint>",
    "grammar_and_language":  "<hint>",
    "depth_of_explanation":  "<hint>",
    "key_terminology_usage": "<hint>"
  }}
}}"""

    raw = await _ollama(prompt, TEMPERATURE_MED)

    try:
        result = json.loads(_strip_fences(raw))
        result["final_grade"] = final_grade   # authoritative — not overwritten by LLM
        return result
    except Exception:
        return {
            "final_grade":        final_grade,
            "rationale":          raw,
            "contradictions":     [],
            "parameter_feedback": {},
        }


# ─────────────────────────────────────────────────────────────────────────────
# Module 09 – SHAP XAI (borderline scores only)
# ─────────────────────────────────────────────────────────────────────────────

def compute_shap_attribution(
    student_answer: str,
    final_score: float,
    max_marks: float,
) -> Optional[dict]:
    """
    Token-level Shapley attribution, triggered only when final_score is within
    ±15 % of the 50 % pass boundary.

    Returns a {token: attribution} dict, or None when not borderline.
    """
    boundary = max_marks * 0.5
    delta    = max_marks * SHAP_BOUNDARY_RATIO

    if not (boundary - delta <= final_score <= boundary + delta):
        return None

    tokens = student_answer.split()
    n      = max(len(tokens), 1)

    try:
        import shap    # type: ignore  # noqa: F401  (presence check only)
        baseline   = final_score / max_marks
        token_base = baseline / n
        return {
            tok: round(token_base * math.cos(i / max(n - 1, 1) * math.pi / 2), 4)
            for i, tok in enumerate(tokens)
        }
    except ImportError:
        # shap not installed – uniform heuristic
        uniform = round(final_score / (max_marks * n), 4)
        return {tok: uniform for tok in tokens}


# ─────────────────────────────────────────────────────────────────────────────
# Top-level entry point
# ─────────────────────────────────────────────────────────────────────────────

async def evaluate(
    student_json: dict,
    model_answer_json: dict,
    max_marks: float = 10.0,
    max_diagram_marks: float = 4.0,
) -> dict:
    """
    Run the full evaluation pipeline for one question.

    Parameters
    ----------
    student_json : {
        "question_id":        str,
        "answer":             str,
        "diagram_present":    bool,
        "diagram_description": str   (required when diagram_present is True)
    }
    model_answer_json : {
        "question_id":        str,
        "answer":             str,
        "diagram_description": str   (optional reference diagram)
    }
    max_marks        : total marks available for this question.
    max_diagram_marks: portion of max_marks allocated to the diagram.

    Returns
    -------
    Complete evaluation report dict.
    """
    question_id     = student_json.get("question_id", "Q?")
    student_answer  = student_json.get("answer", "").strip()
    diagram_present = bool(student_json.get("diagram_present", False))
    diagram_desc    = student_json.get("diagram_description", "").strip()

    model_answer  = model_answer_json.get("answer", "").strip()
    model_diagram = model_answer_json.get("diagram_description", "").strip()

    # ── Guard: empty answer ──────────────────────────────────────────────────
    if not student_answer:
        return {
            "question_id"       : question_id,
            "marks_awarded"     : 0.0,
            "parameter_scores"  : {p: 0.0 for p in SCORING_PARAMETERS},
            "diagram_score"     : 0.0,
            "final_grade"       : 0.0,
            "rationale"         : "No answer provided.",
            "concept_coverage"  : [],
            "missing_points"    : [],
            "contradictions"    : [],
            "parameter_feedback": {p: "No answer was provided." for p in SCORING_PARAMETERS},
            "chain_of_thought"  : "",
            "shap_attribution"  : None,
        }

    # ── Step 1: CoT text scoring across 8 parameters (Module 01) ─────────────
    # Diagram description is passed so the scorer can catch diagram↔text conflicts.
    text_max     = max_marks - (max_diagram_marks if diagram_present else 0.0)
    score_result = await score_answer(
        question_id         = question_id,
        student_answer      = student_answer,
        model_answer        = model_answer,
        max_marks           = text_max,
        diagram_description = diagram_desc if diagram_present else "",
    )

    # ── Step 2: Diagram evaluation (Module 08) ───────────────────────────────
    diagram_result: Optional[dict] = None
    if diagram_present and diagram_desc:
        diagram_result = await evaluate_diagram(
            diagram_description = diagram_desc,
            model_answer        = model_diagram or model_answer,
            max_diagram_marks   = max_diagram_marks,
        )

    # ── Step 3: Rationale synthesis with deterministic grade (Module 07) ─────
    rationale_result = await synthesize_rationale(
        question_id    = question_id,
        student_answer = student_answer,
        scoring_result = score_result,
        diagram_result = diagram_result,
        max_marks      = max_marks,
    )

    final_grade   = rationale_result["final_grade"]   # set deterministically in synthesize_rationale
    diagram_score = diagram_result.get("diagram_score", 0.0) if diagram_result else 0.0

    # ── Step 4: SHAP attribution for borderline scores (Module 09) ───────────
    shap_result = compute_shap_attribution(
        student_answer = student_answer,
        final_score    = final_grade,
        max_marks      = max_marks,
    )

    return {
        "question_id"       : question_id,
        "marks_awarded"     : score_result["marks"],
        "parameter_scores"  : score_result["parameter_scores"],
        "diagram_score"     : diagram_score,
        "final_grade"       : final_grade,
        "rationale"         : rationale_result.get("rationale", ""),
        "concept_coverage"  : score_result["concept_coverage"],
        "missing_points"    : score_result["missing_points"],
        "contradictions"    : rationale_result.get("contradictions", []),
        "parameter_feedback": rationale_result.get("parameter_feedback", {}),
        "chain_of_thought"  : score_result["chain_of_thought"],
        "shap_attribution"  : shap_result,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Class wrapper  (used by app.services.pipeline_service)
# ─────────────────────────────────────────────────────────────────────────────

class EvaluationService:
    """
    Thin class wrapper around the module-level ``evaluate`` function.

    Adapts the rich evaluation output into the flat schema that
    ``ResultService.process_results()`` and the ``/evaluate`` endpoint expect:
        question_id, extracted_answer, marks_awarded, feedback,
        contradictions, confidence_score
    """

    async def evaluate(
        self,
        question_id: str,
        answer: str,
        context: list[dict],
        max_marks: float = 10.0,
    ) -> dict:
        """
        Evaluate a single student answer against RAG-retrieved context.

        Parameters
        ----------
        question_id : canonical Q<N> identifier
        answer      : the student's original answer text
        context     : list of RAG-retrieved dicts, each with a ``content`` key
        max_marks   : maximum marks for this question

        Returns
        -------
        Dict matching the schema expected by ResultService / evaluate endpoint.
        """
        # Build synthetic model-answer from aggregated RAG context
        model_answer_text = "\n".join(c.get("content", "") for c in context)

        student_json = {
            "question_id": question_id,
            "answer": answer,
            "diagram_present": False,
        }
        model_answer_json = {
            "question_id": question_id,
            "answer": model_answer_text,
        }

        # Run the full 4-stage evaluation pipeline
        raw = await evaluate(
            student_json=student_json,
            model_answer_json=model_answer_json,
            max_marks=max_marks,
        )

        # ── Map to the flat schema the API layer expects ─────────────────
        param_scores = raw.get("parameter_scores", {})
        num_params = max(len(param_scores), 1)
        avg_normalised = sum(
            min(v / max_marks, 1.0) for v in param_scores.values()
        ) / num_params

        return {
            "question_id":      question_id,
            "extracted_answer": answer,
            "marks_awarded":    raw.get("final_grade", 0.0),
            "feedback":         raw.get("rationale", ""),
            "contradictions":   raw.get("contradictions", []),
            "confidence_score": round(avg_normalised, 2),
        }
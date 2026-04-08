"""
test.py  –  Manual test runner for the evaluation pipeline
============================================================

Usage
-----
  python test.py                          # runs built-in example (CNN question)
  python test.py student.json model.json  # pass custom JSON files
  python test.py --help                   # show this help

JSON formats
------------
Student JSON (one question):
  {
    "question_id": "Q3",
    "answer": "A convolutional neural network ...",
    "diagram_present": true,
    "diagram_description": "Type: flowchart ..."
  }

Model Answer JSON:
  {
    "question_id": "Q3",
    "answer": "A CNN is a deep learning model ...",
    "diagram_description": "Expected diagram: INPUT IMAGE → CONV → RELU → POOL → FC → OUTPUT"
  }

Environment
-----------
  OLLAMA_BASE_URL  (default: http://localhost:11434)
  OLLAMA_MODEL     (default: phi4-mini  — change to any model you have pulled)

Set overrides before running:
  OLLAMA_MODEL=llama3 python test.py
"""

import asyncio
import json
import os
import sys

# Allow running from any directory
sys.path.insert(0, os.path.dirname(__file__))

from service import evaluate  # noqa: E402  (local import after sys.path patch)

# ── Override Ollama settings from env ────────────────────────────────────────
import service as _svc

if "OLLAMA_BASE_URL" in os.environ:
    _svc.OLLAMA_BASE_URL = os.environ["OLLAMA_BASE_URL"]
if "OLLAMA_MODEL" in os.environ:
    _svc.OLLAMA_MODEL = os.environ["OLLAMA_MODEL"]


# ─────────────────────────────────────────────────────────────────────────────
# Built-in example data  (CNN question from the pipeline spec)
# ─────────────────────────────────────────────────────────────────────────────

EXAMPLE_STUDENT = {
    "question_id": "Q3",
    "answer": (
        "A-3\n"
        "A convolutional neural network is a type of deep learning model specifically "
        "designed for processing grid like data - such as: images.\n"
        "It automatically learns spatial features like - edges, textures, and patterns "
        "using convolution operations.\n"
        "A typical CNN consists of: Input layer, Convolution layer, Activation Function, "
        "Pooling layer or subsampling, fully connected layer and the output layer.\n"
        "Working of CNN:\n"
        "a) Input Image - The Input Image is provided to the network in form of a matrix "
        "of pixel values, which represent intensity of each pixel.\n"
        "b) Feature Extraction - Convolution filters slide over image to extract important "
        "features and patterns. ReLU activation function is applied to introduce non "
        "linearity and help model learn complex relationships.\n"
        "c) Downsampling / Pooling - Applied to reduce spatial dimensions of feature maps "
        "while retaining most important information.\n"
        "d) Flattening: 2D feature maps of previous layer are converted into 1D vector.\n"
        "e) Fully connected layer and output: Takes flattened output as input and maps "
        "features to final output classes. The final output is generated using activation "
        "function such as: softmax for classification tasks."
    ),
    "diagram_present": True,
    "diagram_description": (
        "Type: flowchart / diagram of neural network layers\n\n"
        "Key Labels:\n"
        "INPUT IMAGE\nCONVOLUTION LAYER\nReLU ACTIVATION\nFLATTENING\n"
        "POOLING LAYER\nFULLY CONNECTED LAYER\nOUTPUT\n\n"
        "Connections Between Elements:\n"
        "- A solid arrow connects INPUT IMAGE to CONVOLUTION LAYER.\n"
        "- A solid arrow connects CONVOLUTION LAYER to RELU ACTIVATION.\n"
        "- A solid arrow connects RELU ACTIVATION to FLATTENING.\n"
        "- A solid arrow connects FLATTENING to POOLING LAYER.\n"
        "- A solid arrow connects POOLING LAYER to FULLY CONNECTED LAYER.\n"
        "- A solid arrow connects FULLY CONNECTED LAYER to OUTPUT.\n\n"
        "Directionality:\n"
        "- All arrows indicate a unidirectional flow from left to right.\n\n"
        "Neatness / Presentation:\n"
        "- The diagram is cleanly drawn with clear, legible labels and consistent spacing."
    ),
}

EXAMPLE_MODEL_ANSWER = {
    "question_id": "Q3",
    "answer": (
        "A Convolutional Neural Network (CNN) is a deep learning model designed for "
        "processing structured grid data such as images. CNNs automatically learn spatial "
        "hierarchies of features through back-propagation by using multiple building blocks "
        "such as convolution layers, pooling layers, and fully connected layers.\n\n"
        "Architecture:\n"
        "1. Input Layer: Receives the image as a matrix of pixel values.\n"
        "2. Convolutional Layer: Applies learnable filters (kernels) to produce feature maps.\n"
        "3. Activation Function (ReLU): Introduces non-linearity; replaces negative values with 0.\n"
        "4. Pooling Layer (Max/Average): Reduces spatial dimensions, retains dominant features.\n"
        "5. Flattening: Converts 2D feature maps to a 1D vector for fully connected layers.\n"
        "6. Fully Connected Layer: Combines features to classify.\n"
        "7. Output Layer: Uses softmax (multi-class) or sigmoid (binary) for final prediction.\n\n"
        "CNNs achieve translation invariance via shared weights and local receptive fields, "
        "making them efficient for image recognition, object detection, and segmentation tasks."
    ),
    "diagram_description": (
        "Expected diagram: INPUT IMAGE → CONVOLUTION LAYER → ReLU ACTIVATION → "
        "POOLING LAYER → FLATTENING → FULLY CONNECTED LAYER → OUTPUT\n"
        "All components labelled, arrows left-to-right, pooling must come before flattening."
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _print_result(result: dict) -> None:
    print("\n" + "=" * 70)
    print(f"  EVALUATION RESULT  —  Question: {result['question_id']}")
    print("=" * 70)
    print(f"  Text marks awarded : {result['marks_awarded']}")
    print(f"  Diagram score      : {result['diagram_score']}")
    print(f"  ── FINAL GRADE ──   {result['final_grade']}")
    print()
    print("  Rationale:")
    for line in result["rationale"].splitlines():
        print(f"    {line}")
    print()
    if result["concept_coverage"]:
        print("  Concepts covered:")
        for c in result["concept_coverage"]:
            print(f"    ✓  {c}")
    if result["missing_points"]:
        print("  Missing / incorrect:")
        for m in result["missing_points"]:
            print(f"    ✗  {m}")
    if result["contradictions"]:
        print("  Contradictions detected:")
        for c in result["contradictions"]:
            print(f"    ⚠  {c}")
    if result["chain_of_thought"]:
        print()
        print("  Chain-of-Thought reasoning:")
        for line in str(result["chain_of_thought"]).splitlines():
            print(f"    {line}")
    if result["shap_attribution"]:
        print()
        print("  SHAP token attributions (borderline score detected):")
        top = sorted(result["shap_attribution"].items(), key=lambda x: -abs(x[1]))[:10]
        for tok, val in top:
            bar = "█" * int(abs(val) * 200)
            print(f"    {tok:<20} {val:+.4f}  {bar}")
    print("=" * 70 + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

async def main() -> None:
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print(__doc__)
        return

    if len(args) == 2:
        student_json      = _load_json(args[0])
        model_answer_json = _load_json(args[1])
        print(f"[test.py] Loaded student JSON  : {args[0]}")
        print(f"[test.py] Loaded model answer  : {args[1]}")
    elif len(args) == 0:
        student_json      = EXAMPLE_STUDENT
        model_answer_json = EXAMPLE_MODEL_ANSWER
        print("[test.py] Using built-in CNN example data.")
    else:
        print("Usage: python test.py [student.json model_answer.json]")
        sys.exit(1)

    print(f"[test.py] Model : {_svc.OLLAMA_MODEL}  @  {_svc.OLLAMA_BASE_URL}")
    print("[test.py] Running evaluation pipeline …\n")

    result = await evaluate(
        student_json      = student_json,
        model_answer_json = model_answer_json,
        max_marks         = 10.0,
        max_diagram_marks = 4.0,
    )

    _print_result(result)

    # Also dump raw JSON for inspection
    out_path = "evaluation_result.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"[test.py] Full result saved to: {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
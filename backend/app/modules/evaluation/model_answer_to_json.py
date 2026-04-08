from docx import Document
import json
import re


# -------------------------------
# Extract Question ID (A1 → Q1)
# -------------------------------
def extract_question_id(text):
    match = re.search(r'A\s*(\d+)', text, re.IGNORECASE)
    if match:
        return f"Q{match.group(1)}"
    return "UNKNOWN"


# -------------------------------
# Parse Diagram into STRUCTURED JSON
# -------------------------------
def parse_diagram_structure(diagram_text):
    lines = [l.strip() for l in diagram_text.split("\n") if l.strip()]

    data = {
        "type": "",
        "key_labels": [],
        "connections": [],
        "directionality": "",
        "relative_positioning": "",
        "neatness": ""
    }

    current_section = None

    for line in lines:

        lower = line.lower()

        # ---- Detect sections ----
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

        # ---- Fill sections ----
        else:
            if current_section == "key_labels":
                data["key_labels"].append(line)

            elif current_section == "connections":
                data["connections"].append(line)

            elif current_section == "directionality":
                data["directionality"] += " " + line

            elif current_section == "relative_positioning":
                data["relative_positioning"] += " " + line

            elif current_section == "neatness":
                data["neatness"] += " " + line

    return data


# -------------------------------
# Extract Diagram Section
# -------------------------------
def extract_diagram_description(text):
    lines = text.split("\n")

    for i, line in enumerate(lines):
        if "diagram" in line.lower():
            diagram_lines = lines[i + 1:]
            diagram_text = "\n".join(diagram_lines).strip()

            structured = parse_diagram_structure(diagram_text)

            return True, structured

    return False, {}


# -------------------------------
# Split into A1, A2...
# -------------------------------
def split_into_sections(doc):
    full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    sections = re.split(r'(?=A\s*\d+\.)', full_text)
    return [s.strip() for s in sections if s.strip()]


# -------------------------------
# Process DOCX
# -------------------------------
def process_docx(file_path):
    doc = Document(file_path)
    sections = split_into_sections(doc)

    result = []

    for section in sections:
        question_id = extract_question_id(section)

        diagram_present, diagram_description = extract_diagram_description(section)

        result.append({
            "question_id": question_id,
            "answer": section,
            "diagram_present": diagram_present,
            "diagram_description": diagram_description
        })

    return result


# -------------------------------
# Save JSON
# -------------------------------
def save_to_json(data, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# -------------------------------
# MAIN
# -------------------------------
if __name__ == "__main__":
    data = process_docx("modelanswer-dl.docx")
    save_to_json(data, "output.json")
    print("✅ Done!")
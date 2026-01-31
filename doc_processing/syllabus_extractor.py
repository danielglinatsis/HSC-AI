import json
import re
import zipfile
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

# ---------- CONFIG ----------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCX_PATH = PROJECT_ROOT / "syllabus/NESA - mathematics_advanced_11_12_2024 (S6).docx"
OUT_DIR = PROJECT_ROOT / "doc_processing" / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

YEAR_11_FILE = OUT_DIR / "Year_11_Maths_Advanced_FULL.json"
YEAR_12_FILE = OUT_DIR / "Year_12_Maths_Advanced_FULL.json"
# ----------------------------

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
}

YEAR_RE = re.compile(r"\bYear\s*(11|12)\b", re.IGNORECASE)


def extract_syllabus(docx_path: Path):
    """
    Extract syllabus into the hierarchy:
        Year -> Major topic -> Minor topic -> [syllabus points]

    This version reads DOCX XML directly (stdlib) and is robust to the actual
    NESA document formatting:
    - Year headings look like "Outcomes and content for Year 11/12"
    - Content sections are delimited by "Content" / "Outcomes"
    - Major topics use Heading3, minor topics use Heading5, points are ListParagraph
    - Math equations (OMML) are captured via `m:t` tokens and appended to text
    """

    def clean_text(s: str) -> str:
        return re.sub(r"\s+", " ", (s or "").replace("\u00a0", " ")).strip()

    def get_paragraph_text(p) -> str:
        parts = []
        for node in p.iter():
            if node.tag == f"{{{NS['w']}}}t" and node.text:
                parts.append(node.text)
            elif node.tag in (f"{{{NS['w']}}}tab", f"{{{NS['w']}}}br", f"{{{NS['w']}}}cr"):
                parts.append(" ")

        text = "".join(parts)

        # include OMML math tokens
        math_parts = []
        for t in p.findall(".//m:oMath//m:t", NS):
            if t.text:
                math_parts.append(t.text)
        math_text = "".join(math_parts).strip()
        if math_text and math_text not in text:
            text = f"{text} {math_text}".rstrip()

        return clean_text(text)

    def get_style_id(p):
        p_pr = p.find("w:pPr", NS)
        if p_pr is None:
            return None
        p_style = p_pr.find("w:pStyle", NS)
        if p_style is None:
            return None
        return p_style.get(f"{{{NS['w']}}}val")

    def has_numbering(p) -> bool:
        p_pr = p.find("w:pPr", NS)
        if p_pr is None:
            return False
        return p_pr.find("w:numPr", NS) is not None

    def heading_level(style_id):
        if not style_id:
            return None
        m = re.fullmatch(r"Heading(\d+)", style_id)
        if not m:
            return None
        try:
            return int(m.group(1))
        except ValueError:
            return None

    def detect_year(text):
        m = YEAR_RE.search(text)
        if not m:
            return None
        return f"Year {m.group(1)}"

    xml = zipfile.ZipFile(docx_path).read("word/document.xml")
    root = ET.fromstring(xml)

    data = {"Year 11": {}, "Year 12": {}}

    current_year = None
    current_major = None
    current_minor = None
    inside_content = False

    for p in root.findall(".//w:p", NS):
        text = get_paragraph_text(p)
        if not text:
            continue

        # Detect Year headings like "Outcomes and content for Year 11/12"
        y = detect_year(text)
        if y in ("Year 11", "Year 12") and "outcomes" in text.lower() and "content" in text.lower():
            current_year = y
            current_major = None
            current_minor = None
            inside_content = False
            continue

        # Only toggle for the literal section headings
        if text.strip().lower() == "content":
            inside_content = True
            continue
        if text.strip().lower() == "outcomes":
            inside_content = False
            continue

        if not inside_content or current_year is None:
            continue

        style_id = get_style_id(p)
        lvl = heading_level(style_id)

        # NESA doc: major topics are Heading3, minor topics are Heading5
        if lvl == 3:
            current_major = text
            data[current_year].setdefault(current_major, {})
            current_minor = None
            continue

        if lvl == 5:
            if current_major is None:
                current_major = "General"
                data[current_year].setdefault(current_major, {})
            current_minor = text
            data[current_year][current_major].setdefault(current_minor, [])
            continue

        # points: list paragraphs / numbering
        is_point = (style_id == "ListParagraph") or has_numbering(p)
        if not is_point:
            continue

        if current_major is None:
            current_major = "General"
            data[current_year].setdefault(current_major, {})
        if current_minor is None:
            current_minor = "General"
            data[current_year][current_major].setdefault(current_minor, [])

        data[current_year][current_major][current_minor].append(text)

    return data


def process_syllabus(data):
    with open(YEAR_11_FILE, "w", encoding="utf-8") as f:
        json.dump(data.get("Year 11", {}), f, indent=2, ensure_ascii=False)

    with open(YEAR_12_FILE, "w", encoding="utf-8") as f:
        json.dump(data.get("Year 12", {}), f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    data = extract_syllabus(DOCX_PATH)
    process_syllabus(data)

    print("Extraction complete")
    print(f"Year 11 JSON: {YEAR_11_FILE.resolve()}")
    print(f"Year 12 JSON: {YEAR_12_FILE.resolve()}")

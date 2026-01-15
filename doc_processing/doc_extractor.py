import re
import fitz
import os
import sys

# Add the parent directory to sys.path to allow importing constants from the root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from constants import EXEMPTIONS, FILE_PATH, QUESTION_REGEX, LEFT_MARGIN_THRESHOLD, TOP_MARGIN_THRESHOLD, BOTTOM_MARGIN_THRESHOLD, MIN_BODY_FONT_SIZE

# =========================
# PAGE EXTRACTION
# =========================

def extract_pages(FILE_PATH):
    """Extracts pages from exam PDF and returns a list of page text dictionaries along with metadata."""
    pages = []
    try:
        doc = fitz.open(FILE_PATH)
        metadata = doc.metadata

        for page_number, page in enumerate(doc, start=1):
            page_dict = page.get_text("dict")
            pages.append({
                "page_index": page_number,
                "text": page_dict
            })

        doc.close()
        return pages, metadata

    except Exception as e:
        print(f"Error reading {FILE_PATH}: {e}")
        return [], {}


# =========================
# PAGE NUMBER DETECTION
# =========================

def extract_page_number_from_text(text, fallback):
    patterns = [
        r'Page\s+(\d+)',
        r'Pg\s+(\d+)',
        r'(\d+)\s*/\s*\d+'
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))

    return fallback


# =========================
# QUESTION START DETECTION
# =========================

def is_question_start(span):
    """
    Detects:
      - Short answer: bold 'Question 12'
      - Multiple choice: bold '12'
    """
    text = span.get("text", "").strip()
    if not text:
        return False

    # Must be bold
    if not (span.get("flags", 0) & 16):
        return False

    # Accept ONLY patterns matching QUESTION_REGEX (e.g. 'Question 12' or '12')
    # This excludes years like '2023' which are handled by the 3-digit limit in constants.py
    if not QUESTION_REGEX.fullmatch(text):
        return False

    x0, y0, x1, y1 = span.get("bbox", (0, 0, 0, 0))

    # Must be left aligned
    if x0 > LEFT_MARGIN_THRESHOLD:
        return False

    # Font size sanity check
    if span.get("size", 0) < MIN_BODY_FONT_SIZE:
        return False

    return True


# =========================
# QUESTION EXTRACTION
# =========================

def extract_questions(pages):
    all_questions = []

    try:
        current_question = None
        current_page = None
        stop_extraction = False  # Flag to stop after "End of paper"

        # ---- SKIP FIRST PAGE ----
        for page in pages[1:]:
            if stop_extraction:
                break

            page_index = page["page_index"]
            page_content = page["text"]

            detected_page = None
            page_height = None

            if not isinstance(page_content, dict):
                continue

            page_height = page_content.get("height")

            for block in page_content.get("blocks", []):
                for line in block.get("lines", []):

                    # ---- RECONSTRUCT FULL LINE ----
                    line_parts = []
                    line_spans = []

                    for span in line.get("spans", []):
                        text = span.get("text", "")
                        if text.strip():
                            line_parts.append(text)
                            line_spans.append(span)

                    if not line_parts:
                        continue

                    line_text = "".join(line_parts).strip()

                    # ---- STOP CONDITION: "End of paper" ----
                    if "end of paper" in line_text.lower():
                        stop_extraction = True
                        break

                    # Use first span for positioning / style
                    first_span = line_spans[0]
                    x0, y0, x1, y1 = first_span.get("bbox", (0, 0, 0, 0))

                    # Ignore headers / footers
                    if page_height:
                        if y0 < TOP_MARGIN_THRESHOLD:
                            continue
                        if y1 > page_height - BOTTOM_MARGIN_THRESHOLD:
                            continue

                    # Detect page number once
                    if detected_page is None:
                        detected_page = extract_page_number_from_text(
                            line_text, page_index
                        )

                    # ---- QUESTION START ----
                    if is_question_start(first_span):
                        if current_question:
                            all_questions.append({
                                "page": current_page,
                                "text": "\n".join(current_question).strip()
                            })

                        current_question = [line_text]
                        current_page = detected_page
                        continue

                    # ---- QUESTION BODY ----
                    if current_question:
                        # Skip known boilerplate lines
                        if any(ex.lower() in line_text.lower() for ex in EXEMPTIONS):
                            continue

                        # Skip lines that are mostly punctuation or page numbers
                        if re.fullmatch(r'[-–—\s\d]+', line_text):
                            continue

                        # Skip extremely short lines
                        if len(line_text.strip()) < 3:
                            continue

                        current_question.append(line_text)

                if stop_extraction:
                    break

        # Flush final question
        if current_question:
            all_questions.append({
                "page": current_page,
                "text": "\n".join(current_question).strip()
            })

        return all_questions

    except Exception as e:
        print(f"Error extracting questions: {e}")
        return []


# =========================
# QUESTION COMBINING
# =========================

def combine_snippets(questions):
    """
    Combines fragments safely WITHOUT merging MCQs together.
    """
    combined_questions = []

    main_question_pattern = re.compile(r'^Question\s+(\d+)', re.IGNORECASE)
    continued_question_pattern = re.compile(r'^Question\s+(\d+)\s*\(continued\)', re.IGNORECASE)
    mcq_start_pattern = re.compile(r'^\d+\b')
    subpart_pattern = re.compile(r'^\([a-z]\)')

    for q in questions:
        text = q["text"]
        page = q["page"]
        first_line = text.splitlines()[0].strip()

        is_main = main_question_pattern.match(first_line)
        is_continued = continued_question_pattern.match(first_line)
        is_mcq = mcq_start_pattern.match(first_line)
        is_subpart = subpart_pattern.match(first_line)

        if not combined_questions:
            combined_questions.append({"page": page, "text": text})
            continue

        # Merge ONLY true continuations or subparts
        if is_subpart or is_continued:
            combined_questions[-1]["text"] += "\n" + text

        # Start new question (MCQ or normal)
        elif is_main or is_mcq:
            combined_questions.append({"page": page, "text": text})

        else:
            # Fallback: merge conservatively
            combined_questions[-1]["text"] += "\n" + text

    return combined_questions

# =========================
# FULL PIPELINE
# =========================

def question_to_text(file_path):
    pages, metadata = extract_pages(file_path)
    questions = extract_questions(pages)
    final_questions = combine_snippets(questions)
    return metadata, final_questions

def all_questions():
    all_metadata = []
    all_qs = []
    for file in os.listdir("exams"):
        print(f"Processing {file}")
        metadata, qs = question_to_text(f"exams/{file}")
        all_metadata.append(metadata)
        all_qs.append(qs)
    return all_metadata, all_qs

if __name__ == "__main__":
    all_questions()
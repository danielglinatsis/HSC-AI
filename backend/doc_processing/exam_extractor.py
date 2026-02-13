import re
import os
import sys
import fitz
import pickle

from pathlib import Path

# -------------------------------------------------
# Allow importing constants from project root
# -------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from backend.doc_processing import helpers

from config.constants import (
    EXAM_DIR,
    EXEMPTIONS,
    QUESTION_REGEX,
    LEFT_MARGIN_THRESHOLD,
    TOP_MARGIN_THRESHOLD,
    BOTTOM_MARGIN_THRESHOLD,
    MIN_BODY_FONT_SIZE,
)


# =================================================
# PAGE EXTRACTION
# =================================================

def extract_pages(FILE_PATH):
    """
    Extract all pages from a PDF exam file
    """
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


# =================================================
# PAGE NUMBER DETECTION
# =================================================

def extract_page_number_from_text(text, fallback):
    """
    Extracts a visible page number from page text
    If no match is found, the PDF page index is returned
    """
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


# =================================================
# QUESTION START DETECTION
# =================================================

def is_question_start(span):
    """
    Identifies question starts

    Detects:
        - Multiple-choice questions (e.g. "10")
        - Short answer questions (e.g. "Question 12")

    Checks for:
        - Bold font
        - Matches QUESTION_REGEX
        - Left-aligned on page
        - Sufficient font size
    """
    x0, _, _, _ = span.get("bbox", (0, 0, 0, 0))

    text = span.get("text", "").strip()
    is_bold = span.get("flags", 0) & 16
    is_valid_text = QUESTION_REGEX.fullmatch(text)
    is_left_aligned = x0 <= LEFT_MARGIN_THRESHOLD
    is_valid_font_size = span.get("size", 0) >= MIN_BODY_FONT_SIZE

    if (
        not text
        or not is_bold
        or not is_valid_text
        or not is_left_aligned
        or not is_valid_font_size
    ):
        return False

    return True


# =================================================
# QUESTION EXTRACTION
# =================================================

def extract_questions(pages):
    """
    Parses page dictionaries and extracts question text blocks
    """
    all_questions = []

    current_question = None
    current_page = None
    stop_extraction = False
    detected_page = None

    try:
        # -----------------------------------------
        # Skip cover page (page 0)
        # -----------------------------------------
        for page in pages[1:]:

            if stop_extraction:
                break

            page_index = page.get("page_index")
            page_content = page.get("text")

            if not isinstance(page_content, dict):
                continue

            page_height = page_content.get("height")
            blocks = page_content.get("blocks", [])

            # -----------------------------------------
            # Iterate through page blocks
            # -----------------------------------------
            for block in blocks:

                lines = block.get("lines", [])

                for line in lines:

                    # ---------------------------------
                    # Reconstruct full readable line
                    # ---------------------------------
                    spans = [
                        span for span in line.get("spans", [])
                        if span.get("text", "").strip()
                    ]

                    if not spans:
                        continue

                    line_text = "".join(
                        span["text"] for span in spans
                    ).strip()

                    # ---------------------------------
                    # Margin-based filtering
                    # ---------------------------------
                    first_span = spans[0]
                    _, y0, _, y1 = first_span.get(
                        "bbox", (0, 0, 0, 0)
                    )

                    if page_height:
                        if y0 < TOP_MARGIN_THRESHOLD:
                            continue
                        if y1 > page_height - BOTTOM_MARGIN_THRESHOLD:
                            continue

                    # ---------------------------------
                    # Detect printed page number once
                    # ---------------------------------
                    if detected_page is None:
                        detected_page = extract_page_number_from_text(
                            line_text,
                            page_index
                        )

                    # ---------------------------------
                    # Question start detection
                    # ---------------------------------
                    if is_question_start(first_span):

                        if current_question:
                            all_questions.append({
                                "page": current_page,
                                "text": "\n".join(current_question).strip()
                            })

                        current_question = [line_text]
                        current_page = detected_page
                        continue

                    # ---------------------------------
                    # Question body handling
                    # ---------------------------------
                    if not current_question:
                        continue

                    # Skip boilerplate lines
                    if any(
                        ex.lower() in line_text.lower()
                        for ex in EXEMPTIONS
                    ):
                        continue

                    # Skip divider lines and page numbers
                    if re.fullmatch(r"[-–—\s\d]+", line_text):
                        continue

                    # Skip short lines
                    if len(line_text) < 3:
                        continue

                    current_question.append(line_text)

                    # ---------------------------------
                    # Stop extraction marker
                    # ---------------------------------
                    if "end of paper" in line_text.lower():
                        stop_extraction = True
                        break

                if stop_extraction:
                    break

        # -----------------------------------------
        # Flush final question
        # -----------------------------------------
        if current_question:
            all_questions.append({
                "page": current_page,
                "text": "\n".join(current_question).strip()
            })

        return all_questions

    except Exception as e:
        print(f"Error extracting questions: {e}")
        return []


# =================================================
# QUESTION COMBINING
# =================================================

def combine_snippets(questions):
    """
    Combines fragmented question blocks safely.

    Rules:
        • Merge (a), (b), (c) subparts
        • Merge '(continued)' questions
        • Never merge separate MCQs
    """
    combined_questions = []

    main_question_pattern = re.compile(
        r'^Question\s+(\d+)', re.IGNORECASE
    )
    continued_question_pattern = re.compile(
        r'^Question\s+(\d+)\s*\(continued\)', re.IGNORECASE
    )
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
            combined_questions.append({
                "page": page,
                "text": text
            })
            continue

        # Merge true continuations only
        if is_subpart or is_continued:
            combined_questions[-1]["text"] += "\n" + text

        # Start new question
        elif is_main or is_mcq:
            combined_questions.append({
                "page": page,
                "text": text
            })

        # Conservative fallback
        else:
            combined_questions[-1]["text"] += "\n" + text

    return combined_questions


# =================================================
# QUESTION PIPELINE
# =================================================

def question_to_text(file_path):
    pages, metadata = extract_pages(file_path)
    questions = extract_questions(pages)
    final_questions = combine_snippets(questions)
    return metadata, final_questions


def get_all_questions():
    all_metadata = []
    all_qs = []

    for file in sorted(os.listdir(EXAM_DIR)):
        print(f"Processing {file}")
        metadata, qs = question_to_text(os.path.join(EXAM_DIR, file))
        all_metadata.append(metadata)
        all_qs.append(qs)

    return {
        "metadata": all_metadata,
        "questions": all_qs
    }


# =================================================
# EXAM PIPELINE
# =================================================

def identify_exams(pickle_path):
    """
    Extracts exams already stored in  pickle file
    """
    try:
        with open(pickle_path, "rb") as f:
            data = pickle.load(f)
    except Exception as e:
        print(f"Error loading pickle file: {e}")
        return set()

    pdf_names = set()

    # Dictionary-based structure
    if isinstance(data, dict) and "questions" in data:
        for exam_questions in data["questions"]:
            if isinstance(exam_questions, list) and exam_questions:
                first_q = exam_questions[0]
                if isinstance(first_q, dict) and "exam" in first_q:
                    pdf_names.add(first_q["exam"])

    # Flattened structure
    flat_data = list(
        helpers.flatten(
            data if not isinstance(data, dict)
            else data.get("questions", [])
        )
    )

    for item in flat_data:
        if isinstance(item, dict):
            if "exam" in item:
                pdf_names.add(item["exam"])
            if "source" in item:
                pdf_names.add(item["source"])
        elif hasattr(item, "metadata"):
            if "exam" in item.metadata:
                pdf_names.add(item.metadata["exam"])
            if "source" in item.metadata:
                pdf_names.add(item.metadata["source"])

    # Metadata titles
    if isinstance(data, dict) and "metadata" in data:
        for meta in data["metadata"]:
            if isinstance(meta, dict) and meta.get("title"):
                pdf_names.add(meta["title"])

    return sorted(list(pdf_names))


def process_exams(pickle_path):
    """
    Syncs PDFs in `EXAM_DIR` with stored pickle data
    """
    all_metadata = []
    all_qs = []
    processed_exam_names = set()

    # ---------------------------------------------
    # Scan exam directory
    # ---------------------------------------------
    if not os.path.exists(EXAM_DIR):
        os.makedirs(EXAM_DIR)

    uploaded_exams = sorted(
        f for f in os.listdir(EXAM_DIR) if f.endswith(".pdf")
    )

    # Helper to normalize names for comparison
    def normalize_name(name):
        return name.lower().replace("-", " ").replace(".pdf", "").strip()

    # Create a mapping of normalized names to actual filenames
    filename_map = {normalize_name(f): f for f in uploaded_exams}

    # ---------------------------------------------
    # Load existing pickle
    # ---------------------------------------------
    if os.path.exists(pickle_path):
        try:
            with open(pickle_path, "rb") as f:
                data = pickle.load(f)
                all_metadata = data.get("metadata", [])
                all_qs = data.get("questions", [])

            # Ensure all questions have the 'exam' key and map to filenames
            for i, exam_questions in enumerate(all_qs):
                if isinstance(exam_questions, list) and exam_questions:
                    raw_exam_name = None
                    
                    # 1. Check first question
                    first_q = exam_questions[0]
                    if isinstance(first_q, dict):
                        raw_exam_name = first_q.get("exam") or first_q.get("source")
                    elif hasattr(first_q, "metadata"):
                        raw_exam_name = first_q.metadata.get("exam") or first_q.metadata.get("source")
                    
                    # 2. If still None, try metadata
                    if not raw_exam_name and i < len(all_metadata):
                        meta = all_metadata[i]
                        if isinstance(meta, dict):
                            raw_exam_name = meta.get("title")
                    
                    if raw_exam_name:
                        # Try to resolve to an actual filename
                        norm_name = normalize_name(raw_exam_name)
                        actual_filename = filename_map.get(norm_name) or raw_exam_name
                        
                        processed_exam_names.add(actual_filename)
                        for q in exam_questions:
                            if isinstance(q, dict):
                                q["exam"] = actual_filename
                            elif hasattr(q, "metadata"):
                                q.metadata["exam"] = actual_filename

        except Exception as e:
            print(f"Error loading existing pickle: {e}")

    new_exams = [
        f for f in uploaded_exams
        if f not in processed_exam_names
    ]

    # ---------------------------------------------
    # Process new exams
    # ---------------------------------------------
    if new_exams:

        print(f"Found {len(new_exams)} new exams to process: {new_exams}")

        for exam_file in new_exams:

            file_path = os.path.join(EXAM_DIR, exam_file)
            print(f"Processing {exam_file}...")

            metadata, qs = question_to_text(file_path)

            for q in qs:
                if isinstance(q, dict):
                    q["exam"] = exam_file
                elif hasattr(q, "metadata"):
                    q.metadata["exam"] = exam_file

            all_metadata.append(metadata)
            all_qs.append(qs)

        # -----------------------------------------
        # Save updated pickle
        # -----------------------------------------
        try:
            os.makedirs(os.path.dirname(pickle_path), exist_ok=True)

            data = {
                "metadata": all_metadata,
                "questions": all_qs
            }

            with open(pickle_path, "wb") as f:
                pickle.dump(
                    data,
                    f,
                    protocol=pickle.HIGHEST_PROTOCOL
                )

            print(f"Updated pickle file at {pickle_path}")

        except Exception as e:
            print(f"Error saving updated pickle: {e}")

    else:
        print("No new exams found. All documents already processed.")

    return {
        "metadata": all_metadata,
        "questions": all_qs
    }


# =================================================
# HELPER FUNCTIONS
# =================================================

def print_all_questions(data):
    """
    Print all extracted questions
    """
    all_qs = data.get("questions", [])
    flat_qs = list(helpers.flatten(all_qs))

    for i, q in enumerate(flat_qs, start=1):

        if not isinstance(q, dict):
            print(f"Skipping non-dict item: {q}")
            continue

        page = q.get("page", "N/A")
        text = q.get("text", "").strip()

        print(f"\n{'=' * 40}")
        print(f"Question {i} (Page {page})")
        print("-" * 40)
        print(text)
        print(f"{'=' * 40}\n")


# =================================================
# ENTRY POINT
# =================================================

if __name__ == "__main__":

    pickle_file_path = "backend/doc_processing/all_questions.pkl"
    data = process_exams(pickle_file_path)

    print(f"Total exams in system: {len(data['questions'])}")

    names = identify_exams(pickle_file_path)
    print(f"Verified exams in pickle: {names}")

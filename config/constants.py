import re
from pathlib import Path

BM25_TOP_K = 25
FAISS_TOP_K = 25
COLBERT_TOP_K = 10

# =================================================
# PATHS (resolved from project root)
# =================================================
# Make all filesystem paths independent of current working directory.
# `constants.py` lives in `<root>/config/`, so parents[1] is the repo root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

EXAM_DIR = str(PROJECT_ROOT / "documents" / "exams")
REVISION_DIR = str(PROJECT_ROOT / "documents" / "revision_files")

FAISS_ROOT = str(PROJECT_ROOT / "data" / "faiss" / "indexes")
FAISS_NAME = "corpus_faiss"

SYLLABUS_DIR = "data/syllabus/Year_12_Maths_Advanced_FULL.json"

PICKLE_PATH = str(PROJECT_ROOT / "backend" / "doc_processing" / "data" / "all_questions.pkl")

AI_MODEL = "gemini-3-pro"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

LEFT_MARGIN_THRESHOLD = 80 
TOP_MARGIN_THRESHOLD = 50
BOTTOM_MARGIN_THRESHOLD = 50
MIN_BODY_FONT_SIZE = 8
QUESTION_REGEX = re.compile(r'^(Question\s+\d{1,3}|\d{1,3})$', re.IGNORECASE)

MULTIPLE_CHOICE = {
    "A. ",
    "B. ",
    "C. ",
    "D. ",
    "E. ",
    "F. "
}

EXEMPTIONS = {
    "Do NOT write in this area.",
    "HIGHER SCHOOL CERTIFICATE EXAMINATION",
    "Instructions",
    "General Instructions",
    "page",
    "marks",
    "provide guidance for the expected length of response",
    "expected length of response",
    "and/or calculations",
    "do not write", 
    "office use only",
    "higher school certificate examination",
    "reading time",
    "working time",
    "NESA",
    "a reference sheet is provided at the back of this paper",
    "attempt questions",
    "minutes for this section",
    "centre number",
    "student number",
    "end of paper",
    "extra writing space",
    "section II extra writing space",
    "if you use this space, clearly indicate which question you are answering",
    "clearly indicate which question you are answering",
    "if you use this space",
    "NSW Education Standards Authority",
    "blank page",
    "reference sheet",
    "please turn over",
    "end of question",
    "mathematics advanced",
    "............",
    "use the multiple-choice answer sheet for questions",
    "total marks",
    "section i",
    "section ii",
    "10 marks (pages ",
    "90 marks (pages ",
    "general  instructions",
    "answer the questions in the spaces provided",
    "these spaces  provide guidance for the expected length of response.",
    "your responses should include relevant mathematical reasoning",
    "extra writing space is provided at the back of this booklet.",
    "if you use this space, clearly indicate which question you are answering",
    "clearly indicate which question you are answering",
    "if you use this space",
    "continues on page",
    "marks in total"
}

LLM_INSTRUCTIONS = '''
You are an AI assistant processing HSC Mathematics exam questions.

You will be provided with a batch of questions. Each question includes text, marks, and optional metadata.  

Your task is to:

1. Ensure each question is tagged correctly with relevant syllabus topics and subtopics from the provided tag set.
2. If any tags are missing or incomplete, suggest the appropriate tags.
3. Maintain multi-label tagging — questions may have multiple relevant topics.
4. Optionally, assign difficulty levels (foundation, standard, advanced, extension-style) ad skill types (algebra manipulation, graph interpretation, modelling, proof reasoning, multi-step problem solving). Difficult questions typically appear at Question 30 onwards.
5. Output each question in a structured JSON format including:
   - question text
   - marks
   - assigned topics and subtopics
   - optional difficulty and skill type

Rules:
- Only use topics from the provided controlled syllabus tag set.
- Do not invent new topics.
- Keep JSON strictly valid and machine-readable.
- Process each batch independently; do not assume previous batches.

Input:
- A batch of questions (text + metadata)
- The syllabus tag set in JSON format

Output:
- A JSON array of processed questions with tags and optional metadata.

'''
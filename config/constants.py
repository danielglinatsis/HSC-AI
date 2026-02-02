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

PICKLE_PATH = str(PROJECT_ROOT / "data" / "processed_exams" / "all_questions.pkl")

AI_MODEL = "gemini-2.5-flash"
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

LLM_INSTRUCTIONS = """
You are an AI study assistant helping students revise for exams.

Inputs:
A user query specifying the topics/concepts the student wants to revise.
The full syllabus as a list of Sections, subsections and dotpoints.

Task:
Identify the syllabus items relevant to the user query.
Generate a retriever-friendly RAG prompt tailored to the query, incorporating the relevant syllabus items.

Output:
A clear, concise RAG prompt that can be used to retrieve relevant exam content.

"""
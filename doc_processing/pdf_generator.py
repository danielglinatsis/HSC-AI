import os
from pypdf import PdfReader, PdfWriter
from collections import defaultdict

def group_pages_by_exam(docs):
    pages_by_exam = defaultdict(set)

    for doc in docs:
        exam = doc.metadata["exam"]
        page = doc.metadata["page"] - 1  # PDFs are 0-indexed
        pages_by_exam[exam].add(page)

    return pages_by_exam

def build_custom_pdf(
    retrieved_docs,
    exams_dir="exams",
    output_path="relevant_questions.pdf",
):
    writer = PdfWriter()
    pages_by_exam = group_pages_by_exam(retrieved_docs)

    for exam, pages in pages_by_exam.items():
        pdf_path = os.path.join(exams_dir, exam)
        reader = PdfReader(pdf_path)

        for page_num in sorted(pages):
            if page_num < len(reader.pages):
                writer.add_page(reader.pages[page_num])

    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path

import os
import io
from collections import defaultdict
from pypdf import PdfReader, PdfWriter, PageObject
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors  

# -----------------------------
# Group retrieved docs by exam
# -----------------------------
def group_pages_by_exam(docs):
    '''
    Groups pages of documents by exam name metadata
    '''
    pages_by_exam = defaultdict(set)
    for doc in docs:
        exam = doc.metadata.get("exam")
        page = doc.metadata.get("page")
        if exam and page is not None:
            pages_by_exam[exam].add(page - 1)
        else:
            print(f"Warning: Document missing 'exam' or 'page' metadata: {doc.metadata}")
    return pages_by_exam

# -----------------------------
# Create header overlay page
# -----------------------------

def create_header_page(original_page, label_text):
    '''
    Returns a new page with a header overlayed on the original page
    '''
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    # Set font and color
    can.setFont("Helvetica-Bold", 12)
    can.setFillColor(colors.red)  # make text red

    # Draw text near the top-left corner
    can.drawString(40, 780, label_text)  # y=780 is closer to top than 750

    can.save()
    packet.seek(0)

    # Read the overlay page
    header_pdf = PdfReader(packet)
    header_page = header_pdf.pages[0]

    # Merge original page with header
    merged_page = PageObject.create_blank_page(
        width=original_page.mediabox.width,
        height=original_page.mediabox.height
    )
    merged_page.merge_page(original_page)
    merged_page.merge_page(header_page)
    return merged_page

# -----------------------------
# Build custom PDF with labels
# -----------------------------
def build_custom_pdf(
    retrieved_docs,
    exams_dir,
    output_path
):
    '''
    Builds a compiled PDF from the original exam pages matching the retrieved documents.
    Each page is overlaid with a red "Source: <filename>" header.
    '''
    writer = PdfWriter()
    pages_by_exam = group_pages_by_exam(retrieved_docs)

    # Pre-list exams to handle name mismatches
    available_exams = {}
    if os.path.exists(exams_dir):
        for f in os.listdir(exams_dir):
            if f.endswith(".pdf"):
                # Map normalized name to actual filename
                norm = f.lower().replace("-", " ").replace(".pdf", "").strip()
                available_exams[norm] = f
                # Also map actual filename
                available_exams[f.lower()] = f

    for exam_label, pages in pages_by_exam.items():
        # Try exact match first
        pdf_filename = available_exams.get(exam_label.lower())
        
        # If not found, try normalized match
        if not pdf_filename:
            norm_label = exam_label.lower().replace("-", " ").replace(".pdf", "").strip()
            pdf_filename = available_exams.get(norm_label)

        if not pdf_filename:
            print(f"Warning: Could not find a PDF matching '{exam_label}' in {exams_dir}")
            continue

        pdf_path = os.path.join(exams_dir, pdf_filename)
        reader = PdfReader(pdf_path)
        for page_num in sorted(pages):
            if page_num < len(reader.pages):
                original_page = reader.pages[page_num]
                labeled_page = create_header_page(original_page, f"Source: {pdf_filename}")
                writer.add_page(labeled_page)

    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"PDF saved as {output_path}")
    return output_path

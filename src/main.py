import os
import re
import sys
from pathlib import Path

# Ensure project root is importable (for `config/` etc.)
sys.path.append(str(Path(__file__).resolve().parent.parent))

import retrieval_pipeline

from setup import retriever_setup
from doc_processing import pdf_generator, exam_extractor

from config.constants import EXAM_DIR, PICKLE_PATH, REVISION_DIR

# =================================================
# PRE-RUN SETUP
# =================================================

def setup():
    """
    Processes any necessary documents
    Initialises ensemble retriever with processed documents
    """    
    data = exam_extractor.process_exams(PICKLE_PATH)

    retriever = retriever_setup.create_ensemble_retriever(data["questions"])

    return retriever

# =================================================
# MAIN LOOP
# =================================================

def run(retriever):
    """
    Main loop
    Requests user query, extracts relevant questions and builds a new PDF document
    """
    if retriever is None:
        print("Retriever failed to initialise (no questions loaded).")
        print(f"Check that PDFs exist in '{EXAM_DIR}' and the pickle path '{PICKLE_PATH}' is valid.")
        return

    while True:
        print("\nWhat do you wish to revise? (Enter 'q' to quit)")
        query = input("> ")

        if query.lower() == "q":
            print("Exiting...")
            break

        print("Searching for relevant questions and generating response...")

        try:
            response = retrieval_pipeline.get_response(query, retriever)
            print("\n--- AI REVISION ASSISTANT ---")
            print(response)
            print("----------------------------")

            # Windows-safe filename from query
            safe = re.sub(r'[<>:"/\\\\|?*\\n\\r\\t]+', " ", query).strip()
            safe = re.sub(r"\\s+", " ", safe) or "revision"
            pdf_name = f"{safe}.pdf"

            os.makedirs(REVISION_DIR, exist_ok=True)
            out_path = os.path.join(REVISION_DIR, pdf_name)
            pdf_generator.build_custom_pdf(response, EXAM_DIR, out_path)

        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    retriever = setup()
    run(retriever)
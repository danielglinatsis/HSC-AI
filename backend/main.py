import os
import re
import sys
from pathlib import Path

# Ensure project root is importable (for `config/` etc.)
sys.path.append(str(Path(__file__).resolve().parent.parent))

from ai_calls import retrieval_pipeline

from setup import retriever_setup, ai_model_setup
from doc_processing import pdf_generator, exam_extractor
from doc_processing.process_questions import tag_questions_with_llm, save_questions

from config.constants import EXAM_DIR, PICKLE_PATH, REVISION_DIR

# =================================================
# PRE-RUN SETUP
# =================================================

def setup():
    """
    Processes any necessary documents
    Initialises ensemble retriever with processed documents
    """    
    ai_model_setup.google_api_setup()
    data = exam_extractor.process_exams(PICKLE_PATH)
    data = tag_questions_with_llm(data)
    save_questions(data)
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

            pdf_name = f"{query}.pdf"

            os.makedirs(REVISION_DIR, exist_ok=True)
            out_path = os.path.join(REVISION_DIR, pdf_name)
            pdf_generator.build_custom_pdf(response, EXAM_DIR, out_path)

        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    retriever = setup()
    run(retriever)
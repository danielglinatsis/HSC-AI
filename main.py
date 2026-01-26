import retrieval_pipeline

from setup import retriever_setup
from doc_processing import pdf_generator, exam_extractor

from config.constants import REVISION_DIR

# =================================================
# PRE-RUN SETUP
# =================================================

def setup():
    """
    Processes any necessary documents
    Initialises ensemble retriever with processed documents
    """    
    pickle_path = "doc_processing/data/all_questions.pkl"
    data = exam_extractor.process_exams(pickle_path)

    retriever = retriever_setup.create_ensemble_retriever(data["metadata"], data["questions"])

    return retriever

# =================================================
# MAIN LOOP
# =================================================

def run(retriever):
    """
    Main loop
    Requests user query, extracts relevant questions and builds a new PDF document
    """
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
        except Exception as e:
            print(f"An error occurred: {e}")

        pdf_name = f"{query}.pdf"
        pdf_generator.build_custom_pdf(response, "exams", f"{REVISION_DIR}/{pdf_name}")

if __name__ == "__main__":
    retriever = setup()
    run(retriever)
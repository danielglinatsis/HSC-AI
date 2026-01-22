import retrieval_pipeline
from doc_processing import pdf_generator, doc_extractor
from setup import retriever_setup

from constants import REVISION_DIR

def setup():
    #Process docs
    pickle_path = "doc_processing/data/all_questions.pkl"
    all_metadata, all_qs = doc_extractor.process_exams(pickle_path)
    #retriever setup
    retriever = retriever_setup.create_ensemble_retriever(all_metadata, all_qs)

    return retriever

def run(retriever):

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
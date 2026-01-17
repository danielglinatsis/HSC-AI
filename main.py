import rag_pipeline
from doc_processing import pdf_generator
from setup import retriever_setup, ai_model_setup

def main():
    
    retriever, all_metadata, all_qs = retriever_setup.create_ensemble_retriever()
    ai_model = ai_model_setup.google_api_setup()

    while True:
        print("\nWhat do you wish to revise? (Enter 'q' to quit)")
        query = input("> ")

        if query.lower() == "q":
            print("Exiting...")
            break

        print("Searching for relevant questions and generating response...")
        try:
            response = rag_pipeline.get_rag_response(query, retriever)
            print("\n--- AI REVISION ASSISTANT ---")
            print(response)
            print("----------------------------")
        except Exception as e:
            print(f"An error occurred: {e}")
        pdf_generator.build_custom_pdf(response)
        print(f"Generated PDF: {pdf_generator.build_custom_pdf(response)}")
        print("----------------------------")

if __name__ == "__main__":
    main()
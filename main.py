import rag_pipeline

def main():
    while True:
        print("\nWhat do you wish to revise? (Enter 'q' to quit)")
        query = input("> ")

        if query.lower() == "q":
            print("Exiting...")
            break
        
        if not query.strip():
            continue

        print("Searching for relevant questions and generating response...")
        try:
            response = rag_pipeline.get_rag_response(query)
            print("\n--- AI REVISION ASSISTANT ---")
            print(response)
            print("----------------------------")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
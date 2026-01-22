import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from setup import retriever_setup

def get_response(query, retriever):
    print("Retrieving relevant questions...")
    qs = retriever.get_relevant_documents(query)
    print("Loading reranker...")
    reranker = retriever_setup.load_reranker()
    print("Reranking questions...")
    reranked_qs = retriever_setup.rerank_documents(reranker, query, qs)
    
    return reranked_qs

if __name__ == "__main__":
    from doc_processing import doc_extractor
    pickle_path = "doc_processing/data/all_questions.pkl"
    all_metadata, all_qs = doc_extractor.process_exams(pickle_path)
    retriever = retriever_setup.create_ensemble_retriever(all_metadata, all_qs)
    get_response("integration", retriever)
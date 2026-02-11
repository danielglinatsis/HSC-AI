import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from setup import retriever_setup

def get_response(query, retriever):
    print("Retrieving relevant questions...")
    if retriever is None or not hasattr(retriever, "get_relevant_documents"):
        raise ValueError("Retriever is not initialised (None or missing get_relevant_documents).")
    qs = retriever.invoke(query)
    print("Loading reranker...")
    reranker = retriever_setup.load_reranker()
    print("Reranking questions...")
    reranked_qs = retriever_setup.rerank_documents(reranker, query, qs)
    
    return reranked_qs

if __name__ == "__main__":
    from doc_processing import exam_extractor
    from config.constants import PICKLE_PATH
    data = exam_extractor.process_exams(PICKLE_PATH)
    retriever = retriever_setup.create_ensemble_retriever(data.get("questions", []))
    get_response("integration", retriever)
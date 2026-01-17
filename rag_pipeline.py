import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from setup import retriever_setup

def get_rag_response(query, retriever):
    docs = retriever.get_relevant_documents(query)
    print(docs)
    return docs

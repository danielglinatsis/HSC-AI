import os
import sys
import torch
from pathlib import Path
from typing import Iterable, List

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config.constants import (
    BM25_TOP_K, 
    FAISS_TOP_K, 
    FAISS_ROOT, 
    FAISS_NAME, 
    EMBEDDING_MODEL, 
    COLBERT_TOP_K
)

from doc_processing.helpers import flatten, docs_to_texts_and_meta

from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain_classic.retrievers import EnsembleRetriever
from langchain_huggingface import HuggingFaceEmbeddings
from sentence_transformers import CrossEncoder
from langchain_core.documents import Document



# =================================================
# RETRIEVER FUNCTIONS
# =================================================

def setup_bm25_retriever(docs: List[Document]):
    retriever = BM25Retriever.from_documents(docs)
    retriever.k = BM25_TOP_K
    print("BM25 retriever created")
    return retriever


def setup_faiss_retriever(docs: List[Document]):
    if not docs:
        raise ValueError("No documents provided for FAISS indexing")

    embedding = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vs = load_or_update_faiss(docs, embedding)

    print("FAISS retriever created")
    return vs.as_retriever(search_kwargs={"k": FAISS_TOP_K})


def load_or_update_faiss(docs: List[Document], embedding) -> FAISS:
    index_path = os.path.join(FAISS_ROOT, FAISS_NAME)
    texts, metadatas = docs_to_texts_and_meta(docs)

    if os.path.exists(index_path):
        print(f"Loading FAISS index from {index_path}")
        try:
            vs = FAISS.load_local(
                index_path,
                embedding,
                allow_dangerous_deserialization=True,
            )
        except Exception as e:
            print(f"FAISS index unreadable ({e}) — rebuilding")
        else:
            existing = {d.page_content for d in vs.docstore._dict.values()}

            # Detect format mismatch: new docs have tag enrichment but the saved
            # index was built before tags existed. Rebuild to avoid duplicates.
            new_have_tags = any("Topics:" in d.page_content for d in docs)
            old_have_tags = any("Topics:" in c for c in existing)
            if new_have_tags and not old_have_tags:
                print("Tag-enriched content detected — rebuilding FAISS index")
                # Fall through to rebuild; save_local overwrites files in-place
            else:
                new_docs = [d for d in docs if d.page_content not in existing]
                if new_docs:
                    print(f"Appending {len(new_docs)} new items to FAISS index")
                    new_texts, new_metas = docs_to_texts_and_meta(new_docs)
                    vs.add_texts(new_texts, metadatas=new_metas)
                    vs.save_local(index_path)
                else:
                    print("No new FAISS entries found")
                return vs

    print(f"Creating new FAISS index at {index_path}")
    os.makedirs(FAISS_ROOT, exist_ok=True)
    vs = FAISS.from_texts(texts, embedding, metadatas=metadatas)
    vs.save_local(index_path)
    return vs


def expand_content(question: dict) -> str:
    """Build the text stored in page_content for retrieval.

    Tags, difficulty, and skill types are appended so both BM25 and FAISS
    can match against them directly, e.g. a query for 'integration' will
    surface questions tagged 'Calculus / Integration' even when the raw
    question text uses different wording.
    """
    parts = [question.get("text", "")]
    if question.get("tags"):
        parts.append("Topics: " + ", ".join(question["tags"]))
    if question.get("difficulty"):
        parts.append("Difficulty: " + question["difficulty"])
    if question.get("skill_types"):
        parts.append("Skills: " + ", ".join(question["skill_types"]))
    return "\n".join(p for p in parts if p)


def create_ensemble_retriever(nested_questions, weights=[0.4,0.6]):

    flat_questions = flatten(nested_questions)

    if not flat_questions:
        print("No questions found")
        return None

    docs = [
        Document(
            page_content= expand_content(q),
            metadata={k: v for k, v in q.items() if k != "text"},
        )
        for q in flat_questions
    ]

    # Create ensemble retriever
    bm25 = setup_bm25_retriever(docs)
    faiss = setup_faiss_retriever(docs)
    retriever = EnsembleRetriever(retrievers=[bm25, faiss], weights=weights)

    return retriever


# =================================================
# COLBERT RERANKER FUNCTIONS
# =================================================

def load_reranker():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    reranker = CrossEncoder(model_name, device=device)
    return reranker


def rerank_documents(reranker, query, qs, top_k=COLBERT_TOP_K):
    # Extract text from Document objects if needed
    texts = [q.page_content if hasattr(q, 'page_content') else q for q in qs]
    
    # Create query-document pairs
    pairs = [[query, text] for text in texts]
    
    # Get scores from cross-encoder
    scores = reranker.predict(pairs)
    
    # Sort by score and return top-k
    reranked = sorted(zip(scores.tolist(), qs), key=lambda x: x[0], reverse=True)
    return [doc for score, doc in reranked[:top_k]]


if __name__ == "__main__":
    from doc_processing import exam_extractor
    from config.constants import PICKLE_PATH
    data = exam_extractor.process_exams(PICKLE_PATH)
    retriever = create_ensemble_retriever(data.get("questions", []))
    if retriever:
        print("Ensemble retriever is ready for use.")

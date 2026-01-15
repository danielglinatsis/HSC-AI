from rank_bm25 import BM25Retriever
from faiss import FaissRetriever

def retriever_setup(flattened_docs, all_metadatas, all_qs):
    bm25_retriever = BM25Retriever.from_documents(flattened_docs)
    faiss_retriever = FaissRetriever.from_documents(flattened_docs)
import os
import pickle
import numpy as np
import google.generativeai as genai
from dotenv import load_dotenv
from constants import RAG_INSTRUCTIONS

# Load environment variables
load_dotenv("secrets.env")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

VECTOR_STORE_PATH = "doc_processing/data/vector_store.pkl"
# Using gemini-1.5-flash as it's the stable high-speed model
# Gemini 2.0 Flash is also an option if available
MODEL_NAME = "gemini-1.5-flash"
EMBED_MODEL = "models/embedding-001"

def load_vector_store():
    if not os.path.exists(VECTOR_STORE_PATH):
        return None
    with open(VECTOR_STORE_PATH, "rb") as f:
        return pickle.load(f)

def get_query_embedding(query):
    result = genai.embed_content(
        model=EMBED_MODEL,
        content=query,
        task_type="retrieval_query"
    )
    return result['embeddings']

def retrieve_relevant_questions(query, vector_store, top_k=5):
    if not vector_store:
        return []
    
    query_emb = np.array(get_query_embedding(query))
    store_embs = vector_store["embeddings"]
    
    # Simple cosine similarity: (A . B) / (||A|| * ||B||)
    # Since Gemini embeddings are often normalized, dot product is usually enough
    # but we'll do the full check to be safe
    similarities = np.dot(store_embs, query_emb) / (
        np.linalg.norm(store_embs, axis=1) * np.linalg.norm(query_emb)
    )
    
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        results.append({
            "content": vector_store["data"][idx],
            "score": similarities[idx]
        })
    return results

def get_rag_response(query):
    """Full RAG flow: Retrieve and then Generate."""
    vector_store = load_vector_store()
    if not vector_store:
        return "Error: Vector store not found. Please run retriever_setup.py first."
    
    relevant_docs = retrieve_relevant_questions(query, vector_store)
    
    context_text = "\n\n".join([
        f"Source: {doc['content']['exam']} (Page {doc['content']['page']})\n{doc['content']['text']}"
        for doc in relevant_docs
    ])
    
    prompt = f"""
{RAG_INSTRUCTIONS}

Context:
{context_text}

User Question: {query}

Answer the user's request using the context provided above. If no relevant questions are found in the context, inform the user.
"""
    
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(prompt)
    
    return response.text

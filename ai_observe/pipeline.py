import pickle
import numpy as np
from sentence_transformers import SentenceTransformer, util
from transformers import pipeline

from ai_observe.sdk import trace

EMBEDDINGS_FILE = "ai_observe/corpus_embeddings.pkl"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
GENERATION_MODEL_NAME = "google/flan-t5-small"

# Lazy loading singletons for performance
_embedding_model = None
_generation_pipeline = None
_corpus_data = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedding_model

def get_generation_pipeline():
    global _generation_pipeline
    if _generation_pipeline is None:
        _generation_pipeline = pipeline("text2text-generation", model=GENERATION_MODEL_NAME)
    return _generation_pipeline

def load_corpus():
    global _corpus_data
    if _corpus_data is None:
        try:
            with open(EMBEDDINGS_FILE, "rb") as f:
                _corpus_data = pickle.load(f)
        except FileNotFoundError:
            raise RuntimeError(f"Embeddings file not found at {EMBEDDINGS_FILE}. Run compute_embeddings.py first.")
    return _corpus_data

@trace
def retrieve(query, top_k=3):
    corpus_data = load_corpus()
    model = get_embedding_model()
    
    query_embedding = model.encode(query)
    
    # Compute cosine similarity
    cos_scores = util.cos_sim(query_embedding, corpus_data["embeddings"])[0]
    
    # Get top_k results
    top_results = np.argpartition(-cos_scores, range(min(top_k, len(cos_scores))))[:top_k]
    
    results = []
    for idx in top_results:
        results.append({
            "id": corpus_data["docs"][idx]["id"],
            "text": corpus_data["docs"][idx]["text"],
            "score": float(cos_scores[idx])
        })
    
    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    return results

@trace
def generate_answer(query, retrieved):
    generator = get_generation_pipeline()
    
    context = " ".join([doc["text"] for doc in retrieved])
    
    # Truncate context if needed for flan-t5-small (~512 tokens max usually)
    context_words = context.split()[:300]
    truncated_context = " ".join(context_words)
    
    prompt = f"Answer the question based on the context.\nContext: {truncated_context}\nQuestion: {query}\nAnswer:"
    
    result = generator(prompt, max_length=150, truncation=True)
    return result[0]["generated_text"]

@trace
def judge_grounding(answer, retrieved):
    # evaluate based on embedding similarity of answer to context
    model = get_embedding_model()
    
    context = " ".join([doc["text"] for doc in retrieved])
    if not context:
        return {"verdict": "fail", "score": 0.0, "reason": "No context retrieved"}
        
    answer_embedding = model.encode(answer)
    context_embedding = model.encode(context)
    
    score = float(util.cos_sim(answer_embedding, context_embedding)[0][0])
    
    verdict = "pass" if score > 0.4 else "fail"
    return {
        "verdict": verdict,
        "score": score,
        "reason": "Embedding similarity > 0.4 between answer and context" if verdict == "pass" else "Low semantic overlap with context"
    }

@trace
def run_pipeline(query):
    retrieved = retrieve(query)
    answer = generate_answer(query, retrieved)
    judgment = judge_grounding(answer, retrieved)
    
    return {
        "query": query,
        "retrieved": retrieved,
        "answer": answer,
        "judgment": judgment
    }

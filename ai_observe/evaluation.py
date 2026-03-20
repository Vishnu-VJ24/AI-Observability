from sentence_transformers import SentenceTransformer, util

_eval_model = None

def get_eval_model():
    """Lazy load the sentence transformer to keep the SDK fast on import."""
    global _eval_model
    if _eval_model is None:
        _eval_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _eval_model

def evaluate_hallucination(generation_output, retrieved_docs):
    """
    Model-agnostic evaluation engine. 
    Accepts any LLM output and any retrieved documents structure.
    """
    if not retrieved_docs:
        return {"grounded": False, "score": 0.0, "reason": "No retrieval context available"}

    # Dynamically extract text from unknown retrieved_docs structure
    context_text = ""
    if isinstance(retrieved_docs, list):
        for doc in retrieved_docs:
            if isinstance(doc, dict):
                # Try common keys
                text = doc.get("text", doc.get("content", doc.get("page_content", "")))
                context_text += str(text) + " "
            elif hasattr(doc, "page_content"): # Langchain format support
                context_text += str(doc.page_content) + " "
            else:
                context_text += str(doc) + " "
    else:
        context_text = str(retrieved_docs)

    gen_text = str(generation_output)

    if not context_text.strip():
        return {"grounded": False, "score": 0.0, "reason": "Context text was empty"}

    model = get_eval_model()
    emb_gen = model.encode(gen_text)
    emb_ctx = model.encode(context_text)

    score = float(util.cos_sim(emb_gen, emb_ctx)[0][0])
    
    # Heuristic Threshold
    threshold_score = 0.4
    is_grounded = bool(score >= threshold_score)

    return {
        "grounded": is_grounded,
        "score": score,
        "reason": f"Cosine similarity is {score:.2f} (Threshold: {threshold_score})"
    }

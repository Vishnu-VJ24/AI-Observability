import chromadb
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, T5ForConditionalGeneration

from ai_observe import trace

CHROMA_DB_DIR = "ai_observe/chroma_db"
COLLECTION_NAME = "ai_observability_corpus"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
GENERATION_MODEL_NAME = "google/flan-t5-small"

# Lazy loading singletons for performance
_embedding_model = None
_generation_pipeline = None
_chroma_collection = None


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedding_model


def get_generation_model_and_tokenizer():
    global _generation_pipeline
    if _generation_pipeline is None:
        tokenizer = AutoTokenizer.from_pretrained(GENERATION_MODEL_NAME)
        model = T5ForConditionalGeneration.from_pretrained(
            GENERATION_MODEL_NAME
        )
        _generation_pipeline = (tokenizer, model)
    return _generation_pipeline


def get_chroma_collection():
    global _chroma_collection
    if _chroma_collection is None:
        client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        try:
            _chroma_collection = client.get_collection(name=COLLECTION_NAME)
        except Exception:
            raise RuntimeError(
                f"Chroma collection '{COLLECTION_NAME}' not found. "
                "Run compute_embeddings.py first."
            )
    return _chroma_collection


@trace(span_type="retrieval")
def retrieve(query, top_k=3):
    collection = get_chroma_collection()
    model = get_embedding_model()

    query_embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    mapped_results = []
    if results['ids'] and len(results['ids']) > 0:
        ids = results['ids'][0]
        distances = results['distances'][0]
        documents = results['documents'][0]

        for i in range(len(ids)):
            score = 1.0 - distances[i] if distances[i] is not None else 0.0
            mapped_results.append({
                "id": ids[i],
                "text": documents[i],
                "score": float(score)
            })

    mapped_results.sort(key=lambda x: x["score"], reverse=True)
    return mapped_results


@trace(span_type="generation", evaluate_grounding=True)
def generate_answer(query, retrieved):
    tokenizer, model = get_generation_model_and_tokenizer()

    context = " ".join([doc["text"] for doc in retrieved])

    # Truncate context if needed for flan-t5-small (~512 tokens max usually)
    context_words = context.split()[:300]
    truncated_context = " ".join(context_words)

    prompt = (
        f"Answer the question based on the context.\n"
        f"Context: {truncated_context}\nQuestion: {query}\nAnswer:"
    )

    inputs = tokenizer(
        prompt, return_tensors="pt", max_length=512, truncation=True
    )
    outputs = model.generate(**inputs, max_new_tokens=150)
    generated = tokenizer.decode(outputs[0], skip_special_tokens=True)

    return generated.strip()


@trace(span_type="generic")
def run_pipeline(query):
    retrieved = retrieve(query)
    answer = generate_answer(query, retrieved)

    # Magic! Notice we do not run any hallucination checks here.
    # The ai_observe wrapper automatically grades the generation span behind
    # the scenes.
    return {
        "query": query,
        "retrieved": retrieved,
        "answer": answer
    }

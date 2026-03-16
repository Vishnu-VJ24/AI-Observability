import os
import glob
import pickle
from sentence_transformers import SentenceTransformer

CORPUS_DIR = "corpus"
EMBEDDINGS_FILE = "ai_observe/corpus_embeddings.pkl"
MODEL_NAME = "all-MiniLM-L6-v2"

def load_corpus():
    docs = []
    if not os.path.exists(CORPUS_DIR):
        print(f"Directory {CORPUS_DIR} not found.")
        return docs

    for filepath in glob.glob(os.path.join(CORPUS_DIR, "*.txt")):
        with open(filepath, "r", encoding="utf-8") as f:
            docs.append({"id": os.path.basename(filepath), "text": f.read().strip()})
    return docs

def compute_embeddings():
    print("Loading corpus...")
    docs = load_corpus()
    if not docs:
        print(f"No documents found in {CORPUS_DIR}/")
        return
        
    print(f"Loading model {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    
    texts = [doc["text"] for doc in docs]
    print("Computing embeddings...")
    embeddings = model.encode(texts, show_progress_bar=True)
    
    data = {
        "docs": docs,
        "embeddings": embeddings
    }
    
    os.makedirs(os.path.dirname(EMBEDDINGS_FILE), exist_ok=True)
    with open(EMBEDDINGS_FILE, "wb") as f:
        pickle.dump(data, f)
        
    print(f"Saved {len(docs)} embeddings to {EMBEDDINGS_FILE}")

if __name__ == "__main__":
    compute_embeddings()

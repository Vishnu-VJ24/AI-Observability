import os
import glob
import chromadb
from sentence_transformers import SentenceTransformer

CORPUS_DIR = "corpus"
CHROMA_DB_DIR = "ai_observe/chroma_db"
COLLECTION_NAME = "ai_observability_corpus"
MODEL_NAME = "all-MiniLM-L6-v2"


def load_corpus():
    docs = []
    if not os.path.exists(CORPUS_DIR):
        print(f"Directory {CORPUS_DIR} not found.")
        return docs

    for filepath in glob.glob(os.path.join(CORPUS_DIR, "*.txt")):
        with open(filepath, "r", encoding="utf-8") as f:
            docs.append({
                "id": os.path.basename(filepath),
                "text": f.read().strip()
            })
    return docs


def compute_embeddings():
    print("Loading corpus...")
    docs = load_corpus()
    if not docs:
        print(f"No documents found in {CORPUS_DIR}/")
        return

    print("Loading model " + MODEL_NAME + "...")
    model = SentenceTransformer(MODEL_NAME)

    texts = [doc["text"] for doc in docs]
    print("Computing embeddings...")
    embeddings = model.encode(texts, show_progress_bar=True)
    embeddings_list = embeddings.tolist()

    print("Initializing ChromaDB...")
    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)

    try:
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    ids = [doc["id"] for doc in docs]

    print("Ingesting into ChromaDB...")
    collection.add(
        ids=ids,
        embeddings=embeddings_list,
        documents=texts,
        metadatas=[{"source": doc["id"]} for doc in docs]
    )

    print(f"Saved {len(docs)} documents to ChromaDB at {CHROMA_DB_DIR}")


if __name__ == "__main__":
    compute_embeddings()

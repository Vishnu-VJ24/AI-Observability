Architecture (MVP):
- Gradio (HF Space) frontend presents query UI and trace viewer
- In-process pipeline: embeddings (MiniLM) -> retrieve -> rerank -> generator (Flan-T5) -> judge (similarity)
- Persistence: Chroma/FAISS + SQLite for traces

---
title: AI Observability
emoji: 🪐
colorFrom: purple
colorTo: indigo
sdk: gradio
app_file: app.py
pinned: false
---
# AI Observability — Debugger for LLM Systems

Goal: a free-tier, public demo that captures LLM traces (prompt → retrieval → generation),
detects failures (hallucination, retrieval issues, prompt injection), and surfaces root cause suggestions.

Stack: Python, Gradio (Hugging Face Spaces), sentence-transformers, Chroma/FAISS, Flan-T5-small (CPU).

See /docs for architecture notes, design decisions, and deployment.

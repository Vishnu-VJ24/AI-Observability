@echo off
.venv\Scripts\python.exe -m pip install -r requirements.txt > out.txt 2>&1
.venv\Scripts\python.exe compute_embeddings.py >> out.txt 2>&1

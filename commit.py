import subprocess

try:
    subprocess.check_call(["git", "commit", "-m", "feat(observability): Integrate ChromaDB, Failure Engine, and Root Cause Analyzer"])
    print("Commit successful")
    
    subprocess.check_call(["git", "push"])
    print("Push successful")
except Exception as e:
    print("Error:", str(e))

import sys
import subprocess

print("Python version:", sys.version)

try:
    import chromadb
    print("Chroma is installed")
except ImportError:
    print("Chroma NOT installed")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Finished installing")
    except Exception as e:
        print("Failed to install:", str(e))

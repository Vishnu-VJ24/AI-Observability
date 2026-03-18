import subprocess

try:
    subprocess.check_call(["git", "add", "."])
    print("Add successful")
    subprocess.check_call(["git", "commit", "-m", "fix: flake8 linting errors"])
    print("Commit successful")
except Exception as e:
    print("Error:", str(e))

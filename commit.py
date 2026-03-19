import subprocess

try:
    subprocess.check_call(
        [
            "git",
            "commit",
            "-m",
            "feat(observability): Integrate core components"])
    print("Commit successful")

    subprocess.check_call(["git", "push"])
    print("Push successful")
except Exception as e:
    print("Error:", str(e))

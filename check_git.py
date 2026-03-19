import subprocess


def run_git_cmd(cmd):
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True)
        print(f"--- Output of {' '.join(cmd)} ---")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running {' '.join(cmd)}: {e.stderr}")


if __name__ == "__main__":
    run_git_cmd(["git", "status"])
    run_git_cmd(["git", "log", "-n", "3"])

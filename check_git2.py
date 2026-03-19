import subprocess

try:
    print("Running git status...")
    status = subprocess.check_output(["git", "status"], text=True)
    print(status)

    print("Running git log...")
    log = subprocess.check_output(["git", "log", "-n", "3"], text=True)
    print(log)

    print("Running git diff...")
    diff = subprocess.check_output(["git", "diff"], text=True)
    print("Diff length:", len(diff))

    with open("git_out2.txt", "w", encoding="utf-8") as f:
        f.write("Status:\n")
        f.write(status)
        f.write("\nLog:\n")
        f.write(log)

except Exception as e:
    with open("git_out2.txt", "w", encoding="utf-8") as f:
        f.write(str(e))

class Config:
    project = "default"
    destination = "local"

def init(project: str, destination: str = "local"):
    """Initialize the SDK globally with project settings."""
    Config.project = project
    Config.destination = destination
    print(f"[ai_observe] Attached to project '{project}' tracking to '{destination}'")

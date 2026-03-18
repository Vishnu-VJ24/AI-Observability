import json
from ai_observe.pipeline import run_pipeline

if __name__ == "__main__":
    result = run_pipeline('What is grounding?')
    print(json.dumps(result, indent=2))

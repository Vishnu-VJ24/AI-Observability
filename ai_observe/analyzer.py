import json
import os
import re

TRACE_FILE = "ai_observe/traces.json"

# Heuristics for prompt injection
INJECTION_KEYWORDS = [
    "ignore previous instructions",
    "ignore all prior instructions",
    "disregard previous",
    "you are now",
    "system prompt",
    "bypassing"
]


def detect_failures(pipeline_result):
    """
    Analyzes the output of the RAG pipeline and recent traces
    to detect failures in the system.
    """
    failures = []

    query = pipeline_result.get("query", "").lower()
    retrieved = pipeline_result.get("retrieved", [])
    judgment = pipeline_result.get("judgment", {})
    
    # 1. Prompt Injection Detection
    is_injection = any(keyword in query for keyword in INJECTION_KEYWORDS)
    if is_injection or re.search(
        r"system.*prompt.*(ignore|reveal)", query, re.IGNORECASE
    ):
        failures.append("prompt_injection")

    # 2. Retrieval Failure Detection
    # If the top retrieved document has a low semantic similarity score
    if not retrieved:
        failures.append("retrieval_failure")
    else:
        top_score = max([doc.get("score", 0.0) for doc in retrieved])
        if top_score < 0.15:  # Threshold tuned for MVP embeddings
            failures.append("retrieval_failure")

    # 3. Hallucination Detection
    # If the generated answer has low semantic overlap with retrieved context
    if judgment.get("verdict") == "fail":
        failures.append("hallucination")

    # 4. Latency Anomaly Detection
    # Read traces.json to find the latest execution of run_pipeline
    latency = 0.0
    try:
        if os.path.exists(TRACE_FILE):
            with open(TRACE_FILE, "r") as f:
                traces = json.load(f)
                # Find the most recent run_pipeline trace
                for trace in reversed(traces):
                    if trace.get("function") == "run_pipeline":
                        latency = trace.get("latency_ms", 0.0)
                        break
    except Exception:
        pass

    if latency > 8000.0:  # 8 seconds is abnormally slow for local MVP
        failures.append("latency_anomaly")

    return {
        "failures": failures,
        "metrics": {
            "top_retrieval_score": top_score if retrieved else 0.0,
            "grounding_score": judgment.get("score", 0.0),
            "pipeline_latency_ms": latency
        }
    }


def get_root_causes(failures):
    """
    Maps detected failures to potential root causes and mitigation suggestions.
    """
    diagnostics = {}

    if "prompt_injection" in failures:
        diagnostics["Prompt Injection"] = [
            "User query contained suspicious keywords attempting "
            "to override system behavior.",
            "Action: Implement an intent-classification "
            "guardrail model before the RAG pipeline.",
            "Action: Refuse to answer queries matching known "
            "injection patterns."
        ]

    if "retrieval_failure" in failures:
        diagnostics["Retrieval Failure"] = [
            "Vector database returned context with low semantic "
            "similarity to the query.",
            "Action: Increase chunk overlap or modify chunking sizes.",
            "Action: Evaluate upgrading the embedding model (e.g., "
            "all-MiniLM-L6-v2 -> text-embedding-ada-002).",
            "Action: Implement a Re-ranker to improve top-k relevance."
        ]

    if "hallucination" in failures:
        diagnostics["Hallucination (Low Grounding)"] = [
            "The generated answer did not align with the retrieved context.",
            "Action: Enhance the system prompt to enforce strict adherence "
            "to context ('Say I don't know if not found').",
            "Action: Check if context length exceeded the model's window, "
            "causing it to truncate useful facts.",
            "Action: Tune generation parameters (lower temperature)."
        ]

    if "latency_anomaly" in failures:
        diagnostics["Latency Anomaly"] = [
            "The pipeline execution exceeded the latency threshold (>8000ms).",
            "Action: Profile `generate_answer` vs `retrieve`.",
            "Action: Scale down the LLM size or deploy it on specialized "
            "inferencing hardware (e.g., vLLM or ONNX)."
        ]

    if not failures:
        diagnostics["Healthy"] = [
            "No failures detected. Trace execution is within "
            "expected parameters."
        ]

    return diagnostics


def analyze_trace(pipeline_result):
    """
    Executes the full Failure Detection and Root Cause pipeline.
    """
    detection = detect_failures(pipeline_result)
    root_causes = get_root_causes(detection["failures"])

    return {
        "metrics": detection["metrics"],
        "detected_failures": detection["failures"],
        "diagnostics": root_causes
    }

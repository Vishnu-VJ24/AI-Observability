import time
import json
import uuid
import os
from functools import wraps

from .config import Config
from .state import current_trace_id, current_parent_id, active_traces
from .evaluation import evaluate_hallucination

def _serialize(obj):
    try:
        json.dumps(obj)
        return obj
    except Exception:
        return str(obj)

def trace(span_type="generic", evaluate_grounding=False):
    """
    Production-grade decorator. 
    Intercepts inputs, outputs, builds trace trees, and runs evaluations.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 1. Establish Trace Context
            trace_id = current_trace_id.get()
            is_root_span = False
            
            if trace_id is None:
                trace_id = str(uuid.uuid4())
                current_trace_id.set(trace_id)
                active_traces[trace_id] = []
                is_root_span = True

            parent_id = current_parent_id.get()
            span_id = str(uuid.uuid4())

            # Setting this span as the parent for any downstream calls
            token_parent = current_parent_id.set(span_id)

            start_time = time.time()
            error = None
            status = "success"
            result = None

            # 2. Execute
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                error = str(e)
                status = "error"
                raise
            finally:
                end_time = time.time()
                latency = (end_time - start_time) * 1000

                span_data = {
                    "trace_id": trace_id,
                    "span_id": span_id,
                    "parent_id": parent_id,
                    "span_type": span_type,
                    "function": func.__name__,
                    "inputs": {
                        "args": [_serialize(a) for a in args],
                        "kwargs": {k: _serialize(v) for k, v in kwargs.items()}
                    },
                    "output": _serialize(result) if status == "success" else None,
                    "status": status,
                    "error": error,
                    "latency_ms": latency,
                    "timestamp": start_time
                }

                # 3. Automatic Grounding Evaluation (The Magic)
                if evaluate_grounding and span_type == "generation" and status == "success":
                    spans = active_traces.get(trace_id, [])
                    retrieval_spans = [s for s in spans if s.get("span_type") == "retrieval"]
                    
                    if retrieval_spans:
                        latest_retrieval = retrieval_spans[-1]
                        retrieved_docs = latest_retrieval.get("output", [])
                        eval_result = evaluate_hallucination(result, retrieved_docs)
                        span_data["evaluation"] = eval_result
                    else:
                        span_data["evaluation"] = {
                            "grounded": False, 
                            "score": 0.0, 
                            "reason": "SDK failed to locate a prior 'retrieval' span in this trace."
                        }

                # Save span to memory
                if trace_id in active_traces:
                    active_traces[trace_id].append(span_data)

                # Reset context for the cascade
                current_parent_id.reset(token_parent)

                # 4. Dump entire trace tree if we are the root
                if is_root_span:
                    trace_record = {
                        "project": Config.project,
                        "trace_id": trace_id,
                        "timestamp": start_time,
                        "spans": active_traces[trace_id]
                    }
                    _write_trace(trace_record)
                    
                    # Memory cleanup
                    del active_traces[trace_id]
                    current_trace_id.set(None)

            return result
        return wrapper
    return decorator

def _write_trace(trace_record):
    log_file = "logs.json" if Config.destination == "local" else f"{Config.project}_traces.json"
    traces = []
    
    if os.path.exists(log_file):
        try:
            with open(log_file, "r") as f:
                traces = json.load(f)
        except Exception:
            pass

    traces.append(trace_record)
    with open(log_file, "w") as f:
        json.dump(traces, f, indent=2)

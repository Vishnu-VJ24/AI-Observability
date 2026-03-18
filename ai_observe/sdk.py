import json
import os
import time

TRACE_FILE = "ai_observe/traces.json"


def trace(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            status = "success"
            error = None
        except Exception as e:
            result = None
            status = "error"
            error = str(e)
            raise
        finally:
            end_time = time.time()

            # Basic serialization of args/kwargs for trace
            def serialize(obj):
                try:
                    json.dumps(obj)
                    return obj
                except (TypeError, OverflowError):
                    return str(obj)

            trace_data = {
                "function": func.__name__,
                "args": [serialize(a) for a in args],
                "kwargs": {k: serialize(v) for k, v in kwargs.items()},
                "result": serialize(result) if status == "success" else None,
                "status": status,
                "error": error,
                "latency_ms": (end_time - start_time) * 1000,
                "timestamp": start_time
            }

            os.makedirs(os.path.dirname(TRACE_FILE), exist_ok=True)

            traces = []
            if os.path.exists(TRACE_FILE):
                try:
                    with open(TRACE_FILE, "r") as f:
                        traces = json.load(f)
                except Exception:
                    pass

            traces.append(trace_data)

            with open(TRACE_FILE, "w") as f:
                json.dump(traces, f, indent=2)

        return result
    return wrapper

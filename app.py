import gradio as gr
from ai_observe.pipeline import run_pipeline
import json
import os

# 1. Initialize our shiny new global AI Observability SDK
import ai_observe
ai_observe.init("demo_app", destination="local")

# Auto-build ChromaDB if it doesn't exist (crucial for Hugging Face Spaces
# startup)
if not os.path.exists("ai_observe/chroma_db"):
    print("ChromaDB not found. Generating embeddings automatically...")
    from compute_embeddings import compute_embeddings
    compute_embeddings()


def process_query(query):
    try:
        if not query.strip():
            return "Please enter a query.", "", "", "No data"

        # 2. Run the stripped-down logic pipeline
        result = run_pipeline(query)

        # 3. Prove the Observability works: Read the pure telemetry log to get
        # insights!
        log_file = "logs.json"
        diagnostics_json = "No traces logged."
        verdict = "Verdict: Unknown"

        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                traces = json.load(f)

            latest_trace = traces[-1]
            diagnostics_json = json.dumps(latest_trace, indent=2)

            # Extract auto-evaluation metric from the generation span
            spans = latest_trace.get("spans", [])
            gen_span = next(
                (s for s in spans if s.get("span_type") == "generation"), None)

            if gen_span and "evaluation" in gen_span:
                eval_data = gen_span["evaluation"]
                is_grounded = eval_data.get("grounded", False)
                score = eval_data.get("score", 0.0)
                verdict = f"Verdict: {'Pass' if is_grounded else 'Fail'} (Score: {score:.2f})"

        retrieved_text = json.dumps(result["retrieved"], indent=2)
        answer = result["answer"]

        return retrieved_text, answer, verdict, diagnostics_json
    except Exception as e:
        err = str(e)
        return (
            f"Error: {err}\n\n(Did you run compute_embeddings.py first?)",
            "",
            "Error",
            "Error"
        )


def get_latest_traces():
    try:
        trace_file = "logs.json"
        if os.path.exists(trace_file):
            with open(trace_file, "r") as f:
                traces = json.load(f)
                # Return last 5 traces
                return json.dumps(traces[-5:], indent=2)
    except Exception as e:
        return f"Error loading traces: {str(e)}"
    return "No traces found yet."


with gr.Blocks() as demo:
    gr.Markdown("# AI Observability - Debugger")
    gr.Markdown("Detect hallucination and tracing in an MVP RAG pipeline.")

    with gr.Tab("Pipeline Options"):
        with gr.Row():
            with gr.Column(scale=4):
                query_input = gr.Textbox(
                    label="Query",
                    placeholder="Ask a question about AI observability..."
                )
            with gr.Column(scale=1):
                btn = gr.Button("Run Pipeline", variant="primary")

        with gr.Row():
            with gr.Column(scale=2):
                retrieved_output = gr.Code(
                    label="Retrieved Documents", language="json"
                )
            with gr.Column(scale=2):
                answer_output = gr.Textbox(label="Generated Answer")
                verdict_output = gr.Textbox(label="Grounding Verdict")
            with gr.Column(scale=3):
                diagnostics_output = gr.Code(
                    label="Failure Diagnostics & Root Cause", language="json"
                )

        btn.click(
            process_query,
            inputs=[query_input],
            outputs=[
                retrieved_output,
                answer_output,
                verdict_output,
                diagnostics_output
            ],
            api_name="process_query"
        )
        query_input.submit(
            process_query,
            inputs=[query_input],
            outputs=[
                retrieved_output,
                answer_output,
                verdict_output,
                diagnostics_output
            ],
            api_name="query_submit"
        )

    with gr.Tab("Traces"):
        refresh_btn = gr.Button("Refresh Traces")
        traces_output = gr.Code(
            label="Recent Traces (Last 5 function calls)", language="json"
        )

        refresh_btn.click(
            get_latest_traces,
            inputs=[],
            outputs=[traces_output],
            api_name="get_traces"
        )

if __name__ == "__main__":
    demo.launch()

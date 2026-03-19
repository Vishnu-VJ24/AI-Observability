import gradio as gr
from ai_observe.pipeline import run_pipeline
from ai_observe.analyzer import analyze_trace
import json
import os


def process_query(query):
    try:
        if not query.strip():
            return "Please enter a query.", "", "", "No data"
            
        result = run_pipeline(query)
        analysis = analyze_trace(result)
        
        retrieved_text = json.dumps(result["retrieved"], indent=2)
        answer = result["answer"]
        vdict = result['judgment']['verdict']
        vscore = result['judgment']['score']
        verdict = f"Verdict: {vdict} (Score: {vscore:.2f})"
        
        diagnostics_json = json.dumps(analysis, indent=2)
        
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
        trace_file = "ai_observe/traces.json"
        if os.path.exists(trace_file):
            with open(trace_file, "r") as f:
                traces = json.load(f)
                return json.dumps(traces[-5:], indent=2)  # Return last 5 traces
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

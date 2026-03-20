import { Client } from "https://cdn.jsdelivr.net/npm/@gradio/client/dist/index.min.js";

// ==========================================
// CONFIGURATION
// ==========================================
// IMPORTANT: Update this variable after you deploy your Gradio app to Hugging Face Spaces.
// Example: "vishnu/ai-observability"
const HF_SPACE_ID = "VJ24/ai-observability";

// DOM Elements
const elements = {
    queryInput: document.getElementById('queryInput'),
    runBtn: document.getElementById('runBtn'),
    btnText: document.querySelector('.btn-text'),
    loader: document.querySelector('.loader'),

    refreshTracesBtn: document.getElementById('refreshTracesBtn'),
    tracesOutput: document.getElementById('tracesOutput'),

    retrievedOutput: document.getElementById('retrievedOutput'),
    answerOutput: document.getElementById('answerOutput'),
    verdictOutput: document.getElementById('verdictOutput'),
    latencyOutput: document.getElementById('latencyOutput'),
    diagnosticsOutput: document.getElementById('diagnosticsOutput'),

    setupAlert: document.getElementById('setupAlert')
};

// State
let client = null;

async function initClient() {
    if (HF_SPACE_ID.includes("YOUR_HF_USERNAME")) {
        // Just mock it until they actually hook it up
        return null;
    }

    try {
        client = await Client.connect(HF_SPACE_ID);
        elements.setupAlert.style.display = 'none';
        return client;
    } catch (e) {
        console.error("Failed to connect to Hugging Face Space:", e);
        return null;
    }
}

function setLoading(isLoading) {
    if (isLoading) {
        elements.btnText.textContent = "Processing...";
        elements.loader.classList.remove('hidden');
        elements.runBtn.disabled = true;
    } else {
        elements.btnText.textContent = "Execute Chain";
        elements.loader.classList.add('hidden');
        elements.runBtn.disabled = false;
    }
}

async function runPipeline() {
    const query = elements.queryInput.value.trim();
    if (!query) return;

    setLoading(true);
    const startTime = performance.now();

    try {
        if (!client) {
            // Mock response if backend is not linked yet
            await simulateExecution();
            return;
        }

        // Call our explicitly named API endpoint
        const result = await client.predict("/process_query", {
            query: query
        });

        const [retrievedText, answerText, verdictText, diagnosticsJSON] = result.data;

        // Update UI
        elements.answerOutput.textContent = answerText;
        renderRetrievedDocs(retrievedText);
        renderDiagnostics(diagnosticsJSON);

        // Parse verdict
        updateVerdictUI(verdictText);

    } catch (e) {
        console.error("Pipeline Error:", e);
        elements.answerOutput.textContent = "Error: Failed to fetch from backend. Check console.";
    } finally {
        const latency = Math.round(performance.now() - startTime);
        elements.latencyOutput.textContent = `${latency} ms`;
        setLoading(false);
        fetchTraces(); // Auto refresh traces
    }
}

async function fetchTraces() {
    elements.refreshTracesBtn.style.transform = "rotate(180deg)";
    setTimeout(() => { elements.refreshTracesBtn.style.transform = "rotate(0deg)"; }, 300);

    try {
        if (!client) {
            elements.tracesOutput.textContent = "// Traces mock (Backend not connected)";
            return;
        }

        const result = await client.predict("/get_traces", {});
        renderRecentTraces(result.data[0]);
    } catch (e) {
        console.error("Traces Error:", e);
        elements.tracesOutput.textContent = "// Failed to load traces.";
    }
}

function updateVerdictUI(verdictText) {
    // Example format: "Verdict: pass (Score: 0.85)"
    elements.verdictOutput.textContent = verdictText;
    elements.verdictOutput.className = "value-badge";

    if (verdictText.toLowerCase().includes('pass')) {
        elements.verdictOutput.classList.add('pass');
    } else if (verdictText.toLowerCase().includes('fail')) {
        elements.verdictOutput.classList.add('fail');
    }
}

function renderRetrievedDocs(jsonStr) {
    try {
        const docs = JSON.parse(jsonStr);
        if (!docs || docs.length === 0) {
            elements.retrievedOutput.innerHTML = '<div class="empty-state">No context retrieved</div>';
            return;
        }
        elements.retrievedOutput.innerHTML = docs.map((d, i) => `
            <div class="doc-card">
                <div class="doc-header">
                    <span class="doc-id">📄 Chunk ${i + 1}</span>
                    <span class="doc-score">Score: ${d.score ? d.score.toFixed(3) : 'N/A'}</span>
                </div>
                <p class="doc-text">"${d.text ? d.text.substring(0, 150) : ''}..."</p>
            </div>
        `).join('');
    } catch(e) {
        elements.retrievedOutput.textContent = jsonStr;
    }
}

function renderDiagnostics(jsonStr) {
    try {
        const trace = JSON.parse(jsonStr);
        if (!trace || !trace.spans) {
            elements.diagnosticsOutput.innerHTML = '<div class="empty-state">No diagnostic data</div>';
            return;
        }
        
        elements.diagnosticsOutput.innerHTML = `
            <div class="trace-overview">
                <div class="metric"><span class="label">Trace ID</span> <span class="val">${trace.trace_id.substring(0,8)}</span></div>
                <div class="metric"><span class="label">Project</span> <span class="val">${trace.project}</span></div>
            </div>
            <div class="spans-list">
                ${trace.spans.map(s => `
                    <div class="span-item status-${s.status}">
                        <div class="span-header">
                            <span class="span-name">⚡ ${s.function} <span class="span-type">(${s.span_type})</span></span>
                            <span class="span-latency">${s.latency_ms.toFixed(1)}ms</span>
                        </div>
                        ${s.evaluation ? `
                            <div class="span-eval">
                                <span class="eval-badge ${s.evaluation.grounded ? 'pass' : 'fail'}">
                                    ${s.evaluation.grounded ? 'Grounded' : 'Hallucination'}
                                </span>
                                <span class="eval-score">Confidence: ${s.evaluation.score.toFixed(2)}</span>
                            </div>
                        ` : ''}
                        ${s.error ? `<div class="span-error">❌ ${s.error}</div>` : ''}
                    </div>
                `).join('')}
            </div>
        `;
    } catch(e) {
        elements.diagnosticsOutput.textContent = jsonStr;
    }
}

function renderRecentTraces(jsonStr) {
    try {
        const traces = JSON.parse(jsonStr);
        if (!traces || traces.length === 0) {
            elements.tracesOutput.innerHTML = '<div class="empty-state">No recent traces found.</div>';
            return;
        }
        
        // Reverse so newest is first
        const reversed = [...traces].reverse();
        
        elements.tracesOutput.innerHTML = reversed.map(t => {
            const numSpans = t.spans ? t.spans.length : 0;
            const evalSpans = t.spans ? t.spans.filter(s => s.evaluation) : [];
            const hasHallucination = evalSpans.some(s => !s.evaluation.grounded);
            
            return `
            <div class="trace-card ${hasHallucination ? 'trace-alert' : ''}">
                <div class="trace-header">
                    <span class="trace-id">Trace #${t.trace_id.substring(0,6)}</span>
                    <span class="trace-spans">${numSpans} spans</span>
                </div>
                ${hasHallucination ? '<div class="trace-warning">⚠️ Hallucination Detected</div>' : ''}
            </div>
        `}).join('');
    } catch(e) {
        elements.tracesOutput.textContent = jsonStr;
    }
}

async function simulateExecution() {
    await new Promise(r => setTimeout(r, 1500));
    
    renderRetrievedDocs(JSON.stringify([
        { "id": "mock", "text": "This is mock data because HF backend is not connected.", "score": 0.95 }
    ]));
    
    elements.answerOutput.textContent = "This is a frontend demonstration. Setup the Hugging Face space pointing to your repository, then place the space ID in app.js to go live.";
    updateVerdictUI("Verdict: pass (Score: 0.99) [MOCK]");
    
    renderDiagnostics(JSON.stringify({
        project: "demo",
        trace_id: "mock12345",
        spans: [{ function: "mock_execution", span_type: "generic", latency_ms: 120, status: "success" }]
    }));
}

// Event Listeners
elements.runBtn.addEventListener('click', runPipeline);
elements.refreshTracesBtn.addEventListener('click', fetchTraces);

elements.queryInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        runPipeline();
    }
});

document.addEventListener('DOMContentLoaded', () => {
    initClient();
});

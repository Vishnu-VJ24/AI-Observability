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
        elements.retrievedOutput.textContent = retrievedText;
        elements.answerOutput.textContent = answerText;
        elements.diagnosticsOutput.textContent = diagnosticsJSON;
        
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
        elements.tracesOutput.textContent = result.data[0];
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

async function simulateExecution() {
    // A mock response to demonstrate UI if the user hasn't connected HF yet.
    await new Promise(r => setTimeout(r, 1500));
    
    elements.retrievedOutput.textContent = JSON.stringify([
        {"id": "mock_id", "text": "This is mock data because HF backend is not connected.", "score": 0.9}
    ], null, 2);
    
    elements.answerOutput.textContent = "This is a frontend demonstration. Setup the Hugging Face space pointing to your repository, then place the space ID in app.js to go live.";
    
    updateVerdictUI("Verdict: pass (Score: 0.99) [MOCK]");
    
    elements.diagnosticsOutput.textContent = JSON.stringify({
        "status": "success",
        "mock": true
    }, null, 2);
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

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initClient();
});

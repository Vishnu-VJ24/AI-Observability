import pytest
from ai_observe.pipeline import retrieve, judge_grounding

def test_retrieve():
    try:
        results = retrieve("What is AI observability?", top_k=2)
        assert isinstance(results, list)
        if len(results) > 0:
            assert "id" in results[0]
            assert "text" in results[0]
            assert "score" in results[0]
    except RuntimeError:
        pytest.skip("Embeddings not computed yet. Run compute_embeddings.py to test retrieve().")

def test_judge_grounding():
    # Provide a simple test to ensure judge_grounding returns expected structure
    answer = "Tracing is a method to monitor request execution."
    retrieved = [
        {"id": "doc8.txt", "text": "Tracing is the process of monitoring the execution of a request through various components of an application.", "score": 0.9}
    ]
    
    result = judge_grounding(answer, retrieved)
    assert isinstance(result, dict)
    assert "verdict" in result
    assert "score" in result
    assert "reason" in result

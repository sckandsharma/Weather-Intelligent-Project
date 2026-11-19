from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.evaluation.metrics import (
    compute_answer_score,
    compute_retrieval_score,
    compute_routing_score,
)
from app.llm.prompts import DocumentSource, WeatherSource


def test_metric_routing_score():
    # Exact match
    assert compute_routing_score("weather", "weather", "Delhi", "Delhi") == 1.0
    # Location mismatch partial credit
    assert compute_routing_score("weather", "weather", None, "Delhi") == 0.85
    # Route mismatch but location match
    assert compute_routing_score("both", "weather", "Delhi", "Delhi") == 0.20
    # Complete mismatch
    assert compute_routing_score("neither", "weather", None, "Delhi") == 0.0


def test_metric_retrieval_score():
    # Route not expecting RAG -> None
    assert compute_retrieval_score("weather", [], [], []) is None

    # RAG route with matching category and valid citations
    doc_sources = [
        DocumentSource(title="NDMA Heatwave Guide", source_url="https://ndma.gov.in/heat", category="heatwave")
    ]
    score = compute_retrieval_score(
        expected_route="rag",
        retrieved_chunks=[],
        expected_categories=["heatwave"],
        document_sources=doc_sources,
    )
    assert score == 1.0


def test_metric_answer_score():
    # Alert disclaimer verification
    ans_with_disclaimer = "Currently conditions are overcast. Note: This forecast is not an official government alert."
    score = compute_answer_score(
        answer=ans_with_disclaimer,
        expected_keywords=["conditions"],
        expected_route="weather",
        needs_official_alert=True,
        weather_sources=[WeatherSource(endpoint="url", city="Mumbai")],
        document_sources=[],
    )
    assert score >= 0.80


def test_evaluation_api_endpoints(client: TestClient, evaluator_headers, user_headers):
    # Non-evaluator role blocked -> 403
    unauth = client.get("/api/v1/evaluation/results", headers=user_headers)
    assert unauth.status_code == 403

    # Evaluator role allowed -> 200
    res = client.get("/api/v1/evaluation/results", headers=evaluator_headers)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data

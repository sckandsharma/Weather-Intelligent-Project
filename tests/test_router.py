import json
from pathlib import Path
import pytest

from app.llm.router import RouteSource, route_query

DATASET_PATH = Path(__file__).resolve().parent.parent / "app" / "evaluation" / "dataset.json"


def test_word_boundary_edge_cases():
    # 'training' must not match 'rain'
    res1 = route_query("The corporate training session is at noon.")
    assert res1.source == RouteSource.NEITHER

    # 'hotel' must not match 'hot'
    res2 = route_query("Book a luxury hotel room in Paris.")
    assert res2.source == RouteSource.NEITHER

    # 'livestock' must not trigger out-of-scope 'stock'
    res3 = route_query("What precautions should be taken for livestock during Delhi's heatwave?")
    assert res3.source == RouteSource.BOTH
    assert res3.location == "Delhi"

    # 'required' must not match alert 'red'
    res4 = route_query("What precautions are required in a flood?")
    assert res4.source == RouteSource.RAG


def test_missing_location_gives_clarification():
    res = route_query("Will it rain tomorrow?")
    assert res.source == RouteSource.CLARIFICATION
    assert res.location is None

    res2 = route_query("What precautions should I take tomorrow?")
    assert res2.source == RouteSource.CLARIFICATION


def test_out_of_scope_gives_neither():
    res = route_query("Tell me Apple's latest stock price.")
    assert res.source == RouteSource.NEITHER
    assert res.is_out_of_scope is True


def test_15_official_assignment_dataset_questions():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    for item in dataset:
        q = item["question"]
        expected = item.get("expected_route") or item.get("expected_source")
        decision = route_query(q)
        assert decision.source.value == expected, f"Failed on Q#{item['id']}: '{q}'. Expected {expected}, got {decision.source.value}"

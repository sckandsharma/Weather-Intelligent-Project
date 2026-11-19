from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.llm.generator import LLMResult
from app.weather.client import WeatherClientResult
from app.weather.geocoding import GeoLocation, LocationNotFoundError


def test_out_of_scope_fast_path(client: TestClient, user_headers):
    payload = {"message": "Tell me Apple's latest stock price."}
    res = client.post("/api/v1/chat/ask", json=payload, headers=user_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["routing_decision"] == "neither"
    assert "specialized exclusively in weather" in data["answer"].lower()
    assert data["weather_sources"] == []
    assert data["document_sources"] == []


def test_clarification_fast_path(client: TestClient, user_headers):
    payload = {"message": "What precautions should I take tomorrow?"}
    res = client.post("/api/v1/chat/ask", json=payload, headers=user_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["routing_decision"] == "clarification"
    assert "specify" in data["answer"].lower()


def test_weather_failure_returns_clear_message(client: TestClient, user_headers):
    # Test misspelled city returns clear message, not invented weather numbers
    with patch("app.weather.service.geocode_city", side_effect=LocationNotFoundError("Delhii")):
        payload = {"message": "What's the weather in Delhii?"}
        res = client.post("/api/v1/chat/ask", json=payload, headers=user_headers)
        assert res.status_code == 200
        data = res.json()
        assert "could not be resolved" in data["answer"].lower()
        assert data["weather_sources"] == []


def test_chat_end_to_end_success(client: TestClient, user_headers):
    mock_loc = GeoLocation(name="Delhi", latitude=28.61, longitude=77.20, timezone="Asia/Kolkata")
    mock_weather = WeatherClientResult(
        response_json={
            "current": {"temperature_2m": 32.0, "relative_humidity_2m": 40, "wind_speed_10m": 10, "weather_code": 0},
            "hourly": {"time": ["2026-11-19T14:00"], "precipitation_probability": [0], "uv_index": [5]},
            "timezone": "Asia/Kolkata",
        },
        status_code=200,
        latency_ms=95.0,
        request_params={},
    )
    mock_llm = LLMResult(
        content="Current temperature in Delhi is 32.0°C under clear skies.",
        latency_ms=350,
        finish_reason="STOP",
        total_tokens=60,
    )

    with patch("app.weather.service.geocode_city", return_value=mock_loc), \
         patch("app.weather.service.fetch_current_weather", return_value=mock_weather), \
         patch("app.services.chat_service.generate_response", new_callable=AsyncMock, return_value=mock_llm):

        payload = {"message": "What's the temperature in Delhi?"}
        res = client.post("/api/v1/chat/ask", json=payload, headers=user_headers)
        assert res.status_code == 200
        data = res.json()

        assert data["routing_decision"] == "weather"
        assert "32.0°c" in data["answer"].lower()
        assert data["confidence"] == "high"
        assert len(data["weather_sources"]) >= 1
        assert data["weather_sources"][0]["city"] == "Delhi"
        assert data["conversation_id"] > 0
        assert data["message_id"] > 0

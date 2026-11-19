from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import WeatherAPILog
from app.services.cache_service import cache_service
from app.weather.client import WeatherAPIError, WeatherClientResult
from app.weather.geocoding import GeoLocation, LocationNotFoundError
from app.weather.service import (
    InvalidDateRangeError,
    get_current_weather,
    get_daily_forecast,
    get_hourly_forecast,
    validate_forecast_days,
    validate_target_date,
)


def test_geocoding_success_and_weather_call(db: Session):
    cache_service.flush()
    mock_loc = GeoLocation(name="Delhi", latitude=28.61, longitude=77.20, timezone="Asia/Kolkata")
    mock_result = WeatherClientResult(
        response_json={
            "current": {"temperature_2m": 31.5, "relative_humidity_2m": 45, "wind_speed_10m": 12, "weather_code": 0},
            "hourly": {"time": ["2026-11-19T10:00"], "precipitation_probability": [5], "uv_index": [4]},
            "timezone": "Asia/Kolkata",
        },
        status_code=200,
        latency_ms=115.0,
        request_params={"latitude": 28.61, "longitude": 77.20},
    )

    with patch("app.weather.service.geocode_city", return_value=mock_loc), \
         patch("app.weather.service.fetch_current_weather", return_value=mock_result):
        data = get_current_weather("Delhi", db=db)
        assert data["temperature_c"] == 31.5
        assert data["location"]["city"] == "Delhi"

        # Verify call was logged to weather_api_logs table
        log_entry = db.scalar(select(WeatherAPILog).where(WeatherAPILog.city == "Delhi").order_by(WeatherAPILog.id.desc()))
        assert log_entry is not None
        assert log_entry.status_code == 200


def test_misspelled_city_delhii_and_logging(db: Session):
    with patch("app.weather.service.geocode_city", side_effect=LocationNotFoundError("Delhii")):
        with pytest.raises(LocationNotFoundError):
            get_current_weather("Delhii", db=db)

        # Verify error log was persisted
        log_entry = db.scalar(select(WeatherAPILog).where(WeatherAPILog.city == "Delhii"))
        assert log_entry is not None
        assert log_entry.status_code == 404


def test_weather_api_timeout_and_5xx(db: Session):
    mock_loc = GeoLocation(name="Mumbai", latitude=19.07, longitude=72.87, timezone="Asia/Kolkata")
    with patch("app.weather.service.geocode_city", return_value=mock_loc), \
         patch("app.weather.service.fetch_current_weather", side_effect=WeatherAPIError("Timeout communicating with Open-Meteo", status_code=504)):
        with pytest.raises(WeatherAPIError) as exc_info:
            get_current_weather("Mumbai", db=db)
        assert exc_info.value.status_code == 504


def test_date_validation_beyond_range():
    with pytest.raises(InvalidDateRangeError):
        validate_forecast_days(17)

    with pytest.raises(InvalidDateRangeError):
        validate_target_date("2099-01-01")


def test_weather_cache_hit_and_miss(db: Session):
    cache_service.flush()
    mock_loc = GeoLocation(name="Pune", latitude=18.52, longitude=73.85, timezone="Asia/Kolkata")
    mock_result = WeatherClientResult(
        response_json={
            "current": {"temperature_2m": 26.0, "relative_humidity_2m": 60, "wind_speed_10m": 8, "weather_code": 1},
            "hourly": {"time": ["2026-11-19T10:00"], "precipitation_probability": [10], "uv_index": [3]},
            "timezone": "Asia/Kolkata",
        },
        status_code=200,
        latency_ms=80.0,
        request_params={"latitude": 18.52, "longitude": 73.85},
    )

    with patch("app.weather.service.geocode_city", return_value=mock_loc) as mock_geo, \
         patch("app.weather.service.fetch_current_weather", return_value=mock_result) as mock_fetch:
        
        # 1st call -> Cache MISS (triggers geocoding + fetch)
        res1 = get_current_weather("Pune", db=db)
        assert res1["temperature_c"] == 26.0
        assert mock_fetch.call_count == 1

        # 2nd call -> Cache HIT (returns immediately without calling fetch)
        res2 = get_current_weather("Pune", db=db)
        assert res2["temperature_c"] == 26.0
        assert mock_fetch.call_count == 1  # Still 1, proving cache hit


def test_weather_endpoints_jwt_protected(client: TestClient, user_headers: dict[str, str]):
    # Unauthorized request -> 401
    unauth = client.get("/api/v1/weather/current?city=Delhi")
    assert unauth.status_code == 401

    # Authorized request with mock
    mock_loc = GeoLocation(name="Delhi", latitude=28.61, longitude=77.20, timezone="Asia/Kolkata")
    mock_result = WeatherClientResult(
        response_json={
            "current": {"temperature_2m": 29.0, "relative_humidity_2m": 50, "wind_speed_10m": 10, "weather_code": 0},
            "hourly": {"time": ["2026-11-19T12:00"], "precipitation_probability": [0], "uv_index": [5]},
            "timezone": "Asia/Kolkata",
        },
        status_code=200,
        latency_ms=90.0,
        request_params={"latitude": 28.61, "longitude": 77.20},
    )

    with patch("app.weather.service.geocode_city", return_value=mock_loc), \
         patch("app.weather.service.fetch_current_weather", return_value=mock_result):
        resp = client.get("/api/v1/weather/current?city=Delhi", headers=user_headers)
        assert resp.status_code == 200
        assert resp.json()["temperature_c"] == 29.0

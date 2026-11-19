import time
from typing import Any
import httpx
from pydantic import BaseModel

from app.core.config import settings


class WeatherAPIError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        latency_ms: float = 0.0,
        request_params: dict[str, Any] | None = None,
        response_json: dict[str, Any] | None = None,
        is_timeout: bool = False,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.latency_ms = latency_ms
        self.request_params = request_params or {}
        self.response_json = response_json
        self.is_timeout = is_timeout


class WeatherClientResult(BaseModel):
    request_params: dict[str, Any]
    response_json: dict[str, Any]
    status_code: int
    latency_ms: float


def _call_open_meteo(
    params: dict[str, Any],
    timeout: float = 10.0,
) -> WeatherClientResult:
    url = f"{settings.WEATHER_API_BASE_URL.rstrip('/')}/forecast"
    start = time.perf_counter()

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(url, params=params)
            latency_ms = (time.perf_counter() - start) * 1000
            response.raise_for_status()
            data = response.json()
            return WeatherClientResult(
                request_params=params,
                response_json=data,
                status_code=response.status_code,
                latency_ms=latency_ms,
            )
    except httpx.TimeoutException as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        raise WeatherAPIError(
            "Live weather service timed out. Live weather data is currently unavailable.",
            status_code=504,
            latency_ms=latency_ms,
            request_params=params,
            response_json={"error": "timeout"},
            is_timeout=True,
        ) from exc
    except httpx.HTTPStatusError as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        try:
            error_body = exc.response.json()
        except Exception:
            error_body = {"error": exc.response.text}
        raise WeatherAPIError(
            f"Live weather service returned HTTP {exc.response.status_code}.",
            status_code=exc.response.status_code,
            latency_ms=latency_ms,
            request_params=params,
            response_json=error_body,
        ) from exc
    except httpx.RequestError as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        raise WeatherAPIError(
            "Unable to reach the live weather service.",
            status_code=502,
            latency_ms=latency_ms,
            request_params=params,
            response_json={"error": str(exc)},
        ) from exc


def fetch_current_weather(
    latitude: float,
    longitude: float,
    timezone: str = "auto",
    timeout: float = 10.0,
) -> WeatherClientResult:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
        "hourly": "precipitation_probability,uv_index",
        "forecast_days": 1,
        "timezone": timezone,
    }
    return _call_open_meteo(params, timeout=timeout)


def fetch_daily_forecast(
    latitude: float,
    longitude: float,
    days: int = 3,
    timezone: str = "auto",
    timeout: float = 10.0,
) -> WeatherClientResult:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max,uv_index_max",
        "forecast_days": days,
        "timezone": timezone,
    }
    return _call_open_meteo(params, timeout=timeout)


def fetch_hourly_forecast(
    latitude: float,
    longitude: float,
    days: int = 2,
    timezone: str = "auto",
    timeout: float = 10.0,
) -> WeatherClientResult:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,wind_speed_10m,uv_index,weather_code",
        "forecast_days": days,
        "timezone": timezone,
    }
    return _call_open_meteo(params, timeout=timeout)
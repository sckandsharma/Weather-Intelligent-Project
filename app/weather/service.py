from datetime import date, timedelta
from typing import Any
from sqlalchemy.orm import Session

from app.services.cache_service import cache_service
from app.services.logging_service import log_weather_api_call
from app.weather.client import (
    WeatherAPIError,
    fetch_current_weather,
    fetch_daily_forecast,
    fetch_hourly_forecast,
)
from app.weather.geocoding import (
    GeocodingAPIError,
    LocationNotFoundError,
    geocode_city,
)

MAX_FORECAST_DAYS = 16
MAX_HOURLY_HOURS = 168

WMO_WEATHER_CODES: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class InvalidDateRangeError(Exception):
    pass


def decode_weather_code(code: int | None) -> str:
    if code is None:
        return "Unknown"
    return WMO_WEATHER_CODES.get(code, f"Weather code {code}")


def validate_forecast_days(days: int) -> int:
    if days < 1 or days > MAX_FORECAST_DAYS:
        raise InvalidDateRangeError(
            f"Forecast days must be between 1 and {MAX_FORECAST_DAYS}. Requested: {days}."
        )
    return days


def validate_target_date(target_date: str | None) -> date | None:
    if not target_date:
        return None

    normalized = target_date.strip().lower()
    today = date.today()

    if normalized in {"today", "now", "tonight", "this evening", "this morning"}:
        return today
    if normalized == "tomorrow":
        return today + timedelta(days=1)
    if normalized in {"day after tomorrow", "overmorrow"}:
        return today + timedelta(days=2)

    try:
        parsed = date.fromisoformat(normalized)
    except ValueError as exc:
        raise InvalidDateRangeError(
            f"Invalid date format '{target_date}'. Expected YYYY-MM-DD or relative terms like 'today'/'tomorrow'."
        ) from exc

    max_date = today + timedelta(days=MAX_FORECAST_DAYS - 1)
    if parsed < today or parsed > max_date:
        raise InvalidDateRangeError(
            f"Date '{parsed.isoformat()}' is outside the supported Open-Meteo forecast range ({today.isoformat()} to {max_date.isoformat()})."
        )
    return parsed


def _resolve_location(city: str, db: Session | None) -> Any:
    try:
        return geocode_city(city)
    except LocationNotFoundError as exc:
        if db is not None:
            log_weather_api_call(
                db=db,
                city=city,
                request_params={"step": "geocoding", "city": city},
                response_json={"error": str(exc)},
                status_code=404,
                latency_ms=0.0,
            )
        raise
    except GeocodingAPIError as exc:
        if db is not None:
            log_weather_api_call(
                db=db,
                city=city,
                request_params={"step": "geocoding", "city": city},
                response_json={"error": str(exc)},
                status_code=exc.status_code,
                latency_ms=0.0,
            )
        raise


def get_current_weather(city: str, db: Session | None = None) -> dict[str, Any]:
    cache_key = f"weather:current:{city.strip().lower()}"
    cached = cache_service.get(cache_key)
    if cached is not None:
        cached_copy = dict(cached)
        cached_copy["cached"] = True
        return cached_copy

    location = _resolve_location(city, db)

    try:
        result = fetch_current_weather(
            latitude=location.latitude,
            longitude=location.longitude,
            timezone=location.timezone,
        )
    except WeatherAPIError as exc:
        if db is not None:
            log_weather_api_call(
                db=db,
                city=location.name,
                request_params=exc.request_params,
                response_json=exc.response_json,
                status_code=exc.status_code,
                latency_ms=exc.latency_ms,
            )
        raise

    if db is not None:
        log_weather_api_call(
            db=db,
            city=location.name,
            request_params=result.request_params,
            response_json=result.response_json,
            status_code=result.status_code,
            latency_ms=result.latency_ms,
        )

    data = result.response_json
    current = data.get("current", {})
    hourly = data.get("hourly", {})
    hourly_times = hourly.get("time", [])
    current_time = current.get("time", "")

    hour_idx = 0
    if current_time and hourly_times:
        prefix = current_time[:13]
        for idx, t in enumerate(hourly_times):
            if t.startswith(prefix):
                hour_idx = idx
                break

    rain_probs = hourly.get("precipitation_probability", [])
    uv_indices = hourly.get("uv_index", [])

    payload = {
        "source": "Open-Meteo",
        "data_type": "current",
        "location": {
            "city": location.name,
            "region": location.admin1,
            "country": location.country,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "timezone": data.get("timezone", location.timezone),
        },
        "observed_at": current_time,
        "temperature_c": current.get("temperature_2m"),
        "humidity_percent": current.get("relative_humidity_2m"),
        "wind_speed_kmh": current.get("wind_speed_10m"),
        "precipitation_mm": current.get("precipitation"),
        "rain_probability_percent": rain_probs[hour_idx] if hour_idx < len(rain_probs) else None,
        "uv_index": uv_indices[hour_idx] if hour_idx < len(uv_indices) else None,
        "weather_code": current.get("weather_code"),
        "weather_condition": decode_weather_code(current.get("weather_code")),
        "latency_ms": round(result.latency_ms, 2),
        "cached": False,
    }
    cache_service.set(cache_key, payload, ttl_seconds=600)
    return payload


def get_daily_forecast(
    city: str,
    days: int = 3,
    db: Session | None = None,
) -> dict[str, Any]:
    validated_days = validate_forecast_days(days)
    cache_key = f"weather:daily:{city.strip().lower()}:{validated_days}"
    cached = cache_service.get(cache_key)
    if cached is not None:
        cached_copy = dict(cached)
        cached_copy["cached"] = True
        return cached_copy

    location = _resolve_location(city, db)

    try:
        result = fetch_daily_forecast(
            latitude=location.latitude,
            longitude=location.longitude,
            days=validated_days,
            timezone=location.timezone,
        )
    except WeatherAPIError as exc:
        if db is not None:
            log_weather_api_call(
                db=db,
                city=location.name,
                request_params=exc.request_params,
                response_json=exc.response_json,
                status_code=exc.status_code,
                latency_ms=exc.latency_ms,
            )
        raise

    if db is not None:
        log_weather_api_call(
            db=db,
            city=location.name,
            request_params=result.request_params,
            response_json=result.response_json,
            status_code=result.status_code,
            latency_ms=result.latency_ms,
        )

    data = result.response_json
    daily = data.get("daily", {})
    dates = daily.get("time", [])
    temp_max = daily.get("temperature_2m_max", [])
    temp_min = daily.get("temperature_2m_min", [])
    rain_prob = daily.get("precipitation_probability_max", [])
    wind_max = daily.get("wind_speed_10m_max", [])
    uv_max = daily.get("uv_index_max", [])
    codes = daily.get("weather_code", [])

    forecast_days = []
    for i, day_str in enumerate(dates):
        code = codes[i] if i < len(codes) else None
        forecast_days.append(
            {
                "date": day_str,
                "temperature_min_c": temp_min[i] if i < len(temp_min) else None,
                "temperature_max_c": temp_max[i] if i < len(temp_max) else None,
                "rain_probability_max_percent": rain_prob[i] if i < len(rain_prob) else None,
                "wind_speed_max_kmh": wind_max[i] if i < len(wind_max) else None,
                "uv_index_max": uv_max[i] if i < len(uv_max) else None,
                "weather_code": code,
                "weather_condition": decode_weather_code(code),
            }
        )

    payload = {
        "source": "Open-Meteo",
        "data_type": "daily_forecast",
        "location": {
            "city": location.name,
            "region": location.admin1,
            "country": location.country,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "timezone": data.get("timezone", location.timezone),
        },
        "days_requested": validated_days,
        "forecast": forecast_days,
        "latency_ms": round(result.latency_ms, 2),
        "cached": False,
    }
    cache_service.set(cache_key, payload, ttl_seconds=600)
    return payload


def get_hourly_forecast(
    city: str,
    hours: int = 24,
    db: Session | None = None,
) -> dict[str, Any]:
    if hours < 1 or hours > MAX_HOURLY_HOURS:
        raise InvalidDateRangeError(
            f"Hourly forecast hours must be between 1 and {MAX_HOURLY_HOURS}. Requested: {hours}."
        )

    cache_key = f"weather:hourly:{city.strip().lower()}:{hours}"
    cached = cache_service.get(cache_key)
    if cached is not None:
        cached_copy = dict(cached)
        cached_copy["cached"] = True
        return cached_copy

    days_needed = min(MAX_FORECAST_DAYS, max(1, (hours + 23) // 24 + 1))
    location = _resolve_location(city, db)

    try:
        result = fetch_hourly_forecast(
            latitude=location.latitude,
            longitude=location.longitude,
            days=days_needed,
            timezone=location.timezone,
        )
    except WeatherAPIError as exc:
        if db is not None:
            log_weather_api_call(
                db=db,
                city=location.name,
                request_params=exc.request_params,
                response_json=exc.response_json,
                status_code=exc.status_code,
                latency_ms=exc.latency_ms,
            )
        raise

    if db is not None:
        log_weather_api_call(
            db=db,
            city=location.name,
            request_params=result.request_params,
            response_json=result.response_json,
            status_code=result.status_code,
            latency_ms=result.latency_ms,
        )

    data = result.response_json
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])[:hours]
    temps = hourly.get("temperature_2m", [])
    humidities = hourly.get("relative_humidity_2m", [])
    rain_probs = hourly.get("precipitation_probability", [])
    winds = hourly.get("wind_speed_10m", [])
    uvs = hourly.get("uv_index", [])
    codes = hourly.get("weather_code", [])

    hourly_items = []
    for i, ts in enumerate(times):
        code = codes[i] if i < len(codes) else None
        hourly_items.append(
            {
                "time": ts,
                "temperature_c": temps[i] if i < len(temps) else None,
                "humidity_percent": humidities[i] if i < len(humidities) else None,
                "rain_probability_percent": rain_probs[i] if i < len(rain_probs) else None,
                "wind_speed_kmh": winds[i] if i < len(winds) else None,
                "uv_index": uvs[i] if i < len(uvs) else None,
                "weather_code": code,
                "weather_condition": decode_weather_code(code),
            }
        )

    payload = {
        "source": "Open-Meteo",
        "data_type": "hourly_forecast",
        "location": {
            "city": location.name,
            "region": location.admin1,
            "country": location.country,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "timezone": data.get("timezone", location.timezone),
        },
        "hours_requested": hours,
        "hourly": hourly_items,
        "latency_ms": round(result.latency_ms, 2),
        "cached": False,
    }
    cache_service.set(cache_key, payload, ttl_seconds=600)
    return payload
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.models import User
from app.database.session import get_db
from app.weather.client import WeatherAPIError
from app.weather.geocoding import GeocodingAPIError, LocationNotFoundError
from app.weather.service import (
    InvalidDateRangeError,
    get_current_weather,
    get_daily_forecast,
    get_hourly_forecast,
)

router = APIRouter(prefix="/weather", tags=["Weather"])


def _handle_weather_error(exc: Exception) -> HTTPException:
    if isinstance(exc, InvalidDateRangeError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    if isinstance(exc, LocationNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    if isinstance(exc, (GeocodingAPIError, WeatherAPIError)):
        code = (
            status.HTTP_504_GATEWAY_TIMEOUT
            if exc.is_timeout
            else status.HTTP_502_BAD_GATEWAY
        )
        return HTTPException(status_code=code, detail=str(exc))
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Unexpected weather service error",
    )


@router.get("/current")
def current_weather(
    city: str = Query(..., min_length=1, description="City name (e.g., Delhi)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        return get_current_weather(city=city, db=db)
    except Exception as exc:
        raise _handle_weather_error(exc)


@router.get("/forecast")
def weather_forecast(
    city: str = Query(..., min_length=1, description="City name (e.g., Manali)"),
    days: int = Query(3, description="Number of forecast days (1 to 16)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        return get_daily_forecast(city=city, days=days, db=db)
    except Exception as exc:
        raise _handle_weather_error(exc)


@router.get("/hourly")
def hourly_weather(
    city: str = Query(..., min_length=1, description="City name (e.g., Bangalore)"),
    hours: int = Query(24, description="Number of forecast hours (1 to 168)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        return get_hourly_forecast(city=city, hours=hours, db=db)
    except Exception as exc:
        raise _handle_weather_error(exc)
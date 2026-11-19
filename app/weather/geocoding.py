import httpx
from pydantic import BaseModel

GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"


class LocationNotFoundError(Exception):
    pass


class GeocodingAPIError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        is_timeout: bool = False,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.is_timeout = is_timeout


class GeoLocation(BaseModel):
    name: str
    latitude: float
    longitude: float
    country: str | None = None
    admin1: str | None = None
    timezone: str = "auto"


CITY_ALIASES = {
    "badmer": "Barmer",
    "bengaluru": "Bangalore",
    "bombay": "Mumbai",
    "calcutta": "Kolkata",
    "madras": "Chennai",
    "gurugram": "Gurgaon",
    "prayagraj": "Allahabad",
    "banaras": "Varanasi",
    "kashi": "Varanasi",
}


def geocode_city(city: str, timeout: float = 10.0) -> GeoLocation:
    cleaned_city = city.strip()
    if not cleaned_city:
        raise LocationNotFoundError("City name cannot be empty")

    lookup_name = CITY_ALIASES.get(cleaned_city.lower(), cleaned_city)

    params = {
        "name": lookup_name,
        "count": 1,
        "language": "en",
        "format": "json",
    }

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(GEOCODING_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException as exc:
        raise GeocodingAPIError(
            f"Geocoding service timed out while looking up '{cleaned_city}'",
            status_code=504,
            is_timeout=True,
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise GeocodingAPIError(
            f"Geocoding service returned HTTP {exc.response.status_code}",
            status_code=exc.response.status_code,
        ) from exc
    except httpx.RequestError as exc:
        raise GeocodingAPIError(
            "Unable to reach the geocoding service",
            status_code=502,
        ) from exc

    results = data.get("results")
    if not results:
        raise LocationNotFoundError(
            f"Location '{cleaned_city}' could not be found. Please check the spelling and try again."
        )

    top_match = results[0]
    return GeoLocation(
        name=top_match["name"],
        latitude=top_match["latitude"],
        longitude=top_match["longitude"],
        country=top_match.get("country"),
        admin1=top_match.get("admin1"),
        timezone=top_match.get("timezone") or "auto",
    )
import re
from enum import Enum
from pydantic import BaseModel, Field


class RouteSource(str, Enum):
    WEATHER = "weather"
    RAG = "rag"
    BOTH = "both"
    NEITHER = "neither"
    CLARIFICATION = "clarification"


class RouteDecision(BaseModel):
    source: RouteSource
    location: str | None = None
    date_intent: str | None = None
    forecast_days: int = 1
    needs_hourly: bool = False
    needs_official_alert: bool = False
    category_hint: str | None = None
    reasoning: str = Field(default="")

    @property
    def requires_weather(self) -> bool:
        return self.source in {RouteSource.WEATHER, RouteSource.BOTH}

    @property
    def requires_rag(self) -> bool:
        return self.source in {RouteSource.RAG, RouteSource.BOTH}

    @property
    def is_clarification(self) -> bool:
        return self.source == RouteSource.CLARIFICATION

    @property
    def is_out_of_scope(self) -> bool:
        return self.source == RouteSource.NEITHER


WEATHER_TERMS = {
    "weather", "temperature", "temp", "rain", "raining", "rainy",
    "forecast", "humidity", "wind", "windy", "cold", "hot", "heat",
    "degrees", "celsius", "fahrenheit", "precipitation", "cloudy",
    "sunny", "showers", "snow", "snowing", "chill", "air quality",
    "monsoon", "drizzle", "barish", "baarish", "barsaat", "mausam",
    "mosam", "garmi", "sardi", "thand", "hawa", "toofan", "tufan",
}

SAFETY_TERMS = {
    "heatwave", "heat wave", "cyclone", "hurricane", "typhoon",
    "orange alert", "red alert", "yellow alert", "green alert",
    "weather alert", "official alert", "disaster", "guidelines",
    "precautions", "precaution", "safety", "advisory", "ndma",
    "imd", "dos and don'ts", "hypothermia", "frostbite",
    "flash flood", "flood", "flooding", "lightning", "thunderstorm",
    "hiking", "trekking", "landslide", "elderly", "safe", "danger",
    "umbrella", "raincoat", "emergency",
}

OUT_OF_SCOPE_TERMS = {
    "stock", "share price", "apple", "crypto", "bitcoin", "recipe",
    "cook", "movie", "film", "cricket score", "coding", "python",
    "poem", "president", "hotel", "resort", "flight ticket", "salary",
}

KNOWN_CITIES = [
    "new delhi", "delhi", "mumbai", "bangalore", "bengaluru",
    "kolkata", "chennai", "hyderabad", "pune", "ahmedabad",
    "jaipur", "jodhpur", "udaipur", "barmer", "badmer", "bikaner",
    "ajmer", "kota", "alwar", "lucknow", "manali", "shimla", "leh", "srinagar",
    "goa", "bhopal", "patna", "chandigarh", "guwahati", "kochi",
    "dehradun", "varanasi", "navi mumbai", "mount abu", "darjeeling",
    "gangtok", "ooty", "rishikesh", "surat", "indore", "nagpur", "nashik",
    "london", "new york", "tokyo", "paris", "sydney", "dubai",
]

LOCATION_STOP_WORDS = {
    "what", "who", "where", "when", "why", "how", "there", "here", "that", "it", "let",
    "is", "are", "was", "were", "can", "will", "would", "should", "could",
    "ha", "kya", "hai", "me", "bhi", "se", "ko",
    "summer", "winter", "monsoon", "elderly", "hiking", "trekking",
    "heatwave", "cyclone", "rain", "flood", "cold", "today", "tomorrow",
    "tonight", "morning", "evening", "advance", "general", "safety",
    "precaution", "precautions", "advisory", "the", "a", "an", "all",
    "our", "my", "your", "this", "weather", "forecast", "temperature",
    "temp", "barish", "baarish", "mausam", "mosam",
}

DEFINITION_PATTERNS = [
    r"^\s*what\s+is\s+(?:a|an|the)?\s*",
    r"^\s*what\s+does\s+.*\s+mean\b",
    r"^\s*define\s+",
    r"^\s*difference\s+between\b",
    r"^\s*explain\s+(?:a|an|the)?\s*",
]


def has_term(text: str, terms: set[str] | list[str]) -> bool:
    for term in terms:
        pattern = r"\b" + re.escape(term.lower()) + r"\b"
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def is_definition_query(text: str) -> bool:
    for pattern in DEFINITION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def extract_location(text: str) -> str | None:
    # 1. Known cities exact word match
    for city in KNOWN_CITIES:
        pattern = r"\b" + re.escape(city) + r"\b"
        if re.search(pattern, text, re.IGNORECASE):
            return " ".join(word.capitalize() for word in city.split())

    # 2. Possessive match (e.g., Delhi's, Pune's)
    possessive_match = re.search(r"\b([A-Za-z]{3,25})'s\b", text)
    if possessive_match:
        cand = possessive_match.group(1).strip()
        if cand.lower() not in LOCATION_STOP_WORDS:
            return cand.capitalize()

    # 3. Hindi/Hinglish "<City> me" (e.g. "Jaipur me barish", "Delhi me")
    hindi_match = re.search(r"\b([A-Za-z]{3,25})\s+me\b", text, re.IGNORECASE)
    if hindi_match:
        cand = hindi_match.group(1).strip()
        if cand.lower() not in LOCATION_STOP_WORDS:
            return cand.capitalize()

    # 4. "<City> weather" / "<City> forecast" / "<City> rain" (e.g. "badmer weather", "barmer forecast")
    prefix_match = re.search(
        r"\b([A-Za-z]{3,25})\s+(?:weather|forecast|temperature|temp|climate|rain|barish|mausam)\b",
        text,
        re.IGNORECASE,
    )
    if prefix_match:
        cand = prefix_match.group(1).strip()
        if cand.lower() not in LOCATION_STOP_WORDS:
            return cand.capitalize()

    # 5. "weather [in/of/for] <City>" (e.g. "weather badmer", "forecast jaipur")
    postfix_match = re.search(
        r"\b(?:weather|forecast|temperature|temp|climate|rain|barish|mausam)\s+(?:in|of|for|at|around)?\s*([A-Za-z]{3,25})\b",
        text,
        re.IGNORECASE,
    )
    if postfix_match:
        cand = postfix_match.group(1).strip()
        if cand.lower() not in LOCATION_STOP_WORDS:
            return cand.capitalize()

    # 6. Standard prepositions: (in|at|for|around|of|near) <City>
    prep_match = re.search(
        r"\b(?:in|at|for|around|of|near)\s+([A-Za-z]{3,25}(?:\s+[A-Za-z]{3,25})?)\b",
        text,
        re.IGNORECASE,
    )
    if prep_match:
        candidate = prep_match.group(1).strip()
        first_word = candidate.split()[0].lower()
        if first_word not in LOCATION_STOP_WORDS:
            return " ".join(word.capitalize() for word in candidate.split())

    return None


def extract_date_intent(text: str) -> tuple[str | None, int, bool]:
    lower = text.lower()
    if has_term(lower, ["beyond the api range", "beyond range", "next month", "30 days"]):
        return ("beyond_range", 30, False)
    if has_term(lower, ["day after tomorrow"]):
        return ("day after tomorrow", 3, False)
    if has_term(lower, ["this evening", "tonight"]):
        return ("this evening", 1, True)
    if has_term(lower, ["tomorrow"]):
        return ("tomorrow", 2, False)
    if has_term(lower, ["this week", "next week", "weekend"]):
        return ("this week", 7, False)
    if has_term(lower, ["3 days", "next 3 days", "three days"]):
        return ("3 days", 3, False)
    if has_term(lower, ["today", "now", "current"]):
        return ("today", 1, False)
    return (None, 1, False)


def extract_category_hint(text: str) -> str | None:
    if has_term(text, ["heatwave", "heat wave", "hot wave"]):
        return "heatwave"
    if has_term(text, ["hurricane", "typhoon"]):
        return "tropical_storms"
    if has_term(text, ["cyclone"]):
        return "cyclone"
    if has_term(text, ["orange alert", "red alert", "yellow alert", "green alert", "weather alert", "official alert"]):
        return "weather_alerts"
    if has_term(text, ["hiking", "trekking", "mountain"]):
        return "hiking_safety"
    if has_term(text, ["umbrella", "raincoat", "flood", "lightning", "thunderstorm", "monsoon"]):
        return "rain_flood"
    if has_term(text, ["cold wave", "frost", "hypothermia", "frostbite"]):
        return "cold_wave"
    return None


def check_official_alert_intent(text: str, location: str | None) -> bool:
    if not location:
        return False
    return has_term(text, ["official alert", "official weather alert", "weather alert", "orange alert", "red alert", "alert status"])


def route_query(query: str) -> RouteDecision:
    cleaned = query.strip()
    if not cleaned:
        return RouteDecision(
            source=RouteSource.NEITHER,
            reasoning="Empty input query.",
        )

    is_def = is_definition_query(cleaned)
    location = extract_location(cleaned)
    date_intent, forecast_days, needs_hourly = extract_date_intent(cleaned)
    category_hint = extract_category_hint(cleaned)

    has_weather_intent = has_term(cleaned, WEATHER_TERMS)
    has_safety_intent = has_term(cleaned, SAFETY_TERMS)
    needs_alert_flag = check_official_alert_intent(cleaned, location)

    # 1. Definitional questions with weather/hazard terms without location -> RAG
    if is_def and (has_safety_intent or has_weather_intent) and not location:
        return RouteDecision(
            source=RouteSource.RAG,
            location=None,
            date_intent=date_intent,
            forecast_days=1,
            needs_hourly=False,
            category_hint=category_hint,
            reasoning="Definitional knowledge query about a weather or safety concept.",
        )

    # 2. Combined Weather + Safety / Advisory queries
    if location and (has_safety_intent or category_hint in {"hiking_safety", "rain_flood", "weather_alerts"}):
        return RouteDecision(
            source=RouteSource.BOTH,
            location=location,
            date_intent=date_intent or "today",
            forecast_days=forecast_days,
            needs_hourly=needs_hourly,
            needs_official_alert=needs_alert_flag,
            category_hint=category_hint,
            reasoning="Requires both live weather observation and safety knowledge advisory.",
        )

    # 3. Missing Location where weather is essential -> Clarification
    if has_weather_intent and not location and not is_def:
        if date_intent == "beyond_range":
            return RouteDecision(
                source=RouteSource.WEATHER,
                location=None,
                date_intent=date_intent,
                forecast_days=forecast_days,
                reasoning="Weather query with out-of-range forecast target.",
            )
        return RouteDecision(
            source=RouteSource.CLARIFICATION,
            location=None,
            date_intent=date_intent,
            reasoning="Weather query lacks a target city or location. Ask user for location.",
        )

    # 4. Situational Precautions without Location or Hazard -> Clarification
    if has_term(cleaned, ["precaution", "precautions"]) and not location and not category_hint:
        return RouteDecision(
            source=RouteSource.CLARIFICATION,
            location=None,
            date_intent=date_intent,
            reasoning="Asks for general precautions without specifying location or hazard type.",
        )

    # 5. Pure RAG / Safety Knowledge (No location requested)
    if has_safety_intent and not location:
        return RouteDecision(
            source=RouteSource.RAG,
            location=None,
            date_intent=date_intent,
            forecast_days=1,
            needs_hourly=False,
            category_hint=category_hint,
            reasoning="Asks for domain disaster/safety guidelines without a specific location.",
        )

    # 6. Pure Weather with Location (explicit weather intent OR standalone location query)
    is_short_location = False
    if location and not has_term(cleaned, OUT_OF_SCOPE_TERMS):
        non_stop_words = [w for w in re.findall(r"\w+", cleaned.lower()) if w not in LOCATION_STOP_WORDS]
        loc_words = re.findall(r"\w+", location.lower())
        if set(non_stop_words).issubset(set(loc_words)) or len(non_stop_words) <= 2:
            is_short_location = True

    if (has_weather_intent or date_intent is not None or is_short_location) and location:
        return RouteDecision(
            source=RouteSource.WEATHER,
            location=location,
            date_intent=date_intent or "today",
            forecast_days=forecast_days,
            needs_hourly=needs_hourly,
            category_hint=None,
            reasoning="Standard weather observation or forecast request for a specific location.",
        )

    # 7. Out-of-Scope (Non-weather or general queries)
    return RouteDecision(
        source=RouteSource.NEITHER,
        location=None,
        reasoning="Query is unrelated to weather metrics or safety advisories.",
    )

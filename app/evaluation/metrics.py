import re
from typing import Any

from app.schemas.chat import ChatResponse


def compute_routing_score(
    actual_route: str,
    expected_route: str,
    actual_location: str | None,
    expected_location: str | None,
) -> float:
    """Computes routing accuracy score (0.0 to 1.0).
    
    Scoring Breakdown:
    - Route Match:
      - Perfect route + perfect location match: 1.0
      - Perfect route + missing/mismatched location: 0.85
    - Route Mismatch:
      - Mismatched route but correct location identified: 0.20
      - Neither route nor location matches: 0.0
    """
    actual_r = (actual_route or "").strip().lower()
    expected_r = (expected_route or "").strip().lower()

    route_matches = actual_r == expected_r

    norm_actual_loc = actual_location.strip().lower() if actual_location else None
    norm_expected_loc = expected_location.strip().lower() if expected_location else None
    location_matches = norm_actual_loc == norm_expected_loc

    if route_matches:
        return 1.0 if location_matches else 0.85
    return 0.20 if location_matches else 0.0


def compute_retrieval_score(
    expected_route: str,
    retrieved_chunks: list[dict[str, Any]],
    expected_categories: list[str],
    document_sources: list[Any],
) -> float | None:
    """Computes retrieval relevance and citation integrity score.
    
    Returns:
    - None (stored as null in database) if retrieval was not expected (e.g. weather-only, neither, clarification).
    - Float (0.0 to 1.0) for RAG and BOTH routes based on:
      1. Category Alignment (60% weight): Ratio of retrieved chunks matching expected hazard categories.
      2. Citation Integrity (40% weight): Verified presence of non-empty title and valid http/https source_url.
    """
    normalized_route = (expected_route or "").strip().lower()
    if normalized_route not in {"rag", "both"}:
        return None

    if not retrieved_chunks and not document_sources:
        return 0.0

    # 1. Category Alignment
    norm_expected_cats = {cat.strip().lower() for cat in expected_categories if cat}
    if not norm_expected_cats:
        category_score = 1.0
    else:
        matched_chunks = 0
        total_chunks = len(retrieved_chunks) if retrieved_chunks else len(document_sources)
        for chunk in (retrieved_chunks or document_sources):
            cat = (chunk.get("category") if isinstance(chunk, dict) else getattr(chunk, "category", "") or "").lower()
            if cat in norm_expected_cats:
                matched_chunks += 1
        category_score = matched_chunks / total_chunks if total_chunks > 0 else 0.0

    # 2. Citation Integrity
    sources_to_check = document_sources if document_sources else retrieved_chunks
    valid_citations = 0
    for s in sources_to_check:
        title = s.get("title") if isinstance(s, dict) else getattr(s, "title", None)
        url = s.get("source_url") if isinstance(s, dict) else getattr(s, "source_url", None)
        if title and url and url.startswith("http"):
            valid_citations += 1

    citation_score = valid_citations / len(sources_to_check) if sources_to_check else 0.0

    return round(0.60 * category_score + 0.40 * citation_score, 4)


def compute_answer_score(
    answer: str,
    expected_keywords: list[str],
    expected_route: str,
    needs_official_alert: bool,
    weather_sources: list[Any],
    document_sources: list[Any],
    weather_data: dict[str, Any] | None = None,
    test_id: int | None = None,
) -> float:
    """Deterministically evaluates response quality and grounding without an LLM judge.
    
    Scoring Components (Total 1.0):
    1. Keyword Coverage (40%): Fraction of mandatory domain keywords found in the answer.
    2. Citation / Source Provenance (30%):
       - If route is RAG: requires document sources > 0.
       - If route is WEATHER: requires weather sources > 0 (or clean error message on negative tests).
       - If route is BOTH: requires both sources present.
    3. Official Alert Compliance (15%):
       - If needs_official_alert is True, requires explicit alert disclaimer ("not official" / "verified").
    4. Anti-Hallucination & Numerical Grounding (15%):
       - Ensures no invented metrics appear in the answer, and errors (Test 11/12) report clear messages.
    """
    if not answer or not answer.strip():
        return 0.0

    norm_answer = answer.lower()
    score = 0.0

    # 1. Keyword Coverage (0.0 to 0.40)
    if expected_keywords:
        found_keywords = sum(1 for kw in expected_keywords if kw.lower() in norm_answer)
        keyword_fraction = found_keywords / len(expected_keywords)
        score += 0.40 * keyword_fraction
    else:
        score += 0.40

    # 2. Source Provenance (0.0 to 0.30)
    route = (expected_route or "").strip().lower()
    if route == "rag":
        score += 0.30 if document_sources else 0.0
    elif route == "weather":
        # Negative tests (Q11, Q12) expect clean error messages rather than live weather sources
        if test_id in {11, 12}:
            score += 0.30 if ("could not be resolved" in norm_answer or "exceed" in norm_answer or "range" in norm_answer) else 0.0
        else:
            score += 0.30 if weather_sources else 0.0
    elif route == "both":
        doc_ok = bool(document_sources)
        weather_ok = bool(weather_sources)
        if doc_ok and weather_ok:
            score += 0.30
        elif doc_ok or weather_ok:
            score += 0.15
    elif route in {"neither", "clarification"}:
        score += 0.30

    # 3. Official Alert Mandate (0.0 to 0.15)
    if needs_official_alert:
        has_disclaimer = any(
            phrase in norm_answer
            for phrase in [
                "not official",
                "not an official",
                "cannot be verified",
                "could not be verified",
                "consult official",
                "official alert",
                "official government alert",
                "civil warnings",
                "mausam.imd.gov.in",
            ]
        )
        score += 0.15 if has_disclaimer else 0.0
    else:
        score += 0.15

    # 4. Anti-Hallucination & Grounding Check (0.0 to 0.15)
    # Check that temperature numbers cited in answer match weather_data
    if weather_data and route in {"weather", "both"}:
        # Extract temperatures mentioned like "28°C", "28.5 °C"
        cited_numbers = re.findall(r"\b(\d{1,2}(?:\.\d)?)\s*°?\s*c\b", norm_answer)
        if cited_numbers:
            valid_numbers = set()
            for key in ["temperature_c", "temperature_max_c", "temperature_min_c", "apparent_temperature_c"]:
                val = weather_data.get(key)
                if val is not None:
                    valid_numbers.add(str(round(float(val))))
                    valid_numbers.add(str(round(float(val), 1)))
            # If at least one cited temperature matches verified data
            matches_data = any(num.split(".")[0] in valid_numbers for num in cited_numbers)
            score += 0.15 if matches_data else 0.05
        else:
            score += 0.15
    else:
        score += 0.15

    return round(min(1.0, max(0.0, score)), 4)

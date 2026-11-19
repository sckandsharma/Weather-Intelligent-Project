import logging
import time
from typing import Any
from fastapi import HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.database.models import Conversation, Message
from app.llm.generator import LLMGenerationError, generate_response
from app.llm.prompts import (
    CLARIFICATION_MESSAGE,
    OUT_OF_SCOPE_MESSAGE,
    DocumentSource,
    WeatherSource,
    build_document_sources,
    build_user_prompt,
    build_weather_sources,
    calculate_confidence,
)
from app.llm.router import RouteDecision, RouteSource, extract_location, route_query
from app.rag.retrieval import retrieve_relevant_chunks
from app.services.logging_service import log_audit_event
from app.schemas.chat import ChatResponse
from app.weather.client import WeatherAPIError
from app.weather.geocoding import LocationNotFoundError
from app.weather.service import (
    get_current_weather,
    get_daily_forecast,
    get_hourly_forecast,
)

logger = logging.getLogger(__name__)

NO_RAG_MATCH_MESSAGE = (
    "I could not find matching official disaster safety guidelines or meteorological "
    "documentation for your request in the verified knowledge base."
)





def _get_or_create_conversation(
    db: Session,
    user_id: int,
    conversation_id: int | None,
    initial_title: str,
) -> Conversation:
    if conversation_id:
        conv = db.get(Conversation, conversation_id)
        if not conv or conv.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found for current user",
            )
        return conv

    title = initial_title.strip()[:60] if initial_title else "New Conversation"
    conv = Conversation(user_id=user_id, title=title)
    db.add(conv)
    db.flush()
    return conv


def _fetch_conversation_history(
    db: Session,
    conversation_id: int,
    max_turns: int = 4,
) -> list[dict[str, str]]:
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(max_turns)
    )
    messages = db.execute(stmt).scalars().all()
    messages.reverse()

    history: list[dict[str, str]] = []
    for m in messages:
        history.append({"role": "user", "content": m.question})
        history.append({"role": "assistant", "content": m.answer})
    return history


def _find_location_in_history(history: list[dict[str, str]]) -> str | None:
    for turn in reversed(history):
        cand = extract_location(turn.get("content", ""))
        if cand:
            return cand
    return None


def _fetch_weather_sync(
    decision: RouteDecision,
    db: Session,
) -> tuple[dict[str, Any] | None, str | None]:
    if decision.forecast_days > 16 or decision.date_intent == "beyond_range":
        return None, "Forecast requests beyond 16 days exceed the supported meteorological model range (1-16 days)."

    if not decision.location:
        return None, "A location is required to retrieve meteorological conditions."

    loc = decision.location

    try:
        if decision.needs_hourly:
            return get_hourly_forecast(city=loc, hours=24, db=db), None
        elif decision.forecast_days > 1:
            return get_daily_forecast(city=loc, days=decision.forecast_days, db=db), None
        else:
            return get_current_weather(city=loc, db=db), None

    except LocationNotFoundError:
        return None, f"Location '{loc}' could not be resolved by the geocoding service. Please check the spelling."
    except WeatherAPIError as e:
        logger.error("WeatherAPIError for %s: %s", loc, str(e))
        return None, "The meteorological data provider is temporarily unavailable or timed out."
    except ValueError as e:
        return None, str(e)
    except Exception as e:
        logger.exception("Unexpected error fetching weather for %s: %s", loc, str(e))
        return None, "An unexpected error occurred while fetching live weather metrics."


def _retrieve_chunks_sync(
    query: str,
    db: Session,
    category_hint: str | None,
) -> list[dict[str, Any]]:
    chunks = retrieve_relevant_chunks(
        query=query,
        db=db,
        top_k=5,
        min_score=0.30,
        category_filter=category_hint,
    )
    if not chunks and category_hint:
        chunks = retrieve_relevant_chunks(
            query=query,
            db=db,
            top_k=5,
            min_score=0.30,
            category_filter=None,
        )
    return chunks


def _save_message_and_respond(
    db: Session,
    conv_id: int,
    question: str,
    answer: str,
    confidence: str,
    routing_decision: str,
    location: str | None = None,
    weather_sources: list[WeatherSource] | None = None,
    document_sources: list[DocumentSource] | None = None,
    start_time: float | None = None,
    user_id: int | None = None,
) -> ChatResponse:
    total_latency_ms = int((time.perf_counter() - start_time) * 1000) if start_time else 0

    msg = Message(conversation_id=conv_id, question=question, answer=answer)
    db.add(msg)
    db.commit()
    db.refresh(msg)

    if user_id:
        log_audit_event(
            db=db,
            action="chat_query",
            resource=f"conversation:{conv_id}",
            user_id=user_id,
        )

    return ChatResponse(
        conversation_id=conv_id,
        message_id=msg.id,
        answer=answer,
        confidence=confidence,
        routing_decision=routing_decision,
        location=location,
        weather_sources=weather_sources or [],
        document_sources=document_sources or [],
        latency_ms=total_latency_ms,
    )


async def process_chat_message(
    user_id: int,
    message: str,
    db: Session,
    conversation_id: int | None = None,
) -> ChatResponse:
    start_pipeline_time = time.perf_counter()
    cleaned_query = message.strip()

    if not cleaned_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message content cannot be empty",
        )

    try:
        conv = _get_or_create_conversation(db, user_id, conversation_id, cleaned_query)
        history = _fetch_conversation_history(db, conv.id, max_turns=4)

        decision = route_query(cleaned_query)
        source = decision.source

        # 1. Fast-Path: Out-of-Scope (NEITHER)
        if source == RouteSource.NEITHER:
            return _save_message_and_respond(
                db=db,
                conv_id=conv.id,
                question=cleaned_query,
                answer=OUT_OF_SCOPE_MESSAGE,
                confidence="high",
                routing_decision=source.value,
                start_time=start_pipeline_time,
                user_id=user_id,
            )

        # 2. Fast-Path: Clarification (Vague input)
        if source == RouteSource.CLARIFICATION:
            return _save_message_and_respond(
                db=db,
                conv_id=conv.id,
                question=cleaned_query,
                answer=CLARIFICATION_MESSAGE,
                confidence="high",
                routing_decision=source.value,
                start_time=start_pipeline_time,
                user_id=user_id,
            )

        # 3. Contextual City Recovery from History
        if decision.requires_weather and not decision.location:
            history_loc = _find_location_in_history(history)
            if history_loc:
                decision.location = history_loc
            elif decision.date_intent != "beyond_range":
                return _save_message_and_respond(
                    db=db,
                    conv_id=conv.id,
                    question=cleaned_query,
                    answer="Could you please specify which city or location you would like the weather report for?",
                    confidence="high",
                    routing_decision=RouteSource.CLARIFICATION.value,
                    start_time=start_pipeline_time,
                    user_id=user_id,
                )

        # 4. Asynchronous / Threadpool Data Fetching
        weather_data: dict[str, Any] | None = None
        weather_err: str | None = None

        if decision.requires_weather:
            weather_data, weather_err = await run_in_threadpool(
                _fetch_weather_sync, decision, db
            )

        chunks: list[dict[str, Any]] = []
        if decision.requires_rag:
            chunks = await run_in_threadpool(
                _retrieve_chunks_sync, cleaned_query, db, decision.category_hint
            )

        # 5. Fast-Path: Weather-only with resolution error
        if source == RouteSource.WEATHER and weather_err and not weather_data:
            return _save_message_and_respond(
                db=db,
                conv_id=conv.id,
                question=cleaned_query,
                answer=weather_err,
                confidence="low",
                routing_decision=source.value,
                location=decision.location,
                start_time=start_pipeline_time,
                user_id=user_id,
            )

        # 6. Fast-Path: RAG-only with zero matching chunks
        if source == RouteSource.RAG and not chunks:
            return _save_message_and_respond(
                db=db,
                conv_id=conv.id,
                question=cleaned_query,
                answer=NO_RAG_MATCH_MESSAGE,
                confidence="low",
                routing_decision=source.value,
                location=None,
                start_time=start_pipeline_time,
                user_id=user_id,
            )

        # 7. Assemble Verified Sources & Calculate Confidence
        weather_sources = build_weather_sources(weather_data)
        document_sources = build_document_sources(chunks)
        confidence = calculate_confidence(source, weather_data, chunks)

        user_prompt = build_user_prompt(
            source=source,
            query=cleaned_query,
            weather_data=weather_data,
            chunks=chunks,
            history=history,
            date_intent=decision.date_intent,
            needs_official_alert=decision.needs_official_alert,
            weather_error=weather_err,
        )

        # 8. Call LLM Generator
        llm_result = await generate_response(user_prompt=user_prompt)
        answer = llm_result.content

        return _save_message_and_respond(
            db=db,
            conv_id=conv.id,
            question=cleaned_query,
            answer=answer,
            confidence=confidence,
            routing_decision=source.value,
            location=decision.location,
            weather_sources=weather_sources,
            document_sources=document_sources,
            start_time=start_pipeline_time,
            user_id=user_id,
        )

    except HTTPException:
        db.rollback()
        raise
    except LLMGenerationError as e:
        db.rollback()
        logger.error("LLM Generation failed: %s (status %d)", e.message, e.status_code)
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        db.rollback()
        logger.exception("Unexpected error during chat processing: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your conversation turn.",
        )

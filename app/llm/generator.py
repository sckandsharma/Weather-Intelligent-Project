import asyncio
from functools import lru_cache
import logging
import time
from typing import Any
from google import genai
from google.genai import types
from google.genai.errors import APIError
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.llm.prompts import SYSTEM_INSTRUCTION

logger = logging.getLogger(__name__)


class LLMGenerationError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class LLMResult(BaseModel):
    content: str
    latency_ms: int
    finish_reason: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


@lru_cache(maxsize=1)
def get_gemini_client() -> genai.Client:
    api_key = settings.GEMINI_API_KEY.strip()
    if not api_key or api_key == "your_api_key_here":
        logger.error("GEMINI_API_KEY is not configured or contains placeholder text.")
        raise LLMGenerationError(
            "Gemini API key is not configured. Please set GEMINI_API_KEY in your .env file.",
            status_code=500,
        )
    return genai.Client(api_key=api_key)


def _build_config(
    system_instruction: str,
    temperature: float,
    max_output_tokens: int,
) -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )


def _extract_usage(usage_metadata: Any) -> tuple[int | None, int | None, int | None]:
    if not usage_metadata:
        return None, None, None
    prompt = getattr(usage_metadata, "prompt_token_count", None)
    candidates = getattr(usage_metadata, "candidates_token_count", None)
    total = getattr(usage_metadata, "total_token_count", None)
    return prompt, candidates, total


async def generate_response(
    user_prompt: str,
    system_instruction: str = SYSTEM_INSTRUCTION,
    temperature: float = 0.2,
    max_output_tokens: int = 2048,
    max_retries: int = 2,
) -> LLMResult:
    client = get_gemini_client()
    config = _build_config(system_instruction, temperature, max_output_tokens)

    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        start_time = time.perf_counter()
        try:
            response = await run_in_threadpool(
                client.models.generate_content,
                model=settings.LLM_MODEL,
                contents=user_prompt,
                config=config,
            )
            latency_ms = int((time.perf_counter() - start_time) * 1000)

            finish_reason: str | None = None
            if response.candidates:
                candidate = response.candidates[0]
                if candidate.finish_reason:
                    finish_reason = str(candidate.finish_reason)

                if finish_reason in {"SAFETY", "BLOCKLIST"}:
                    logger.warning("Gemini blocked response due to safety filters: %s", finish_reason)
                    raise LLMGenerationError(
                        "The response could not be completed due to content safety policies.",
                        status_code=400,
                    )
                if finish_reason == "MAX_TOKENS" and not response.text:
                    logger.warning("Gemini exceeded token limit without generating text.")
                    raise LLMGenerationError(
                        "The response exceeded maximum token limits. Please refine your query.",
                        status_code=500,
                    )

            if not response.text:
                logger.error("Gemini returned an empty text payload. Finish reason: %s", finish_reason)
                raise LLMGenerationError(
                    "The AI service returned an empty response.",
                    status_code=502,
                )

            p_tokens, c_tokens, t_tokens = _extract_usage(response.usage_metadata)

            return LLMResult(
                content=response.text.strip(),
                latency_ms=latency_ms,
                finish_reason=finish_reason,
                prompt_tokens=p_tokens,
                completion_tokens=c_tokens,
                total_tokens=t_tokens,
            )

        except APIError as e:
            last_error = e
            logger.error("Gemini APIError on attempt %d: code=%s message=%s", attempt + 1, e.code, e.message)

            if e.code in {429, 503} and attempt < max_retries:
                backoff = 1.5 ** (attempt + 1)
                logger.info("Retrying Gemini API request in %.1f seconds...", backoff)
                await asyncio.sleep(backoff)
                continue

            if e.code == 429:
                raise LLMGenerationError(
                    "The AI service is currently experiencing high demand. Please try again shortly.",
                    status_code=429,
                )
            if e.code in {401, 403}:
                raise LLMGenerationError(
                    "Authentication with the AI provider failed. Please check server configuration.",
                    status_code=500,
                )
            if e.code == 404:
                raise LLMGenerationError(
                    f"Configured LLM model '{settings.LLM_MODEL}' was not found. Check LLM_MODEL setting.",
                    status_code=500,
                )

            raise LLMGenerationError(
                "The AI service is temporarily unavailable.",
                status_code=502,
            )

        except LLMGenerationError:
            raise
        except Exception as e:
            last_error = e
            logger.exception("Unexpected error while invoking Gemini API: %s", str(e))
            raise LLMGenerationError(
                "An unexpected internal error occurred while generating the AI response.",
                status_code=502,
            )

    raise LLMGenerationError(
        f"Failed to communicate with AI provider after {max_retries + 1} attempts.",
        status_code=502,
    )


def generate_response_sync(
    user_prompt: str,
    system_instruction: str = SYSTEM_INSTRUCTION,
    temperature: float = 0.2,
    max_output_tokens: int = 2048,
) -> LLMResult:
    return asyncio.run(
        generate_response(
            user_prompt=user_prompt,
            system_instruction=system_instruction,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
    )

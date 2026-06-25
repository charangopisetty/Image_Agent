"""Map upstream failures (Groq, LiteLLM, CrewAI) to HTTP API errors."""

from __future__ import annotations

from enum import StrEnum

from fastapi import HTTPException
from pydantic import BaseModel, Field


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "validation_error"
    UNAUTHORIZED = "unauthorized"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    AUTHENTICATION_ERROR = "authentication_error"
    CONTEXT_TOO_LARGE = "context_too_large"
    UPSTREAM_TIMEOUT = "upstream_timeout"
    UPSTREAM_UNAVAILABLE = "upstream_unavailable"
    VISION_ERROR = "vision_error"
    GENERATION_FAILED = "generation_failed"


class ErrorBody(BaseModel):
    code: ErrorCode
    message: str
    status: int
    detail: str | None = Field(
        default=None,
        description="Optional technical detail (safe for clients; no secrets).",
    )


class ErrorResponse(BaseModel):
    error: ErrorBody


def _iter_exception_chain(exc: BaseException) -> list[BaseException]:
    chain: list[BaseException] = []
    current: BaseException | None = exc
    while current is not None and current not in chain:
        chain.append(current)
        current = current.__cause__ or current.__context__
    return chain


def _message_blob(exc: BaseException) -> str:
    return " ".join(str(item) for item in _iter_exception_chain(exc)).lower()


def _try_litellm_mapping(exc: BaseException) -> tuple[int, ErrorCode, str] | None:
    try:
        from litellm.exceptions import (
            APIConnectionError,
            AuthenticationError,
            ContextWindowExceededError,
            RateLimitError,
            ServiceUnavailableError,
            Timeout,
        )
    except ImportError:
        return None

    for item in _iter_exception_chain(exc):
        if isinstance(item, RateLimitError):
            return (
                429,
                ErrorCode.RATE_LIMIT_EXCEEDED,
                "LLM provider rate limit reached. Wait and retry.",
            )
        if isinstance(item, AuthenticationError):
            return (
                502,
                ErrorCode.AUTHENTICATION_ERROR,
                "LLM provider rejected the API key. Check GROQ_API_KEY and model settings.",
            )
        if isinstance(item, Timeout):
            return (
                504,
                ErrorCode.UPSTREAM_TIMEOUT,
                "LLM request timed out. Try again with a smaller request.",
            )
        if isinstance(item, ServiceUnavailableError):
            return (
                503,
                ErrorCode.UPSTREAM_UNAVAILABLE,
                "LLM provider is temporarily unavailable. Retry shortly.",
            )
        if isinstance(item, APIConnectionError):
            return (
                503,
                ErrorCode.UPSTREAM_UNAVAILABLE,
                "Could not reach the LLM provider. Check network and API status.",
            )
        if isinstance(item, ContextWindowExceededError):
            return (
                413,
                ErrorCode.CONTEXT_TOO_LARGE,
                "Input is too large for the model context window.",
            )
    return None


def _message_heuristic_mapping(blob: str) -> tuple[int, ErrorCode, str] | None:
    if any(token in blob for token in ("rate limit", "429", "too many requests", "throttl")):
        return (
            429,
            ErrorCode.RATE_LIMIT_EXCEEDED,
            "LLM provider rate limit reached. Wait and retry.",
        )
    if any(
        token in blob
        for token in ("authentication", "invalid api key", "unauthorized", "401", "403")
    ):
        return (
            502,
            ErrorCode.AUTHENTICATION_ERROR,
            "LLM provider authentication failed. Verify API credentials.",
        )
    if any(token in blob for token in ("timeout", "timed out", "deadline exceeded")):
        return (
            504,
            ErrorCode.UPSTREAM_TIMEOUT,
            "Request timed out while generating social content.",
        )
    if any(
        token in blob
        for token in ("connection refused", "connection error", "failed to connect")
    ):
        return (
            503,
            ErrorCode.UPSTREAM_UNAVAILABLE,
            "Could not connect to a required upstream service.",
        )
    if any(
        token in blob
        for token in ("context window", "context length", "maximum context", "too long")
    ):
        return (
            413,
            ErrorCode.CONTEXT_TOO_LARGE,
            "Input exceeds model limits.",
        )
    if "tool_use_failed" in blob or "failed to call a function" in blob:
        return (
            502,
            ErrorCode.GENERATION_FAILED,
            "Social post generation failed while formatting the model response.",
        )
    if any(token in blob for token in ("vision", "analyze_image_url", "image analysis")) and any(
        token in blob for token in ("failed", "unsupported", "invalid", "could not")
    ):
        return (
            422,
            ErrorCode.VISION_ERROR,
            "Image analysis failed. Verify image_url is public HTTPS and VISION_MODEL supports vision.",
        )
    return None


def classify_exception(exc: BaseException) -> tuple[int, ErrorCode, str]:
    litellm_result = _try_litellm_mapping(exc)
    if litellm_result is not None:
        return litellm_result

    heuristic = _message_heuristic_mapping(_message_blob(exc))
    if heuristic is not None:
        return heuristic

    return (
        500,
        ErrorCode.GENERATION_FAILED,
        "Social post generation failed due to an unexpected error.",
    )


def build_error_response(
    exc: BaseException,
    *,
    include_technical_detail: bool = True,
) -> ErrorResponse:
    status, code, message = classify_exception(exc)
    detail = str(exc).strip() if include_technical_detail and str(exc).strip() else None
    return ErrorResponse(
        error=ErrorBody(code=code, message=message, status=status, detail=detail)
    )


def raise_api_error(exc: BaseException) -> None:
    body = build_error_response(exc)
    headers: dict[str, str] | None = None
    if body.error.status == 429:
        headers = {"Retry-After": "60"}
    raise HTTPException(
        status_code=body.error.status,
        detail=body.model_dump(),
        headers=headers,
    ) from exc

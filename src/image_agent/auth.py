"""Shared API key authentication for HTTP clients."""

from __future__ import annotations

import os
import secrets

from fastapi import Request
from fastapi.responses import JSONResponse

from image_agent.errors import ErrorBody, ErrorCode, ErrorResponse

API_KEY_HEADER = "X-API-Key"

PUBLIC_PATHS = frozenset(
    {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/favicon.ico",
    }
)


def configured_api_key() -> str | None:
    key = os.getenv("API_KEY", "").strip()
    return key or None


def extract_api_key(request: Request) -> str | None:
    header_key = request.headers.get(API_KEY_HEADER)
    if header_key:
        return header_key.strip()

    authorization = request.headers.get("Authorization", "")
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip()

    return None


def is_authorized(request: Request) -> bool:
    expected = configured_api_key()
    if expected is None:
        return True

    provided = extract_api_key(request)
    if provided is None:
        return False

    return secrets.compare_digest(provided, expected)


def unauthorized_response() -> JSONResponse:
    payload = ErrorResponse(
        error=ErrorBody(
            code=ErrorCode.UNAUTHORIZED,
            message="Invalid or missing API key.",
            status=401,
            detail="Send your API key via X-API-Key header or Authorization: Bearer <key>.",
        )
    )
    return JSONResponse(status_code=401, content=payload.model_dump())


def requires_api_key(path: str) -> bool:
    return path not in PUBLIC_PATHS

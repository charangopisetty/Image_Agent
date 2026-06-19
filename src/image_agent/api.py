import asyncio

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse

from image_agent.errors import ErrorBody, ErrorCode, ErrorResponse, raise_api_error
from image_agent.schemas import SocialPostRequest, SocialPostResponse
from image_agent.service import generate_social_post

app = FastAPI(
    title="Image Agent API",
    description="Generate social post captions, hashtags, and tags from an image and brand context.",
    version="0.1.0",
)


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    first_error = exc.errors()[0] if exc.errors() else {}
    location = " -> ".join(str(part) for part in first_error.get("loc", []))
    message = first_error.get("msg", "Invalid request")
    payload = ErrorResponse(
        error=ErrorBody(
            code=ErrorCode.VALIDATION_ERROR,
            message=f"Request validation failed{f' at {location}' if location else ''}.",
            status=422,
            detail=message,
        )
    )
    return JSONResponse(status_code=422, content=payload.model_dump())


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail, headers=exc.headers)
    payload = ErrorResponse(
        error=ErrorBody(
            code=ErrorCode.VALIDATION_ERROR
            if exc.status_code == 422
            else ErrorCode.GENERATION_FAILED,
            message=str(exc.detail),
            status=exc.status_code,
        )
    )
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump(), headers=exc.headers)


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/social-post", response_model=SocialPostResponse)
async def create_social_post(request: SocialPostRequest) -> SocialPostResponse:
    """
    Generate Instagram-style social post content from an image URL and brand context.

    Example:
        curl -X POST http://127.0.0.1:8080/social-post \\
          -H "Content-Type: application/json" \\
          -d @examples/request.json
    """
    try:
        return await asyncio.to_thread(generate_social_post, request)
    except HTTPException:
        raise
    except Exception as exc:
        raise_api_error(exc)

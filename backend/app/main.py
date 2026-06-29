"""
FastAPI application entry point.
"""
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi.errors import RateLimitExceeded

from .config import get_settings
from .routers import tailor
from .utils.auth import require_api_key
from .utils.rate_limit import limiter, rate_limit_handler

settings = get_settings()
logger = logging.getLogger(__name__)

UPLOAD_PATHS = {
    "/api/parse-file",
    "/api/tailor/upload",
    "/api/tailor/upload/stream",
}

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Intelligent CV tailoring system that customizes CVs for specific job descriptions",
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)


@app.middleware("http")
async def api_key_auth_middleware(request: Request, call_next):
    """Require API key authentication before routing any endpoint."""
    return await require_api_key(request, call_next, settings)


@app.middleware("http")
async def upload_size_middleware(request: Request, call_next):
    """Reject oversized upload requests before multipart parsing."""
    if request.url.path in UPLOAD_PATHS:
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                max_request_bytes = (
                    settings.max_upload_bytes + settings.upload_request_overhead_bytes
                )
                if int(content_length) > max_request_bytes:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": "UPLOAD_TOO_LARGE",
                            "message": "Uploaded file is too large.",
                        },
                    )
            except ValueError:
                pass
    return await call_next(request)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Surface structured error details at the top level of the response body.

    Routes raise HTTPException(detail={"error": ..., "message": ..., "details": ...}).
    FastAPI's default nests that under a "detail" key, but the frontend expects
    {error, message, details} at the top level, so flatten it here.
    """
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTP_ERROR", "message": str(exc.detail)},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Log internal failures without exposing exception details to clients."""
    logger.exception("Unhandled request failure")
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An internal server error occurred.",
        },
    )

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tailor.router, prefix="/api", tags=["tailor"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
    }


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs_url": "/docs",
        "health_url": "/health"
    }

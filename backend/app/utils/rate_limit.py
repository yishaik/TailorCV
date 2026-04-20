"""
Rate limiting configuration using slowapi.

Protects API endpoints from abuse and excessive usage.
Uses IP-based rate limiting with configurable limits.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse


def _get_client_ip(request: Request) -> str:
    """Extract client IP, respecting proxy headers for Vercel."""
    # Vercel sets x-forwarded-for
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(
    key_func=_get_client_ip,
    default_limits=["60/minute"],
    storage_uri="memory://",
)


def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom handler for rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "error": "RATE_LIMITED",
            "message": f"Rate limit exceeded: {exc.detail}. Please try again later.",
            "retry_after": exc.detail,
        },
    )

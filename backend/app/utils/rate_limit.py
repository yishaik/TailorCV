"""
Rate limiting configuration using slowapi.

Protects API endpoints from abuse and excessive usage.
Uses IP-based rate limiting with configurable limits.
"""
import hashlib

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

from ..config import get_settings
from .auth import extract_api_key

settings = get_settings()


def _get_client_ip(request: Request) -> str:
    """Extract client IP, respecting proxy headers for Vercel."""
    # Vercel sets x-forwarded-for
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


def _hash_api_key(api_key: str) -> str:
    """Hash API keys before using them in rate-limit storage keys."""
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:16]


def _rate_limit_key(request: Request) -> str:
    """Rate-limit authenticated clients by API key plus client IP."""
    api_key = extract_api_key(request, settings)
    client_ip = _get_client_ip(request)
    if api_key:
        return f"api-key:{_hash_api_key(api_key)}:ip:{client_ip}"
    return f"ip:{client_ip}"


limiter = Limiter(
    key_func=_rate_limit_key,
    default_limits=["60/minute"],
    storage_uri=settings.rate_limit_storage_uri,
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

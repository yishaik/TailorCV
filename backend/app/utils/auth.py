"""
API key authentication helpers.
"""
import logging
import secrets
from collections.abc import Callable, Awaitable

from fastapi import Request
from fastapi.responses import JSONResponse, Response

from ..config import Settings

logger = logging.getLogger(__name__)


def extract_api_key(request: Request, settings: Settings) -> str:
    """Read an API key from the configured header or Authorization bearer."""
    header_value = request.headers.get(settings.api_key_header_name, "").strip()
    if header_value:
        return header_value

    authorization = request.headers.get("authorization", "").strip()
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip()

    return ""


def api_key_error(status_code: int, error: str, message: str) -> JSONResponse:
    """Build a consistent auth failure response."""
    return JSONResponse(
        status_code=status_code,
        content={"error": error, "message": message},
        headers={"WWW-Authenticate": "Bearer"},
    )


async def require_api_key(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
    settings: Settings,
) -> Response:
    """Middleware entry point for fail-closed API key authentication."""
    if request.method == "OPTIONS" or not settings.api_auth_enabled:
        return await call_next(request)

    expected_key = settings.tailorcv_api_key.strip()
    if not expected_key:
        logger.error("API authentication is enabled but TAILORCV_API_KEY is unset")
        return api_key_error(
            503,
            "AUTH_NOT_CONFIGURED",
            "API authentication is not configured.",
        )

    supplied_key = extract_api_key(request, settings)
    if not supplied_key:
        return api_key_error(
            401,
            "AUTH_REQUIRED",
            "A valid API key is required.",
        )

    if not secrets.compare_digest(supplied_key, expected_key):
        return api_key_error(
            401,
            "AUTH_INVALID",
            "A valid API key is required.",
        )

    return await call_next(request)

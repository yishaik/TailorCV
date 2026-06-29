"""
Application configuration settings.
Uses environment variables for sensitive data.
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Literal
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    gemini_api_key: str = ""
    tailorcv_api_key: str = ""
    api_auth_enabled: bool = True
    api_key_header_name: str = "X-API-Key"

    # Request protection
    max_upload_bytes: int = 5 * 1024 * 1024
    upload_request_overhead_bytes: int = 1024 * 1024
    
    # Application settings
    app_name: str = "AI CV Tailor"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # CORS settings
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    cors_origin_regex: str = (
        r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$|"
        r"^https://.*\.vercel\.app$"
    )
    
    # Default options
    default_strictness: Literal["conservative", "moderate", "aggressive"] = "moderate"
    default_output_format: Literal["markdown", "docx", "pdf", "json"] = "markdown"
    default_language: str = "en"
    
    # LLM settings
    gemini_model: str = "gemini-3.1-pro-preview"
    max_retries: int = 3

    # Rate limiting
    rate_limit_storage_uri: str = "redis://localhost:6379/0"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        """Support both JSON arrays and comma-separated CORS origin strings."""
        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned:
                return []
            if cleaned.startswith("["):
                return value
            return [origin.strip() for origin in cleaned.split(",") if origin.strip()]
        return value


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

"""
Application configuration settings.
Uses environment variables for sensitive data.
"""
from pydantic_settings import BaseSettings
from typing import Literal
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    gemini_api_key: str = ""
    
    # Application settings
    app_name: str = "AI CV Tailor"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # CORS settings
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Default options
    default_strictness: Literal["conservative", "moderate", "aggressive"] = "moderate"
    default_output_format: Literal["markdown", "docx", "pdf", "json"] = "markdown"
    default_language: str = "en"
    
    # LLM settings
    gemini_model: str = "gemini-pro"
    max_retries: int = 3
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

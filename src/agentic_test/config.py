"""Application settings loaded from environment and optional `.env` file."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _env_file() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / ".env"
        if candidate.is_file():
            return candidate
    for parent in here.parents:
        if (parent / "pyproject.toml").exists():
            return parent / ".env"
    return Path.cwd() / ".env"


class Settings(BaseSettings):
    """Service configuration for local or Docker deployment."""

    model_config = SettingsConfigDict(
        env_file=_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mongodb_uri: str = Field(default="mongodb://localhost:27017")
    mongodb_database: str = Field(default="microblog")
    messages_collection: str = Field(default="messages")
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    mongodb_ping_on_startup: bool = Field(default=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()

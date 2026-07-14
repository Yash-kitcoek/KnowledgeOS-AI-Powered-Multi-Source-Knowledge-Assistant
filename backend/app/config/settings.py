"""Validated, environment-driven application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables or an optional .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="KNOWLEDGEOS_",
        extra="ignore",
    )

    app_name: str = "KnowledgeOS"
    environment: str = "development"
    database_path: Path = Path("backend/data/knowledgeos.db")
    upload_directory: Path = Path("backend/data/uploads")
    max_upload_size_bytes: int = Field(default=100 * 1024 * 1024, gt=0)
    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "llama3.2"
    ollama_embedding_model: str = "nomic-embed-text"
    retrieval_limit: int = Field(default=6, ge=1, le=20)


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings object for dependency injection."""

    return Settings()

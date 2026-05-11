from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./shortener.db"
    base_url: str = "http://localhost:8000"
    code_length: int = 5
    max_retries: int = 5
    log_level: str = "INFO"

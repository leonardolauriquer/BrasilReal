from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Brasil Real API"
    data_mode: str = "fixtures"  # fixtures | postgres
    database_url: str = "postgresql+psycopg://brasilreal:brasilreal_dev_only@localhost:5432/brasilreal"
    api_cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3010",
        "http://127.0.0.1:3010",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]
    fixtures_root: str = ""
    seed_on_startup: bool = True

    @field_validator("api_cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            raw = value.strip()
            if raw.startswith("["):
                return list(json.loads(raw))
            return [part.strip() for part in raw.split(",") if part.strip()]
        return value

    @property
    def cors_origins(self) -> list[str]:
        return self.api_cors_origins


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

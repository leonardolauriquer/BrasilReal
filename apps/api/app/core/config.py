from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    app_name: str = "Brasil Real API"
    data_mode: str = Field(
        default="fixtures",  # fixtures | postgres
        validation_alias=AliasChoices("DATA_MODE", "BR_DATA_MODE", "data_mode"),
    )
    database_url: str = Field(
        default="postgresql+psycopg://brasilreal:brasilreal_dev_only@localhost:5432/brasilreal",
        validation_alias=AliasChoices("DATABASE_URL", "BR_DATABASE_URL", "database_url"),
    )
    api_cors_origins: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3010",
            "http://127.0.0.1:3010",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
            "https://brasilreal-atlas.web.app",
            "https://brasilreal-atlas.firebaseapp.com",
        ],
        validation_alias=AliasChoices("API_CORS_ORIGINS", "BR_API_CORS_ORIGINS", "api_cors_origins"),
    )
    fixtures_root: str = Field(
        default="",
        validation_alias=AliasChoices("FIXTURES_ROOT", "BR_FIXTURES_ROOT", "fixtures_root"),
    )
    seed_on_startup: bool = Field(
        default=True,
        validation_alias=AliasChoices("SEED_ON_STARTUP", "BR_SEED_ON_STARTUP", "seed_on_startup"),
    )

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

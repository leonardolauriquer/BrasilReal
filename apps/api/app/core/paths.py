"""Filesystem roots shared by store, freshness and live IBGE clients."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root() -> Path:
    # apps/api/app/core/paths.py -> repo root is parents[4]
    return Path(__file__).resolve().parents[4]


def fixtures_root() -> Path:
    if settings.fixtures_root:
        return Path(settings.fixtures_root)
    return repo_root() / "data" / "fixtures"

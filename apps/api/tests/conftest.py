from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

from app.core.store import store  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _reload_store():
    store.scenarios.clear()
    store.runs.clear()
    store.load()
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

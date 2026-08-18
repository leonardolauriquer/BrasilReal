"""Brasil Real API — FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.store import store
from app.routers import geographies, health, indicators, legal, observations, scenarios, share


@asynccontextmanager
async def lifespan(_: FastAPI):
    store.load()
    yield


app = FastAPI(
    title="Brasil Real API",
    version="0.1.0",
    description=(
        "API do simulador educacional Brasil Real. "
        "Não é fonte oficial, parecer jurídico nem sistema de decisão pública."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(share.router)
app.include_router(geographies.router, prefix="/v1")
app.include_router(indicators.router, prefix="/v1")
app.include_router(observations.router, prefix="/v1")
app.include_router(legal.router, prefix="/v1")
app.include_router(scenarios.router, prefix="/v1")

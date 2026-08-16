from fastapi import APIRouter

from app.core.store import store

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "brasil-real-api"}


@router.get("/ready")
def ready() -> dict:
    if not store.loaded:
        return {
            "fixtures_loaded": False,
            "integrity": "pending",
            "uf_count": 0,
            "indicator_layers": 0,
        }
    uf_count = len(store.population.get("records") or [])
    integrity = "ok" if uf_count == 27 else "uf_coverage_fail"
    return {
        "fixtures_loaded": True,
        "integrity": integrity,
        "uf_count": uf_count,
        "indicator_layers": len(store.social)
        + (1 if store.population else 0)
        + (1 if store.pib else 0),
        "manifest": True,
    }

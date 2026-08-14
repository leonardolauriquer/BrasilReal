from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def ready() -> dict[str, str | bool]:
    from app.core.store import store

    return {"status": "ready", "fixtures_loaded": store.loaded}

from fastapi import APIRouter

from app.core.store import store

router = APIRouter(tags=["indicators"])


@router.get("/indicators")
def list_indicators() -> dict:
    items = store.list_indicators()
    return {"count": len(items), "items": items}

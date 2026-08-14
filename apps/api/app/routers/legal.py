from fastapi import APIRouter, HTTPException

from app.core.store import store

router = APIRouter(tags=["legal"])


@router.get("/legal-instruments")
def list_legal_instruments() -> dict:
    return {"count": len(store.legal_instruments), "items": store.legal_instruments}


@router.get("/legal-instruments/{instrument_id}")
def get_legal_instrument(instrument_id: str) -> dict:
    for item in store.legal_instruments:
        if item["id"] == instrument_id:
            return item
    raise HTTPException(status_code=404, detail="Instrumento legal não encontrado")

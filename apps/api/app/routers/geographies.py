from fastapi import APIRouter, HTTPException, Query

from app.core.store import store
from app.services import freshness, ibge_live

router = APIRouter(tags=["geographies"])


@router.get("/geographies")
def list_geographies(level: str = Query(default="state")) -> dict:
    items = store.list_geographies(level=level)
    return {"count": len(items), "items": items}


@router.get("/indicators/{indicator_id}/periods")
def indicator_periods(
    indicator_id: str,
    refresh: bool = Query(
        default=False,
        description="Ignora TTL e reconsulta a fonte oficial (IBGE) quando aplicável.",
    ),
) -> dict:
    """Lista períodos oficiais; por padrão revalida cache se TTL expirou e devolve `latest`."""
    try:
        resolved = freshness.resolve_periods(indicator_id, force=refresh)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Falha ao listar períodos: {exc}") from exc
    if not resolved["items"]:
        raise HTTPException(status_code=404, detail=f"Sem períodos para {indicator_id}")
    return resolved


# More specific than /geographies/{code}/profile — must be registered first.
@router.get("/geographies/states/{uf_code}/municipalities")
def state_municipalities(
    uf_code: str,
    period: str | None = Query(default=None),
) -> dict:
    """Municipal malha + population for one UF (loaded on zoom)."""
    try:
        if not period:
            period = freshness.ensure_latest_period("population") or "2025"
        geo = ibge_live.fetch_municipality_geo(uf_code)
        values = ibge_live.fetch_municipality_population(uf_code, period=period)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Falha municipal: {exc}") from exc

    by_code = {v["ibge_code"]: v for v in values}
    features = []
    for feature in geo.get("features", []):
        props = dict(feature.get("properties") or {})
        code = str(props.get("codarea") or props.get("id") or "")
        meta = by_code.get(code, {})
        features.append(
            {
                **feature,
                "properties": {
                    **props,
                    "ibge_code": code,
                    "name": meta.get("name") or props.get("name") or code,
                    "value": meta.get("value"),
                    "uf_code": uf_code,
                    "level": "municipality",
                },
            }
        )
    return {
        "uf_code": uf_code,
        "period": period,
        "indicator": "population",
        "status_label": "ESTIMADO",
        "definition": (
            "Estimativa da população residente municipal (IBGE agregados 6579), "
            "exibida no zoom do mapa."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": f"Agregados 6579 / malha municipal / {period}",
            "url": "https://sidra.ibge.gov.br/tabela/6579",
            "malha": "API Malhas (qualidade mínima)",
        },
        "count": len(features),
        "geojson": {"type": "FeatureCollection", "features": features},
        "values": values,
    }


@router.get("/geographies/municipalities/{code}/profile")
def municipality_profile(code: str) -> dict:
    profile = store.municipality_profile(code)
    if not profile:
        raise HTTPException(status_code=404, detail="Município não encontrado ou código inválido")
    return profile


@router.get("/geographies/{code}/profile")
def geography_profile(code: str) -> dict:
    profile = store.profile(code)
    if not profile:
        raise HTTPException(status_code=404, detail="UF não encontrada")
    return profile


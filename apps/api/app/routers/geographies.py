from fastapi import APIRouter, HTTPException, Query

from app.core.store import store
from app.services import ibge_live

router = APIRouter(tags=["geographies"])


@router.get("/geographies")
def list_geographies(level: str = Query(default="state")) -> dict:
    items = store.list_geographies(level=level)
    return {"count": len(items), "items": items}


@router.get("/indicators/{indicator_id}/periods")
def indicator_periods(indicator_id: str) -> dict:
    # Fixture-backed series (ex.: Ipeadata) first — avoid empty/502 for non-IBGE layers.
    fixture_periods = store.indicator_periods(indicator_id)
    if fixture_periods and indicator_id not in ibge_live.INDICATOR_AGGREGATES:
        return {"indicator": indicator_id, "count": len(fixture_periods), "items": fixture_periods}
    try:
        periods = ibge_live.list_periods(indicator_id)
    except Exception as exc:  # noqa: BLE001
        if fixture_periods:
            return {"indicator": indicator_id, "count": len(fixture_periods), "items": fixture_periods}
        raise HTTPException(status_code=502, detail=f"Falha ao listar períodos: {exc}") from exc
    if not periods and fixture_periods:
        periods = fixture_periods
    return {"indicator": indicator_id, "count": len(periods), "items": periods}


# More specific than /geographies/{code}/profile — must be registered first.
@router.get("/geographies/states/{uf_code}/municipalities")
def state_municipalities(
    uf_code: str,
    period: str = Query(default="2025"),
) -> dict:
    """Municipal malha + population for one UF (loaded on zoom)."""
    try:
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


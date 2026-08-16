from fastapi import APIRouter, HTTPException, Query
from pydantic import ValidationError

from app.core.data_integrity import (
    enforce_additive_totals,
    enforce_uf_coverage,
    gate_observation_rows,
    log_integrity_drops,
)
from app.core.store import store
from app.schemas.observations import ObservationOut, ObservationsResponse
from app.services import freshness

router = APIRouter(tags=["observations"])


@router.get("/observations")
def list_observations(
    indicator: str | None = Query(default=None),
    geography: str | None = Query(default=None),
    period: str | None = Query(default=None),
    series: bool = Query(
        default=False,
        description="Série oficial completa de uma UF. Exige indicator e geography.",
    ),
    refresh: bool = Query(
        default=False,
        description="Força revalidação do cache de períodos/série IBGE (TTL ignorado).",
    ),
) -> dict:
    """Observações UF. Sem `period`, resolve automaticamente o mais recente (+ cache)."""
    if series:
        if not indicator or not geography:
            raise HTTPException(
                status_code=422,
                detail="series=true exige indicator e geography",
            )
        raw_series = store.observation_series(indicator, geography)
        result = {
            "items": raw_series,
            "resolved_period": None,
            "live_fallback": False,
            "live_error": None,
            "freshness": None,
        }
    else:
        result = freshness.observations_with_freshness(
            indicator,
            period,
            geography,
            prefer_latest=True,
            force=refresh,
        )
    raw_items = result["items"]
    items, dropped = gate_observation_rows(raw_items)
    resolved = result.get("resolved_period")

    schema_rejected = 0
    modeled: list[dict] = []
    for row in items:
        try:
            modeled.append(ObservationOut.model_validate(row).model_dump())
        except ValidationError:
            schema_rejected += 1
            dropped.append(
                {
                    "indicator": str(row.get("indicator") or indicator or "*"),
                    "geography": str(row.get("geography_ibge_code") or "*"),
                    "reason": "schema_reject",
                }
            )
    items = modeled

    items, dropped, coverage_ok = enforce_uf_coverage(
        items,
        dropped,
        indicator=indicator,
        geography=geography,
    )

    pop_ok = None
    pib_ok = None
    if not geography and not series:
        if indicator == "population":
            items, dropped, pop_ok = enforce_additive_totals(
                items,
                dropped,
                indicator="population",
                expected_total=store.population.get("brazil_total"),
                field="brazil_total",
            )
        elif indicator == "pib":
            items, dropped, pib_ok = enforce_additive_totals(
                items,
                dropped,
                indicator="pib",
                expected_total=(store.pib or {}).get("brazil_total_brl"),
                field="brazil_total_brl",
                tolerance=1.0,
            )

    log_integrity_drops(
        indicator=indicator,
        raw_count=len(raw_items),
        kept_count=len(items),
        dropped=dropped,
    )

    meta = {
        "population_brazil_total": store.population.get("brazil_total"),
        "population_reference_date": store.population.get("reference_date"),
        "population_dataset_id": store.population.get("dataset_id"),
        "population_checksum_sha256": store.population.get("checksum_sha256"),
        "pib_brazil_total_brl": store.pib.get("brazil_total_brl") if store.pib else None,
        "pib_reference_period": store.pib.get("reference_period") if store.pib else None,
        "pib_dataset_id": store.pib.get("dataset_id") if store.pib else None,
        "requested_period": period,
        "resolved_period": resolved,
        "live_fallback": bool(result.get("live_fallback")),
        "live_error": result.get("live_error"),
        "freshness": result.get("freshness"),
        "period_resolved": None if not period else bool(items),
        "period_miss": bool(period) and not items,
        "integrity": {
            "gated": True,
            "raw_count": len(raw_items),
            "kept_count": len(items),
            "dropped_count": len(dropped),
            "dropped": dropped[:50],
            "coverage_ok": coverage_ok,
            "population_reconcile_ok": pop_ok,
            "pib_reconcile_ok": pib_ok,
            "schema_rejected": schema_rejected,
        },
    }
    return ObservationsResponse(count=len(items), meta=meta, items=items).model_dump()

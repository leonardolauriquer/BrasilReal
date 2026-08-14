from fastapi import APIRouter, HTTPException, Query

from app.core.store import store
from app.services import ibge_live

router = APIRouter(tags=["observations"])


def _unit_for(indicator: str) -> str:
    return {
        "population": "habitantes",
        "pib": "BRL",
        "poverty_rate": "%",
        "literacy_rate": "%",
        "unemployment_rate": "%",
    }.get(indicator, "")


def _label_for(indicator: str) -> str:
    return {
        "population": "ESTIMADO",
        "pib": "ESTIMADO",
        "poverty_rate": "ESTIMADO",
        "literacy_rate": "OBSERVADO",
        "unemployment_rate": "ESTIMADO",
    }.get(indicator, "ESTIMADO")


@router.get("/observations")
def list_observations(
    indicator: str | None = Query(default=None),
    geography: str | None = Query(default=None),
    period: str | None = Query(default=None),
) -> dict:
    items = store.observations(indicator=indicator, geography=geography, period=period)

    # If a specific period was requested and fixtures don't cover it, fetch live IBGE.
    live_error: str | None = None
    if indicator and period and not items and indicator in ibge_live.INDICATOR_AGGREGATES:
        try:
            available = set(ibge_live.list_periods(indicator))
            if period not in available:
                live_error = f"Período {period} indisponível para {indicator}."
            else:
                rows = ibge_live.fetch_uf_series(indicator, period)
                geo_by_code = {g["ibge_code"]: g for g in store.list_geographies()}
                unit = _unit_for(indicator)
                for row in rows:
                    g = geo_by_code.get(row["ibge_code"], {})
                    if geography and geography not in {row["ibge_code"], g.get("uf")}:
                        continue
                    items.append(
                        {
                            "indicator": indicator,
                            "geography_ibge_code": row["ibge_code"],
                            "uf": g.get("uf", ""),
                            "name": g.get("name") or row["name"],
                            "value": row["value"],
                            "unit": unit,
                            "reference_period": period,
                            "release_date": None,
                            "status_label": _label_for(indicator),
                            "evidence_grade": "A",
                            "higher_is_worse": indicator
                            in {
                                "poverty_rate",
                                "unemployment_rate",
                                "homicide_rate",
                                "homicide_count",
                                "traffic_death_rate",
                            },
                            "source": {
                                "organization": "IBGE",
                                "dataset": f"Agregados sob demanda / {indicator} / {period}",
                                "method_notes": "Série sob demanda via API de Agregados (cache local).",
                            },
                            "dataset_id": f"ibge.{indicator}.{period}",
                            "quality": "official_estimate",
                        }
                    )
        except Exception as exc:  # noqa: BLE001
            live_error = str(exc)

    meta = {
        "population_brazil_total": store.population.get("brazil_total"),
        "population_reference_date": store.population.get("reference_date"),
        "population_dataset_id": store.population.get("dataset_id"),
        "population_checksum_sha256": store.population.get("checksum_sha256"),
        "pib_brazil_total_brl": store.pib.get("brazil_total_brl") if store.pib else None,
        "pib_reference_period": store.pib.get("reference_period") if store.pib else None,
        "pib_dataset_id": store.pib.get("dataset_id") if store.pib else None,
        "requested_period": period,
        "live_fallback": bool(indicator and period and items),
        "live_error": live_error,
    }
    return {"count": len(items), "meta": meta, "items": items}

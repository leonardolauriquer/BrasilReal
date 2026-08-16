"""Build the public indicator list from loaded fixtures + territory catalog."""

from __future__ import annotations

from typing import Any, Protocol

from app.core.source_normalize import normalize_source


class _StoreView(Protocol):
    population: dict[str, Any]
    pib: dict[str, Any]
    social: dict[str, dict[str, Any]]
    territory_catalog: dict[str, Any]


def list_indicators(store: _StoreView) -> list[dict[str, Any]]:
    metric_specs = store.territory_catalog.get("metrics") or {}
    items: list[dict[str, Any]] = [
        {
            "id": "population",
            "name": "População residente estimada",
            "short_name": "População",
            "unit": "habitantes",
            "status_label": "ESTIMADO",
            "frequency": "annual",
            "source_dataset": store.population["dataset_id"],
            "kind": "observed_estimate",
            "higher_is_worse": False,
            "group": "economia",
            "group_label": "Economia / demografia",
            "reference_period": store.population.get("reference_date"),
            **{
                k: v
                for k, v in (metric_specs.get("population") or {}).items()
                if k in {"definition", "source", "limitations"}
            },
        },
    ]
    if store.pib:
        items.append(
            {
                "id": "pib",
                "name": "PIB a preços correntes",
                "short_name": "PIB",
                "unit": "BRL",
                "status_label": "ESTIMADO",
                "frequency": "annual",
                "source_dataset": store.pib["dataset_id"],
                "kind": "observed_estimate",
                "higher_is_worse": False,
                "group": "economia",
                "group_label": "Economia / demografia",
                "reference_period": store.pib.get("reference_period"),
                **{
                    k: v
                    for k, v in (metric_specs.get("pib") or {}).items()
                    if k in {"definition", "source", "limitations"}
                },
            }
        )
    for ind in store.social.values():
        ind_id = ind["indicator_id"]
        meta = metric_specs.get(ind_id) or {}
        item: dict[str, Any] = {
            "id": ind_id,
            "name": ind.get("name") or ind["title"].split(" — ")[0],
            "short_name": ind.get("short_name", ind_id),
            "unit": ind["unit"],
            "status_label": ind["status_label"],
            "frequency": ind.get("frequency"),
            "source_dataset": ind["dataset_id"],
            "kind": ind.get("kind", "observed_estimate"),
            "higher_is_worse": ind.get("higher_is_worse", False),
            "group": ind.get("group") or "social",
            "group_label": ind.get("group_label") or "Social",
            "reference_period": ind.get("reference_period"),
            "available_periods": ind.get("available_periods"),
        }
        for key in ("definition", "source", "limitations"):
            if ind.get(key):
                item[key] = ind[key]
            elif meta.get(key):
                item[key] = meta[key]
        src = item.get("source")
        if isinstance(src, dict) and "dataset" not in src:
            item["source"] = normalize_source(src, fallback_dataset=ind.get("dataset_id"))
        items.append(item)
    return items


def indicator_periods(store: _StoreView, indicator_id: str) -> list[str]:
    if indicator_id == "population":
        ref = str(store.population.get("reference_date") or "")
        year = ref[:4]
        return [p for p in (year, ref) if p]
    if indicator_id == "pib" and store.pib:
        ref = str(store.pib.get("reference_period") or "")
        return [ref] if ref else []
    fixture = store.social.get(indicator_id)
    if not fixture:
        return []
    periods = fixture.get("available_periods")
    if isinstance(periods, list) and periods:
        return [str(p) for p in periods]
    ref = str(fixture.get("reference_period") or "")
    return [ref] if ref else []

"""Observation rows from in-memory fixtures (population, PIB, social)."""

from __future__ import annotations

from typing import Any, Protocol

from app.core.source_normalize import normalize_source


class _StoreView(Protocol):
    population: dict[str, Any]
    pib: dict[str, Any]
    social: dict[str, dict[str, Any]]
    territory_catalog: dict[str, Any]


def _series_records(
    series: dict[str, Any],
    period: str,
) -> tuple[list[Any] | None, str | None]:
    """Exact period key only — never truncate YYYYTn → YYYY (mislabel risk)."""
    if period in series:
        records = series.get(period)
        if isinstance(records, list) and records:
            return records, period
    return None, None


def observations(
    store: _StoreView,
    indicator: str | None = None,
    geography: str | None = None,
    period: str | None = None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    pib_ref = str(store.pib.get("reference_period") or "") if store.pib else ""

    if indicator in (None, "population"):
        pop_ref = store.population["reference_date"]
        pop_year = str(pop_ref)[:4]
        metric_specs = store.territory_catalog.get("metrics") or {}
        pop_meta = metric_specs.get("population") or {}
        pop_src = store.population.get("source") or {}
        pop_source = normalize_source(
            {
                **pop_src,
                **(pop_meta.get("source") or {}),
            },
            fallback_dataset=store.population.get("dataset_id"),
        )
        # Accept full ref or calendar year — not election-style YYYYTn.
        if not period or period in {pop_ref, pop_year}:
            for r in store.population["records"]:
                if geography and geography not in {r["ibge_code"], r["uf"]}:
                    continue
                out.append(
                    {
                        "indicator": "population",
                        "geography_ibge_code": r["ibge_code"],
                        "uf": r["uf"],
                        "name": r["name"],
                        "value": r["population"],
                        "unit": "habitantes",
                        "reference_period": pop_ref,
                        "release_date": store.population["release_date"],
                        "status_label": "ESTIMADO",
                        "evidence_grade": "A",
                        "higher_is_worse": False,
                        "source": pop_source,
                        "dataset_id": store.population["dataset_id"],
                        "quality": "official_estimate",
                        "definition": pop_meta.get("definition"),
                        "limitations": pop_meta.get("limitations"),
                    }
                )

    if indicator in (None, "pib") and store.pib:
        metric_specs = store.territory_catalog.get("metrics") or {}
        pib_meta = metric_specs.get("pib") or {}
        pib_source = normalize_source(
            {
                **(store.pib.get("source") or {}),
                **(pib_meta.get("source") or {}),
            },
            fallback_dataset=store.pib.get("dataset_id"),
        )
        pib_year = pib_ref[:4] if pib_ref else ""
        if not period or period in {pib_ref, pib_year, store.pib.get("reference_date", "")}:
            for r in store.pib["records"]:
                if geography and geography not in {r["ibge_code"], r["uf"]}:
                    continue
                out.append(
                    {
                        "indicator": "pib",
                        "geography_ibge_code": r["ibge_code"],
                        "uf": r["uf"],
                        "name": r["name"],
                        "value": r["pib_brl"],
                        "unit": "BRL",
                        "reference_period": pib_ref,
                        "release_date": store.pib.get("release_date"),
                        "status_label": "ESTIMADO",
                        "evidence_grade": "A",
                        "higher_is_worse": False,
                        "source": pib_source,
                        "dataset_id": store.pib["dataset_id"],
                        "quality": "official_estimate",
                        "definition": pib_meta.get("definition") or store.pib.get("definition"),
                        "limitations": store.pib.get("limitations", [])
                        or pib_meta.get("limitations"),
                    }
                )

    for ind_id, fixture in store.social.items():
        if indicator not in (None, ind_id):
            continue
        series = fixture.get("series") if isinstance(fixture.get("series"), dict) else None
        default_ref = str(fixture.get("reference_period") or "")
        default_year = default_ref[:4] if default_ref else ""
        if period and series:
            records, ref = _series_records(series, period)
        elif period:
            # Non-series fixture: accept exact ref or its calendar year only.
            if period not in {default_ref, default_year}:
                continue
            records = fixture.get("records") or []
            ref = default_ref
        else:
            records = fixture.get("records") or []
            ref = default_ref
        if not records or not ref:
            continue
        metric_specs = store.territory_catalog.get("metrics") or {}
        meta = metric_specs.get(ind_id) or {}
        src = normalize_source(
            {
                **(fixture.get("source") or {}),
                **(meta.get("source") or {}),
            },
            fallback_dataset=fixture.get("dataset_id"),
        )
        definition = fixture.get("definition") or meta.get("definition")
        limitations = list(fixture.get("limitations") or meta.get("limitations") or [])
        if not definition:
            # Fail closed at row build — never emit unlabeled social metrics.
            continue
        for r in records:
            if geography and geography not in {r["ibge_code"], r["uf"]}:
                continue
            out.append(
                {
                    "indicator": ind_id,
                    "geography_ibge_code": r["ibge_code"],
                    "uf": r["uf"],
                    "name": r["name"],
                    "value": r["value"],
                    "unit": fixture["unit"],
                    "reference_period": ref,
                    "release_date": fixture.get("release_date"),
                    "status_label": fixture["status_label"],
                    "evidence_grade": fixture.get("evidence_grade", "A"),
                    "higher_is_worse": fixture.get("higher_is_worse", False),
                    "source": src,
                    "dataset_id": fixture["dataset_id"],
                    "quality": "official_estimate",
                    "limitations": limitations,
                    "short_name": fixture.get("short_name"),
                    "definition": definition,
                }
            )
    return out

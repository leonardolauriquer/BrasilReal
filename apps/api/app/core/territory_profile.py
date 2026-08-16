"""Territory fiche rows (UF / municipality) from catalog + fixtures."""

from __future__ import annotations

from typing import Any, Protocol

from app.services.territory_fiche import make_item


class _StoreView(Protocol):
    population: dict[str, Any]
    territory: dict[str, Any]
    territory_catalog: dict[str, Any]


def _push(items: list[dict[str, Any]], item: dict[str, Any] | None) -> None:
    if item:
        items.append(item)


def territory_items_uf(store: _StoreView, code: str, _geo: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    specs = store.territory_catalog.get("territory") or {}

    ind = (store.territory.get("indigenous_2022") or {}).get("by_uf", {}).get(code, {})
    if "indigenous_population" in specs:
        _push(
            items,
            make_item(
                specs["indigenous_population"],
                value=ind.get("indigenous_population"),
                reference_period="2022",
            ),
        )
    if "indigenous_share" in specs:
        _push(
            items,
            make_item(
                specs["indigenous_share"],
                value=ind.get("indigenous_share"),
                reference_period="2022",
            ),
        )

    quil = (store.territory.get("quilombola_2022") or {}).get("by_uf", {}).get(code, {})
    if "quilombola_residents" in specs:
        _push(
            items,
            make_item(
                specs["quilombola_residents"],
                value=quil.get("quilombola_residents"),
                reference_period="2022",
            ),
        )

    area_row = (store.territory.get("area_2010") or {}).get("by_uf", {}).get(code, {})
    area_val = area_row.get("area_km2")
    if "area_km2" in specs:
        _push(items, make_item(specs["area_km2"], value=area_val, reference_period="2010"))

    pop_row = next(
        (r for r in store.population.get("records", []) if r["ibge_code"] == code),
        None,
    )
    if "population_density" in specs and area_val and pop_row and area_val > 0:
        density = float(pop_row["population"]) / float(area_val)
        _push(
            items,
            make_item(
                specs["population_density"],
                value=round(density, 2),
                reference_period=f"{store.population.get('reference_date', '?')} ÷ 2010",
            ),
        )
    elif "population_density" in specs:
        _push(items, make_item(specs["population_density"], value=None))

    biome_uf = (store.territory.get("biomes_2024") or {}).get("by_uf", {}).get(code, {})
    if "biomes_present" in specs:
        _push(
            items,
            make_item(
                specs["biomes_present"],
                text=biome_uf.get("text"),
                reference_period="2024",
            ),
        )

    return items


def territory_items_mun(store: _StoreView, code: str, _geo: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    specs = store.territory_catalog.get("territory") or {}

    ind = (store.territory.get("indigenous_2022") or {}).get("by_mun", {}).get(code, {})
    if "indigenous_population" in specs:
        _push(
            items,
            make_item(
                specs["indigenous_population"],
                value=ind.get("indigenous_population"),
                reference_period="2022",
            ),
        )
    if "indigenous_share" in specs:
        _push(
            items,
            make_item(
                specs["indigenous_share"],
                value=ind.get("indigenous_share"),
                reference_period="2022",
            ),
        )

    quil = (store.territory.get("quilombola_2022") or {}).get("by_mun", {}).get(code, {})
    if "quilombola_residents" in specs:
        _push(
            items,
            make_item(
                specs["quilombola_residents"],
                value=quil.get("quilombola_residents"),
                reference_period="2022",
            ),
        )

    area_row = (store.territory.get("area_2010") or {}).get("by_mun", {}).get(code, {})
    area_val = area_row.get("area_km2")
    if "area_km2" in specs:
        _push(items, make_item(specs["area_km2"], value=area_val, reference_period="2010"))

    biome = (store.territory.get("biomes_2024") or {}).get("by_mun", {}).get(code, {})
    if "biome_predominant" in specs:
        _push(
            items,
            make_item(
                specs["biome_predominant"],
                text=biome.get("biome_predominant"),
                reference_period="2024",
            ),
        )

    coastal_codes = set((store.territory.get("coastal_marine") or {}).get("codes") or [])
    if "coastal_marine" in specs:
        if coastal_codes:
            _push(
                items,
                make_item(
                    specs["coastal_marine"],
                    text="Sim" if code in coastal_codes else "Não",
                    reference_period="2019",
                ),
            )
        else:
            _push(items, make_item(specs["coastal_marine"], value=None))

    return items

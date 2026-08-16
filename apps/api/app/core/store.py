"""In-memory fixture store — thin facade over focused core modules."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from app.core import indicator_catalog, observations_query, scenario_ops, territory_profile
from app.core.data_integrity import (
    FIXTURE_INDICATOR_RELDIRS,
    gate_observation_rows,
    validate_disk_locks,
    validate_loaded_store,
)
from app.core.paths import fixtures_root, repo_root
from app.services.territory_fiche import enrich_metric

# Re-export for freshness / ibge_live / tests
__all__ = ["InMemoryStore", "store", "repo_root", "fixtures_root"]


@dataclass
class InMemoryStore:
    population: dict[str, Any] = field(default_factory=dict)
    pib: dict[str, Any] = field(default_factory=dict)
    social: dict[str, dict[str, Any]] = field(default_factory=dict)
    territory: dict[str, Any] = field(default_factory=dict)
    territory_catalog: dict[str, Any] = field(default_factory=dict)
    legal_instruments: list[dict[str, Any]] = field(default_factory=list)
    scenarios: dict[str, dict[str, Any]] = field(default_factory=dict)
    runs: dict[str, dict[str, Any]] = field(default_factory=dict)
    loaded: bool = False

    def load(self) -> None:
        pop_path = fixtures_root() / "ibge" / "population_uf_2025.json"
        pib_path = fixtures_root() / "ibge" / "pib_uf_latest.json"
        legal_path = fixtures_root() / "legal" / "lgpd_catalog.json"
        self.population = json.loads(pop_path.read_text(encoding="utf-8"))
        self.pib = json.loads(pib_path.read_text(encoding="utf-8")) if pib_path.exists() else {}
        self.social = {}
        for rel in FIXTURE_INDICATOR_RELDIRS:
            social_dir = fixtures_root() / rel
            if not social_dir.exists():
                continue
            for path in sorted(social_dir.glob("*_latest.json")):
                payload = json.loads(path.read_text(encoding="utf-8"))
                self.social[payload["indicator_id"]] = payload
        self.legal_instruments = [json.loads(legal_path.read_text(encoding="utf-8"))]
        self._load_territory()
        if not self.scenarios:
            scenario_ops.ensure_default_scenario(self)
        validate_loaded_store(self)
        validate_disk_locks(fixtures_root())
        self.loaded = True

    def _load_territory(self) -> None:
        root = fixtures_root() / "territory"
        self.territory = {}
        self.territory_catalog = {}
        if not root.exists():
            return
        catalog_path = root / "catalog.json"
        if catalog_path.exists():
            self.territory_catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        for name in (
            "indigenous_2022",
            "quilombola_2022",
            "area_2010",
            "biomes_2024",
            "coastal_marine",
        ):
            path = root / f"{name}.json"
            if path.exists():
                self.territory[name] = json.loads(path.read_text(encoding="utf-8"))

    def list_geographies(self, level: str = "state") -> list[dict[str, Any]]:
        if level != "state":
            return []
        return [
            {
                "ibge_code": r["ibge_code"],
                "uf": r["uf"],
                "name": r["name"],
                "level": "state",
                "country": "BR",
            }
            for r in self.population["records"]
        ]

    def list_indicators(self) -> list[dict[str, Any]]:
        return indicator_catalog.list_indicators(self)

    def indicator_periods(self, indicator_id: str) -> list[str]:
        return indicator_catalog.indicator_periods(self, indicator_id)

    def observations(
        self,
        indicator: str | None = None,
        geography: str | None = None,
        period: str | None = None,
    ) -> list[dict[str, Any]]:
        return observations_query.observations(self, indicator, geography, period)

    def profile(self, geography: str) -> dict[str, Any] | None:
        geos = self.list_geographies()
        match = next((g for g in geos if geography in {g["ibge_code"], g["uf"]}), None)
        if not match:
            return None
        code = match["ibge_code"]
        metrics = self.observations(geography=code)
        metrics, gated_drops = gate_observation_rows(metrics)
        by_ind: dict[str, dict[str, Any]] = {}
        for row in metrics:
            by_ind[row["indicator"]] = row
        metric_specs = self.territory_catalog.get("metrics") or {}
        enriched_metrics = []
        omitted_metrics: list[dict[str, str]] = []
        for row in by_ind.values():
            enriched = enrich_metric(row, metric_specs)
            if enriched:
                enriched_metrics.append(enriched)
            else:
                omitted_metrics.append(
                    {
                        "indicator": str(row.get("indicator") or ""),
                        "reason": "missing_provenance",
                    }
                )
        for drop in gated_drops:
            omitted_metrics.append(drop)
        territory_items = territory_profile.territory_items_uf(self, code, match)
        return {
            "geography": match,
            "metrics": enriched_metrics,
            "omitted_metrics": omitted_metrics,
            "territory": {"items": territory_items},
            "disclaimer": (
                "Indicadores de anos/pesquisas diferentes; compare com cuidado. "
                "Cada valor traz definição e fonte oficial no tooltip."
            ),
        }

    def municipality_profile(self, mun_code: str) -> dict[str, Any] | None:
        code = str(mun_code)
        if len(code) != 7 or not code.isdigit():
            return None
        uf_code = code[:2]
        uf_geo = next((g for g in self.list_geographies() if g["ibge_code"] == uf_code), None)
        biomes = (self.territory.get("biomes_2024") or {}).get("by_mun", {}).get(code, {})
        indigenous = (self.territory.get("indigenous_2022") or {}).get("by_mun", {}).get(code, {})
        name = (
            biomes.get("name")
            or indigenous.get("name")
            or (self.territory.get("area_2010") or {}).get("by_mun", {}).get(code, {}).get("name")
            or code
        )
        geography = {
            "ibge_code": code,
            "uf": uf_geo["uf"] if uf_geo else uf_code,
            "uf_code": uf_code,
            "name": name,
            "level": "municipality",
            "country": "BR",
        }
        items = territory_profile.territory_items_mun(self, code, geography)
        return {
            "geography": geography,
            "metrics": [],
            "territory": {"items": items},
            "disclaimer": (
                "Atributos territoriais oficiais por município. "
                "População no mapa usa estimativas IBGE 6579 no zoom."
            ),
        }

    def create_scenario(self, title: str, author: str, params: dict[str, str]) -> dict[str, Any]:
        return scenario_ops.create_scenario(self, title, author, params)

    def apply_patch(self, scenario_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        return scenario_ops.apply_patch(self, scenario_id, patch)

    def run_scenario(self, scenario_id: str, seed: int = 42) -> dict[str, Any]:
        return scenario_ops.run_scenario(self, scenario_id, seed)

    def manifest(self, scenario_id: str) -> dict[str, Any]:
        return scenario_ops.manifest(self, scenario_id)


store = InMemoryStore()

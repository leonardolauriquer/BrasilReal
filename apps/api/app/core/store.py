from __future__ import annotations

import json
import uuid
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.services.fund_engine import FundParams, distribute_hypothetical_fund
from app.services.territory_fiche import enrich_metric, make_item


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root() -> Path:
    # apps/api/app/core/store.py -> repo root is parents[4]
    return Path(__file__).resolve().parents[4]


def fixtures_root() -> Path:
    if settings.fixtures_root:
        return Path(settings.fixtures_root)
    return repo_root() / "data" / "fixtures"


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
        for rel in ("ibge/indicators", "ipeadata/indicators", "comex/indicators"):
            social_dir = fixtures_root() / rel
            if not social_dir.exists():
                continue
            for path in sorted(social_dir.glob("*_latest.json")):
                payload = json.loads(path.read_text(encoding="utf-8"))
                self.social[payload["indicator_id"]] = payload
        self.legal_instruments = [json.loads(legal_path.read_text(encoding="utf-8"))]
        self._load_territory()
        if not self.scenarios:
            self._ensure_default_scenario()
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

    def _ensure_default_scenario(self) -> None:
        scenario_id = "scn_baseline_fund_demo"
        self.scenarios[scenario_id] = {
            "id": scenario_id,
            "title": "Fundo federal fictício — linha de base populacional",
            "author": "system",
            "status": "active",
            "is_hypothetical": True,
            "disclaimer": (
                "Cenário explicitamente hipotético. Não representa lei vigente, "
                "fundo real nem política pública em vigor."
            ),
            "cutoff_date": self.population.get("reference_date", "2025-07-01"),
            "baseline": True,
            "created_at": _utc_now(),
            "patches": [],
            "params": {
                "budget_brl": "10000000000.00",
                "population_weight": "1.0",
                "need_weight": "0.0",
            },
        }

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
        metric_specs = self.territory_catalog.get("metrics") or {}
        items = [
            {
                "id": "population",
                "name": "População residente estimada",
                "short_name": "População",
                "unit": "habitantes",
                "status_label": "ESTIMADO",
                "frequency": "annual",
                "source_dataset": self.population["dataset_id"],
                "kind": "observed_estimate",
                "higher_is_worse": False,
                "group": "economia",
                "group_label": "Economia / demografia",
                "reference_period": self.population.get("reference_date"),
                **{
                    k: v
                    for k, v in (metric_specs.get("population") or {}).items()
                    if k in {"definition", "source", "limitations"}
                },
            },
        ]
        if self.pib:
            items.append(
                {
                    "id": "pib",
                    "name": "PIB a preços correntes",
                    "short_name": "PIB",
                    "unit": "BRL",
                    "status_label": "ESTIMADO",
                    "frequency": "annual",
                    "source_dataset": self.pib["dataset_id"],
                    "kind": "observed_estimate",
                    "higher_is_worse": False,
                    "group": "economia",
                    "group_label": "Economia / demografia",
                    "reference_period": self.pib.get("reference_period"),
                    **{
                        k: v
                        for k, v in (metric_specs.get("pib") or {}).items()
                        if k in {"definition", "source", "limitations"}
                    },
                }
            )
        for ind in self.social.values():
            ind_id = ind["indicator_id"]
            meta = metric_specs.get(ind_id) or {}
            item = {
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
            # Normalize fixture source → tooltip shape
            src = item.get("source")
            if isinstance(src, dict) and "dataset" not in src:
                item["source"] = {
                    "organization": src.get("organization") or "",
                    "dataset": src.get("dataset")
                    or src.get("dataset_page")
                    or src.get("sercodigo")
                    or ind.get("dataset_id")
                    or "",
                    "url": src.get("url") or src.get("serie_page") or src.get("dataset_page") or src.get("api_url"),
                }
            items.append(item)
        return items

    def indicator_periods(self, indicator_id: str) -> list[str]:
        if indicator_id == "population":
            ref = str(self.population.get("reference_date") or "")
            year = ref[:4]
            return [p for p in (year, ref) if p]
        if indicator_id == "pib" and self.pib:
            ref = str(self.pib.get("reference_period") or "")
            return [ref] if ref else []
        fixture = self.social.get(indicator_id)
        if not fixture:
            return []
        periods = fixture.get("available_periods")
        if isinstance(periods, list) and periods:
            return [str(p) for p in periods]
        ref = str(fixture.get("reference_period") or "")
        return [ref] if ref else []

    def observations(
        self,
        indicator: str | None = None,
        geography: str | None = None,
        period: str | None = None,
    ) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        pop_ref = self.population["reference_date"]
        pib_ref = str(self.pib.get("reference_period") or "")

        if indicator in (None, "population"):
            if not period or period in {pop_ref, pop_ref[:4], "2025"}:
                for r in self.population["records"]:
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
                            "release_date": self.population["release_date"],
                            "status_label": "ESTIMADO",
                            "evidence_grade": "A",
                            "higher_is_worse": False,
                            "source": self.population["source"],
                            "dataset_id": self.population["dataset_id"],
                            "quality": "official_estimate",
                        }
                    )

        if indicator in (None, "pib") and self.pib:
            if not period or period in {pib_ref, self.pib.get("reference_date", "")}:
                for r in self.pib["records"]:
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
                            "release_date": self.pib.get("release_date"),
                            "status_label": "ESTIMADO",
                            "evidence_grade": "A",
                            "higher_is_worse": False,
                            "source": self.pib["source"],
                            "dataset_id": self.pib["dataset_id"],
                            "quality": "official_estimate",
                            "limitations": self.pib.get("limitations", []),
                        }
                    )

        for ind_id, fixture in self.social.items():
            if indicator not in (None, ind_id):
                continue
            series = fixture.get("series") if isinstance(fixture.get("series"), dict) else None
            default_ref = str(fixture.get("reference_period") or "")
            if period and series:
                records = series.get(period) or series.get(period[:4])
                ref = period if records else None
            elif period:
                if period not in {default_ref, default_ref[:4]}:
                    continue
                records = fixture.get("records") or []
                ref = default_ref
            else:
                records = fixture.get("records") or []
                ref = default_ref
            if not records or not ref:
                continue
            src = fixture.get("source") or {}
            if isinstance(src, dict) and "dataset" not in src:
                src = {
                    "organization": src.get("organization") or "",
                    "dataset": src.get("dataset")
                    or src.get("dataset_page")
                    or src.get("sercodigo")
                    or fixture.get("dataset_id")
                    or "",
                    "url": src.get("url") or src.get("serie_page") or src.get("dataset_page") or src.get("api_url"),
                }
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
                        "limitations": fixture.get("limitations", []),
                        "short_name": fixture.get("short_name"),
                        "definition": fixture.get("definition"),
                    }
                )
        return out

    def profile(self, geography: str) -> dict[str, Any] | None:
        geos = self.list_geographies()
        match = next((g for g in geos if geography in {g["ibge_code"], g["uf"]}), None)
        if not match:
            return None
        code = match["ibge_code"]
        metrics = self.observations(geography=code)
        by_ind: dict[str, dict[str, Any]] = {}
        for row in metrics:
            by_ind[row["indicator"]] = row
        metric_specs = self.territory_catalog.get("metrics") or {}
        enriched_metrics = []
        for row in by_ind.values():
            enriched = enrich_metric(row, metric_specs)
            if enriched:
                enriched_metrics.append(enriched)
        territory_items = self._territory_items_uf(code, match)
        return {
            "geography": match,
            "metrics": enriched_metrics,
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
        # Population for municipality is not in UF fixtures; leave metrics empty
        # or surface zoom-layer note via territory items only.
        items = self._territory_items_mun(code, geography)
        return {
            "geography": geography,
            "metrics": [],
            "territory": {"items": items},
            "disclaimer": (
                "Atributos territoriais oficiais por município. "
                "População no mapa usa estimativas IBGE 6579 no zoom."
            ),
        }

    def _spec(self, key: str) -> dict[str, Any]:
        return (self.territory_catalog.get("territory") or {}).get(key) or {}

    def _push(self, items: list[dict[str, Any]], item: dict[str, Any] | None) -> None:
        if item:
            items.append(item)

    def _territory_items_uf(self, code: str, geo: dict[str, Any]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        specs = self.territory_catalog.get("territory") or {}

        ind = (self.territory.get("indigenous_2022") or {}).get("by_uf", {}).get(code, {})
        if "indigenous_population" in specs:
            self._push(
                items,
                make_item(
                    specs["indigenous_population"],
                    value=ind.get("indigenous_population"),
                    reference_period="2022",
                ),
            )
        if "indigenous_share" in specs:
            self._push(
                items,
                make_item(
                    specs["indigenous_share"],
                    value=ind.get("indigenous_share"),
                    reference_period="2022",
                ),
            )

        quil = (self.territory.get("quilombola_2022") or {}).get("by_uf", {}).get(code, {})
        if "quilombola_residents" in specs:
            self._push(
                items,
                make_item(
                    specs["quilombola_residents"],
                    value=quil.get("quilombola_residents"),
                    reference_period="2022",
                ),
            )

        area_row = (self.territory.get("area_2010") or {}).get("by_uf", {}).get(code, {})
        area_val = area_row.get("area_km2")
        if "area_km2" in specs:
            self._push(items, make_item(specs["area_km2"], value=area_val, reference_period="2010"))

        pop_row = next(
            (r for r in self.population.get("records", []) if r["ibge_code"] == code),
            None,
        )
        if "population_density" in specs and area_val and pop_row and area_val > 0:
            density = float(pop_row["population"]) / float(area_val)
            self._push(
                items,
                make_item(
                    specs["population_density"],
                    value=round(density, 2),
                    reference_period=f"{self.population.get('reference_date', '?')} ÷ 2010",
                ),
            )
        elif "population_density" in specs:
            self._push(items, make_item(specs["population_density"], value=None))

        biome_uf = (self.territory.get("biomes_2024") or {}).get("by_uf", {}).get(code, {})
        if "biomes_present" in specs:
            self._push(
                items,
                make_item(
                    specs["biomes_present"],
                    text=biome_uf.get("text"),
                    reference_period="2024",
                ),
            )

        return items

    def _territory_items_mun(self, code: str, geo: dict[str, Any]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        specs = self.territory_catalog.get("territory") or {}

        ind = (self.territory.get("indigenous_2022") or {}).get("by_mun", {}).get(code, {})
        if "indigenous_population" in specs:
            self._push(
                items,
                make_item(
                    specs["indigenous_population"],
                    value=ind.get("indigenous_population"),
                    reference_period="2022",
                ),
            )
        if "indigenous_share" in specs:
            self._push(
                items,
                make_item(
                    specs["indigenous_share"],
                    value=ind.get("indigenous_share"),
                    reference_period="2022",
                ),
            )

        quil = (self.territory.get("quilombola_2022") or {}).get("by_mun", {}).get(code, {})
        if "quilombola_residents" in specs:
            self._push(
                items,
                make_item(
                    specs["quilombola_residents"],
                    value=quil.get("quilombola_residents"),
                    reference_period="2022",
                ),
            )

        area_row = (self.territory.get("area_2010") or {}).get("by_mun", {}).get(code, {})
        area_val = area_row.get("area_km2")
        if "area_km2" in specs:
            self._push(items, make_item(specs["area_km2"], value=area_val, reference_period="2010"))

        biome = (self.territory.get("biomes_2024") or {}).get("by_mun", {}).get(code, {})
        if "biome_predominant" in specs:
            self._push(
                items,
                make_item(
                    specs["biome_predominant"],
                    text=biome.get("biome_predominant"),
                    reference_period="2024",
                ),
            )

        coastal_codes = set((self.territory.get("coastal_marine") or {}).get("codes") or [])
        if "coastal_marine" in specs:
            if coastal_codes:
                self._push(
                    items,
                    make_item(
                        specs["coastal_marine"],
                        text="Sim" if code in coastal_codes else "Não",
                        reference_period="2019",
                    ),
                )
            else:
                self._push(items, make_item(specs["coastal_marine"], value=None))

        return items

    def create_scenario(self, title: str, author: str, params: dict[str, str]) -> dict[str, Any]:
        scenario_id = f"scn_{uuid.uuid4().hex[:12]}"
        scenario = {
            "id": scenario_id,
            "title": title,
            "author": author,
            "status": "draft",
            "is_hypothetical": True,
            "disclaimer": (
                "Cenário explicitamente hipotético. Não representa lei vigente, "
                "fundo real nem política pública em vigor."
            ),
            "cutoff_date": self.population.get("reference_date", "2025-07-01"),
            "baseline": False,
            "created_at": _utc_now(),
            "patches": [],
            "params": {
                "budget_brl": params.get("budget_brl", "10000000000.00"),
                "population_weight": params.get("population_weight", "0.7"),
                "need_weight": params.get("need_weight", "0.3"),
            },
        }
        self.scenarios[scenario_id] = scenario
        return scenario

    def apply_patch(self, scenario_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        scenario = self.scenarios[scenario_id]
        allowed = {"budget_brl", "population_weight", "need_weight"}
        path = patch.get("path")
        if path not in allowed:
            raise ValueError(f"patch path não permitido: {path}")
        before = scenario["params"].get(path)
        scenario["params"][path] = str(patch["value"])
        entry = {
            "id": f"patch_{uuid.uuid4().hex[:8]}",
            "path": path,
            "before": before,
            "after": scenario["params"][path],
            "at": _utc_now(),
            "note": patch.get("note"),
        }
        scenario["patches"].append(entry)
        scenario["status"] = "patched"
        return scenario

    def run_scenario(self, scenario_id: str, seed: int = 42) -> dict[str, Any]:
        scenario = self.scenarios[scenario_id]
        params = FundParams(
            budget_brl=Decimal(scenario["params"]["budget_brl"]),
            population_weight=Decimal(scenario["params"]["population_weight"]),
            need_weight=Decimal(scenario["params"]["need_weight"]),
        )
        baseline_params = FundParams(
            budget_brl=params.budget_brl,
            population_weight=Decimal("1.0"),
            need_weight=Decimal("0.0"),
        )
        records = self.population["records"]
        result = distribute_hypothetical_fund(records, params, seed=seed)
        baseline = distribute_hypothetical_fund(records, baseline_params, seed=seed)
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        run = {
            "id": run_id,
            "scenario_id": scenario_id,
            "status": "succeeded",
            "seed": seed,
            "created_at": _utc_now(),
            "model": {
                "id": "hypothetical_federal_fund_v1",
                "layer": "A",
                "evidence_grade": "A",
                "description": (
                    "Identidade contábil de rateio: participação = "
                    "w_pop*pop_share + w_need*need_share. Sem efeitos comportamentais."
                ),
            },
            "params": scenario["params"],
            "results": result,
            "baseline_results": baseline,
            "comparison": _build_comparison(result, baseline),
            "status_label": "SIMULADO",
            "disclaimer": scenario["disclaimer"],
        }
        self.runs[run_id] = run
        scenario["status"] = "ran"
        scenario["last_run_id"] = run_id
        return run

    def manifest(self, scenario_id: str) -> dict[str, Any]:
        scenario = deepcopy(self.scenarios[scenario_id])
        run = self.runs.get(scenario.get("last_run_id", ""), {})
        return {
            "schema": "brasilreal.scenario.manifest.v1",
            "generated_at": _utc_now(),
            "product": {
                "name": "Brasil Real",
                "version": "0.1.0",
                "disclaimer": (
                    "Simulador educacional e exploratório. Não é fonte oficial, "
                    "parecer jurídico, previsão garantida ou sistema de decisão pública."
                ),
            },
            "data_versions": {
                "population_dataset_id": self.population["dataset_id"],
                "population_checksum_sha256": self.population["checksum_sha256"],
                "population_reference_date": self.population["reference_date"],
                "population_release_date": self.population["release_date"],
            },
            "scenario": scenario,
            "last_run": {
                "id": run.get("id"),
                "seed": run.get("seed"),
                "model": run.get("model"),
                "status_label": run.get("status_label"),
            }
            if run
            else None,
            "reproducibility": {
                "deterministic": True,
                "notes": (
                    "Mesmo manifesto + seed deve reproduzir resultados idênticos "
                    "para o motor hypothetical_federal_fund_v1."
                ),
            },
        }


def _build_comparison(scenario: dict[str, Any], baseline: dict[str, Any]) -> list[dict[str, Any]]:
    base_by_uf = {r["uf"]: r for r in baseline["allocations"]}
    rows = []
    for row in scenario["allocations"]:
        base = base_by_uf[row["uf"]]
        delta = Decimal(row["amount_brl"]) - Decimal(base["amount_brl"])
        rows.append(
            {
                "uf": row["uf"],
                "ibge_code": row["ibge_code"],
                "name": row["name"],
                "scenario_amount_brl": row["amount_brl"],
                "baseline_amount_brl": base["amount_brl"],
                "delta_brl": f"{delta:.2f}",
                "scenario_per_capita_brl": row["per_capita_brl"],
                "baseline_per_capita_brl": base["per_capita_brl"],
                "status_label": "SIMULADO",
            }
        )
    return rows


store = InMemoryStore()

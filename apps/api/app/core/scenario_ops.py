"""Hypothetical fund scenarios — create, patch, run, manifest."""

from __future__ import annotations

import uuid
from copy import deepcopy
from decimal import Decimal
from typing import Any, Protocol

from app.core.paths import utc_now
from app.services.fund_engine import FundParams, distribute_hypothetical_fund


class _StoreView(Protocol):
    population: dict[str, Any]
    scenarios: dict[str, dict[str, Any]]
    runs: dict[str, dict[str, Any]]


def ensure_default_scenario(store: _StoreView) -> None:
    scenario_id = "scn_baseline_fund_demo"
    if scenario_id in store.scenarios:
        return
    store.scenarios[scenario_id] = {
        "id": scenario_id,
        "title": "Fundo federal fictício — linha de base populacional",
        "author": "system",
        "status": "active",
        "is_hypothetical": True,
        "disclaimer": (
            "Cenário explicitamente hipotético. Não representa lei vigente, "
            "fundo real nem política pública em vigor."
        ),
        "cutoff_date": store.population.get("reference_date", "2025-07-01"),
        "baseline": True,
        "created_at": utc_now(),
        "patches": [],
        "params": {
            "budget_brl": "10000000000.00",
            "population_weight": "1.0",
            "need_weight": "0.0",
        },
    }


def create_scenario(
    store: _StoreView, title: str, author: str, params: dict[str, str]
) -> dict[str, Any]:
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
        "cutoff_date": store.population.get("reference_date", "2025-07-01"),
        "baseline": False,
        "created_at": utc_now(),
        "patches": [],
        "params": {
            "budget_brl": params.get("budget_brl", "10000000000.00"),
            "population_weight": params.get("population_weight", "0.7"),
            "need_weight": params.get("need_weight", "0.3"),
        },
    }
    store.scenarios[scenario_id] = scenario
    return scenario


def apply_patch(store: _StoreView, scenario_id: str, patch: dict[str, Any]) -> dict[str, Any]:
    scenario = store.scenarios[scenario_id]
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
        "at": utc_now(),
        "note": patch.get("note"),
    }
    scenario["patches"].append(entry)
    scenario["status"] = "patched"
    return scenario


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


def run_scenario(store: _StoreView, scenario_id: str, seed: int = 42) -> dict[str, Any]:
    scenario = store.scenarios[scenario_id]
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
    records = store.population["records"]
    result = distribute_hypothetical_fund(records, params, seed=seed)
    baseline = distribute_hypothetical_fund(records, baseline_params, seed=seed)
    run_id = f"run_{uuid.uuid4().hex[:12]}"
    run = {
        "id": run_id,
        "scenario_id": scenario_id,
        "status": "succeeded",
        "seed": seed,
        "created_at": utc_now(),
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
    store.runs[run_id] = run
    scenario["status"] = "ran"
    scenario["last_run_id"] = run_id
    return run


def manifest(store: _StoreView, scenario_id: str) -> dict[str, Any]:
    scenario = deepcopy(store.scenarios[scenario_id])
    run = store.runs.get(scenario.get("last_run_id", ""), {})
    return {
        "schema": "brasilreal.scenario.manifest.v1",
        "generated_at": utc_now(),
        "product": {
            "name": "Brasil Real",
            "version": "0.1.0",
            "disclaimer": (
                "Simulador educacional e exploratório. Não é fonte oficial, "
                "parecer jurídico, previsão garantida ou sistema de decisão pública."
            ),
        },
        "data_versions": {
            "population_dataset_id": store.population["dataset_id"],
            "population_checksum_sha256": store.population["checksum_sha256"],
            "population_reference_date": store.population["reference_date"],
            "population_release_date": store.population["release_date"],
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

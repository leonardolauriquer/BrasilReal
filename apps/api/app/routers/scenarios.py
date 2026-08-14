from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.store import store

router = APIRouter(tags=["scenarios"])


class ScenarioCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    author: str = Field(default="anonymous", max_length=120)
    budget_brl: str = Field(default="10000000000.00")
    population_weight: str = Field(default="0.7")
    need_weight: str = Field(default="0.3")


class ScenarioPatch(BaseModel):
    path: str
    value: str
    note: str | None = None


class ScenarioRunRequest(BaseModel):
    seed: int = 42


@router.get("/scenarios")
def list_scenarios() -> dict:
    items = list(store.scenarios.values())
    return {"count": len(items), "items": items}


@router.post("/scenarios", status_code=201)
def create_scenario(body: ScenarioCreate) -> dict[str, Any]:
    return store.create_scenario(
        title=body.title,
        author=body.author,
        params={
            "budget_brl": body.budget_brl,
            "population_weight": body.population_weight,
            "need_weight": body.need_weight,
        },
    )


@router.get("/scenarios/{scenario_id}")
def get_scenario(scenario_id: str) -> dict[str, Any]:
    if scenario_id not in store.scenarios:
        raise HTTPException(status_code=404, detail="Cenário não encontrado")
    return store.scenarios[scenario_id]


@router.post("/scenarios/{scenario_id}/patches")
def patch_scenario(scenario_id: str, body: ScenarioPatch) -> dict[str, Any]:
    if scenario_id not in store.scenarios:
        raise HTTPException(status_code=404, detail="Cenário não encontrado")
    try:
        return store.apply_patch(scenario_id, body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/scenarios/{scenario_id}/runs", status_code=201)
def run_scenario(scenario_id: str, body: ScenarioRunRequest) -> dict[str, Any]:
    if scenario_id not in store.scenarios:
        raise HTTPException(status_code=404, detail="Cenário não encontrado")
    try:
        return store.run_scenario(scenario_id, seed=body.seed)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/runs/{run_id}")
def get_run(run_id: str) -> dict[str, Any]:
    if run_id not in store.runs:
        raise HTTPException(status_code=404, detail="Execução não encontrada")
    return store.runs[run_id]


@router.get("/runs/{run_id}/results")
def get_run_results(run_id: str) -> dict[str, Any]:
    if run_id not in store.runs:
        raise HTTPException(status_code=404, detail="Execução não encontrada")
    run = store.runs[run_id]
    return {
        "run_id": run_id,
        "status_label": run["status_label"],
        "disclaimer": run["disclaimer"],
        "results": run["results"],
        "baseline_results": run["baseline_results"],
        "comparison": run["comparison"],
    }


@router.get("/scenarios/{scenario_id}/manifest")
def get_manifest(scenario_id: str) -> dict[str, Any]:
    if scenario_id not in store.scenarios:
        raise HTTPException(status_code=404, detail="Cenário não encontrado")
    return store.manifest(scenario_id)

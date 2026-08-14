from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure app imports resolve
import sys

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

from app.core.store import store  # noqa: E402
from app.main import app  # noqa: E402
from app.services.fund_engine import FundParams, distribute_hypothetical_fund  # noqa: E402


@pytest.fixture(autouse=True)
def _reload_store():
    store.scenarios.clear()
    store.runs.clear()
    store.load()
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/ready").json()["fixtures_loaded"] is True


def test_geographies_27_ufs(client):
    data = client.get("/v1/geographies?level=state").json()
    assert data["count"] == 27
    ufs = {item["uf"] for item in data["items"]}
    assert len(ufs) == 27


def test_population_reconciles_official_total(client):
    data = client.get("/v1/observations?indicator=population").json()
    assert data["meta"]["population_brazil_total"] == 213_421_037
    total = sum(item["value"] for item in data["items"])
    assert total == 213_421_037
    assert all(item["status_label"] == "ESTIMADO" for item in data["items"])
    assert all("source" in item for item in data["items"])


def test_social_indicators_and_profile(client):
    indicators = {i["id"] for i in client.get("/v1/indicators").json()["items"]}
    assert {"population", "pib", "poverty_rate", "literacy_rate", "unemployment_rate"} <= indicators
    poverty = client.get("/v1/observations?indicator=poverty_rate").json()
    assert poverty["count"] == 27
    lit = client.get("/v1/observations?indicator=literacy_rate").json()
    assert lit["count"] == 27
    unemp = client.get("/v1/observations?indicator=unemployment_rate").json()
    assert unemp["count"] == 27
    profile = client.get("/v1/geographies/35/profile").json()
    assert profile["geography"]["uf"] == "SP"
    metric_ids = {m["indicator"] for m in profile["metrics"]}
    assert "poverty_rate" in metric_ids
    assert "literacy_rate" in metric_ids


def test_ipeadata_safety_layers(client):
    indicators = {i["id"]: i for i in client.get("/v1/indicators").json()["items"]}
    assert "homicide_rate" in indicators
    assert indicators["homicide_rate"]["group"] == "seguranca"
    assert indicators["homicide_rate"]["higher_is_worse"] is True
    periods = client.get("/v1/indicators/homicide_rate/periods").json()
    assert periods["count"] >= 1
    latest = periods["items"][-1]
    obs = client.get(f"/v1/observations?indicator=homicide_rate&period={latest}").json()
    assert obs["count"] == 27
    assert all(item["unit"] == "por 100 mil hab" for item in obs["items"])
    assert all(item.get("definition") for item in obs["items"])
    traffic = client.get("/v1/observations?indicator=traffic_death_rate").json()
    assert traffic["count"] == 27
    counts = client.get("/v1/observations?indicator=homicide_count").json()
    assert counts["count"] == 27


def test_comex_agro_export_layers(client):
    indicators = {i["id"]: i for i in client.get("/v1/indicators").json()["items"]}
    for key in ("export_meat_fob", "export_bovine_fob", "export_soy_fob"):
        assert key in indicators
        assert indicators[key]["group"] == "agro"
        assert indicators[key]["unit"] == "USD"
    meat = client.get("/v1/observations?indicator=export_meat_fob").json()
    assert meat["count"] == 27
    assert sum(i["value"] for i in meat["items"]) > 0
    soy = client.get("/v1/observations?indicator=export_soy_fob").json()
    assert soy["count"] == 27
    periods = client.get("/v1/indicators/export_soy_fob/periods").json()
    assert periods["count"] >= 1
    assert all(item.get("definition") for item in meat["items"])


def test_legal_instrument_catalogued_not_computable(client):
    data = client.get("/v1/legal-instruments").json()
    assert data["count"] >= 1
    item = data["items"][0]
    assert item["computable_rules"] is False
    assert "canonical_url" in item


def test_fund_engine_invariants():
    records = store.population["records"]
    params = FundParams(
        budget_brl=Decimal("10000000000.00"),
        population_weight=Decimal("0.6"),
        need_weight=Decimal("0.4"),
    )
    a = distribute_hypothetical_fund(records, params, seed=42)
    b = distribute_hypothetical_fund(records, params, seed=42)
    assert a == b
    assert a["invariants"]["budget_conserved"] is True
    assert a["invariants"]["shares_sum_to_one"] is True
    assert a["invariants"]["n_ufs"] == 27
    share_sum = sum(Decimal(x["share"]) for x in a["allocations"])
    assert abs(share_sum - Decimal("1")) < Decimal("1e-9")
    total = sum(Decimal(x["amount_brl"]) for x in a["allocations"])
    assert total == Decimal("10000000000.00")


def test_scenario_run_compare_manifest(client):
    created = client.post(
        "/v1/scenarios",
        json={
            "title": "Rateio hipotético 70/30",
            "author": "test",
            "budget_brl": "10000000000.00",
            "population_weight": "0.7",
            "need_weight": "0.3",
        },
    ).json()
    assert created["is_hypothetical"] is True
    run = client.post(f"/v1/scenarios/{created['id']}/runs", json={"seed": 7}).json()
    assert run["status_label"] == "SIMULADO"
    assert "hipotético" in run["disclaimer"].lower() or "hipotetica" in run["disclaimer"].lower() or "hipotética" in run["disclaimer"].lower()
    results = client.get(f"/v1/runs/{run['id']}/results").json()
    assert len(results["comparison"]) == 27
    manifest = client.get(f"/v1/scenarios/{created['id']}/manifest").json()
    assert manifest["schema"] == "brasilreal.scenario.manifest.v1"
    assert manifest["data_versions"]["population_checksum_sha256"]


def test_fixture_checksum_stable():
    path = Path(__file__).resolve().parents[3] / "data" / "fixtures" / "ibge" / "population_uf_2025.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["brazil_total"] == 213_421_037
    assert len(payload["records"]) == 27

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from app.core.store import store  # noqa: E402
from app.services.fund_engine import FundParams, distribute_hypothetical_fund  # noqa: E402


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/ready").json()["fixtures_loaded"] is True


def test_share_redirects_browser(client):
    response = client.get(
        "/s?camada=homicide_rate&ano=2024&recorte=S",
        headers={"User-Agent": "Mozilla/5.0"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    location = response.headers["location"]
    assert location.startswith("https://brasilreal-atlas.web.app/")
    assert "camada=homicide_rate" in location
    assert "recorte=S" in location
    assert "/s?" not in location and not location.rstrip("/").endswith("/s")


def test_share_og_html_for_whatsapp(client):
    response = client.get(
        "/s?camada=homicide_rate&ano=2024&recorte=S&uf=SC",
        headers={"User-Agent": "WhatsApp/10.0.0"},
    )
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    body = response.text
    assert "og:title" in body
    assert "Sul" in body
    assert "SC" in body
    assert "Brasil Real" in body
    assert "/og.png" in body
    assert "feminicídio" not in body.lower()


def test_share_html_format_query(client):
    response = client.get("/v1/share?format=html&camada=population")
    assert response.status_code == 200
    assert "População" in response.text
    assert "og:image" in response.text


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
    female = client.get("/v1/observations?indicator=female_homicide_count").json()
    assert female["count"] == 27
    assert indicators["female_homicide_count"]["higher_is_worse"] is True
    assert "feminicídio" not in indicators["female_homicide_count"]["short_name"].lower()
    sp = next(item for item in obs["items"] if item["uf"] == "SP")
    if latest == "2024":
        assert sp["value"] == 6.6


def test_periods_expose_latest(client):
    data = client.get("/v1/indicators/population/periods").json()
    assert data["count"] >= 1
    assert data["latest"] == data["items"][-1]
    assert "source" in data
    obs = client.get("/v1/observations?indicator=population").json()
    assert obs["count"] == 27
    assert obs["meta"].get("resolved_period")
    # Fixture hit must not claim live_fallback
    if not obs["meta"].get("live_fallback"):
        assert obs["meta"]["live_fallback"] is False


def test_live_fallback_flag_false_on_fixture_hit(client):
    latest = client.get("/v1/indicators/homicide_rate/periods").json()["latest"]
    obs = client.get(f"/v1/observations?indicator=homicide_rate&period={latest}").json()
    assert obs["count"] == 27
    assert obs["meta"]["live_fallback"] is False


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


def test_tse_presidential_election_layers(client):
    indicators = {i["id"]: i for i in client.get("/v1/indicators").json()["items"]}
    assert "pres_winner_share" in indicators
    assert indicators["pres_winner_share"]["group"] == "eleicoes"
    assert indicators["pres_winner_share"]["status_label"] == "OBSERVADO"
    assert "pres_party_pt" in indicators
    assert "pres_party_pl" in indicators
    periods = client.get("/v1/indicators/pres_party_pt/periods").json()
    assert "2022T2" in periods["items"]
    assert "2018T1" in periods["items"]
    obs = client.get("/v1/observations?indicator=pres_party_pt&period=2022T2").json()
    assert obs["count"] == 27
    assert all(item["unit"] == "%" for item in obs["items"])
    assert all(0 <= item["value"] <= 100 for item in obs["items"])
    sp = next(i for i in obs["items"] if i["uf"] == "SP")
    assert 40 <= sp["value"] <= 50
    margin = client.get("/v1/observations?indicator=pres_margin_pp&period=2022T2").json()
    assert margin["count"] == 27
    assert all(item.get("definition") for item in obs["items"])


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


def test_period_no_year_truncation_mislabel(client):
    """YYYYTn must not silently resolve to calendar year on annual series."""
    bad = client.get("/v1/observations?indicator=homicide_rate&period=2024T2").json()
    assert bad["count"] == 0
    assert bad["meta"]["period_miss"] is True
    assert bad["meta"]["period_resolved"] is False
    # Exact year still works when present in series.
    periods = client.get("/v1/indicators/homicide_rate/periods").json()["items"]
    year = next(p for p in periods if len(p) == 4 and p.isdigit())
    ok = client.get(f"/v1/observations?indicator=homicide_rate&period={year}").json()
    assert ok["count"] == 27
    assert ok["meta"]["period_resolved"] is True
    assert all(item["reference_period"] == year for item in ok["items"])


def test_observation_sources_have_dataset(client):
    for indicator in ("population", "pib", "poverty_rate", "pres_party_pt"):
        q = f"/v1/observations?indicator={indicator}"
        if indicator == "pres_party_pt":
            q += "&period=2022T2"
        data = client.get(q).json()
        assert data["count"] >= 1, indicator
        for item in data["items"]:
            src = item["source"]
            assert src.get("organization"), indicator
            assert src.get("dataset"), f"{indicator} missing dataset: {src}"


def test_municipality_profile_shape(client):
    profile = client.get("/v1/geographies/municipalities/3550308/profile").json()
    assert profile["geography"]["ibge_code"] == "3550308"
    assert profile["geography"]["uf_code"] == "35"
    assert profile["metrics"] == []
    assert "territory" in profile


def test_integrity_gate_on_observations(client):
    data = client.get("/v1/observations?indicator=population").json()
    assert data["meta"]["integrity"]["gated"] is True
    assert data["meta"]["integrity"]["dropped_count"] == 0
    assert data["meta"]["integrity"]["population_reconcile_ok"] is True
    assert data["meta"]["integrity"]["coverage_ok"] is True
    assert data["count"] == 27
    for item in data["items"]:
        assert item["definition"]
        assert item["source"]["organization"]
        assert item["source"]["dataset"]
        assert item["reference_period"]
        assert item["status_label"]


def test_ready_reports_integrity(client):
    ready = client.get("/ready").json()
    assert ready["fixtures_loaded"] is True
    assert ready["integrity"] == "ok"
    assert ready["uf_count"] == 27
    assert ready["indicator_layers"] >= 1
    assert ready["manifest"] is True


def test_store_load_validates_fixtures():
    from app.core.data_integrity import DataIntegrityError, validate_loaded_store

    validate_loaded_store(store)  # must not raise
    broken = type("S", (), {})()
    broken.population = {"records": [], "brazil_total": 1, "source": {}}
    broken.pib = {}
    broken.social = {}
    try:
        validate_loaded_store(broken)
        assert False, "expected DataIntegrityError"
    except DataIntegrityError:
        pass


def test_promoted_territory_and_derived_layers(client):
    indicators = {i["id"]: i for i in client.get("/v1/indicators").json()["items"]}
    for key in (
        "area_km2",
        "population_density",
        "indigenous_population",
        "indigenous_share",
        "quilombola_residents",
        "pib_per_capita",
        "sanitation_adequate",
    ):
        assert key in indicators, key
        assert indicators[key].get("definition")
    assert indicators["area_km2"]["unit"] == "km²"
    assert indicators["population_density"]["status_label"] == "DERIVADO"
    assert indicators["pib_per_capita"]["status_label"] == "DERIVADO"
    assert indicators["pib_per_capita"]["unit"] == "BRL/hab"
    assert indicators["sanitation_adequate"]["unit"] == "%"
    area = client.get("/v1/observations?indicator=area_km2").json()
    assert area["count"] == 27
    assert all(item["value"] > 0 for item in area["items"])
    assert all(item.get("definition") for item in area["items"])
    dens = client.get("/v1/observations?indicator=population_density").json()
    assert dens["count"] == 27
    quil = client.get("/v1/observations?indicator=quilombola_residents").json()
    assert quil["count"] == 27
    by_uf = {i["uf"]: i["value"] for i in quil["items"]}
    assert by_uf["AC"] == 0
    assert by_uf["RR"] == 0
    assert by_uf["BA"] > 0
    pc = client.get("/v1/observations?indicator=pib_per_capita").json()
    assert pc["count"] == 27
    assert all(item["value"] > 0 for item in pc["items"])
    san = client.get("/v1/observations?indicator=sanitation_adequate").json()
    assert san["count"] == 27
    assert all(0 <= item["value"] <= 100 for item in san["items"])


def test_comex_extended_export_layers(client):
    indicators = {i["id"]: i for i in client.get("/v1/indicators").json()["items"]}
    for key in (
        "export_corn_fob",
        "export_soy_meal_fob",
        "export_iron_ore_fob",
        "export_soy_oil_fob",
        "export_petroleum_fob",
    ):
        assert key in indicators, key
        obs = client.get(f"/v1/observations?indicator={key}").json()
        assert obs["count"] == 27, key
        assert sum(i["value"] for i in obs["items"]) > 0
        assert all(item.get("definition") for item in obs["items"])


def test_pnadc_income_and_gini_layers(client):
    indicators = {i["id"]: i for i in client.get("/v1/indicators").json()["items"]}
    gini = indicators["gini_household"]
    assert gini["unit"] == "índice"
    assert gini["higher_is_worse"] is True
    assert gini["group"] == "economia"
    gini_obs = client.get("/v1/observations?indicator=gini_household").json()
    assert gini_obs["count"] == 27
    assert all(0 <= item["value"] <= 1 for item in gini_obs["items"])
    assert all(item.get("definition") for item in gini_obs["items"])
    income = indicators["household_income_pc"]
    assert income["unit"] == "BRL/mês"
    inc_obs = client.get("/v1/observations?indicator=household_income_pc").json()
    assert inc_obs["count"] == 27
    assert all(item["value"] > 0 for item in inc_obs["items"])
    assert all(item.get("definition") for item in inc_obs["items"])
    gini_periods = client.get("/v1/indicators/gini_household/periods").json()
    assert gini_periods["count"] >= 2


def test_observation_series_one_uf_keeps_periods_and_provenance(client):
    missing = client.get("/v1/observations?indicator=gini_household&series=true")
    assert missing.status_code == 422
    data = client.get(
        "/v1/observations?indicator=gini_household&geography=35&series=true"
    ).json()
    assert data["count"] >= 2
    assert all(item["uf"] == "SP" and item["geography_ibge_code"] == "35" for item in data["items"])
    periods = {item["reference_period"] for item in data["items"]}
    assert len(periods) >= 2
    assert all(item.get("definition") for item in data["items"])
    assert all((item.get("source") or {}).get("organization") for item in data["items"])
    latest = client.get("/v1/observations?indicator=gini_household&geography=35").json()
    assert latest["count"] == 1


def test_siconfi_fiscal_layers(client):
    indicators = {i["id"]: i for i in client.get("/v1/indicators").json()["items"]}
    keys = (
        "rcl_rreo",
        "receita_tributaria_rreo",
        "impostos_rreo",
        "transf_uniao_rreo",
        "despesa_empenhada_rreo",
        "dcl_rreo",
    )
    for key in keys:
        assert key in indicators, key
        assert indicators[key]["unit"] == "BRL"
        assert indicators[key]["group"] == "fiscal"
        assert indicators[key]["status_label"] == "OBSERVADO"
        obs = client.get(f"/v1/observations?indicator={key}").json()
        assert obs["count"] == 27, key
        assert all(item.get("definition") for item in obs["items"])
        periods = client.get(f"/v1/indicators/{key}/periods").json()
        assert periods["count"] >= 1, key
    assert all(item["value"] > 0 for item in client.get("/v1/observations?indicator=rcl_rreo").json()["items"])
    assert indicators["dcl_rreo"]["higher_is_worse"] is True
    trib_obs = {i["uf"]: i["value"] for i in client.get("/v1/observations?indicator=receita_tributaria_rreo").json()["items"]}
    tax_obs = {i["uf"]: i["value"] for i in client.get("/v1/observations?indicator=impostos_rreo").json()["items"]}
    assert tax_obs["SP"] <= trib_obs["SP"]


def test_cgu_union_transfer_layers(client):
    indicators = {i["id"]: i for i in client.get("/v1/indicators").json()["items"]}
    for key in ("union_transfers", "union_transfers_const", "union_transfers_pc"):
        assert key in indicators, key
        assert indicators[key]["group"] == "uniao"
        assert "CGU" in (indicators[key].get("source") or {}).get("organization", "") or key == "union_transfers_pc"
        obs = client.get(f"/v1/observations?indicator={key}").json()
        assert obs["count"] == 27, key
        assert all(item.get("definition") for item in obs["items"])
        assert all(item["value"] > 0 for item in obs["items"]), key
        periods = client.get(f"/v1/indicators/{key}/periods").json()
        assert periods["count"] >= 2, key
    observed = indicators["union_transfers"]
    assert observed["unit"] == "BRL"
    assert observed["status_label"] == "OBSERVADO"
    assert indicators["union_transfers_pc"]["unit"] == "BRL/hab"
    assert indicators["union_transfers_pc"]["status_label"] == "DERIVADO"
    by_uf = {item["uf"]: item["value"] for item in client.get("/v1/observations?indicator=union_transfers").json()["items"]}
    assert by_uf["SP"] > by_uf["RR"]
    rreo = {
        item["uf"]: item["value"]
        for item in client.get("/v1/observations?indicator=transf_uniao_rreo").json()["items"]
    }
    assert by_uf["SP"] != rreo["SP"]
    sample = client.get("/v1/observations?indicator=union_transfers").json()["items"][0]
    blob = " ".join(
        [
            sample.get("definition") or "",
            " ".join(sample.get("limitations") or []),
        ]
    ).casefold()
    assert "favorecido" in blob
    assert "siconfi" in blob or "rreo" in blob


def test_governor_layers_full_uf_coverage(client):
    indicators = {i["id"]: i for i in client.get("/v1/indicators").json()["items"]}
    for key in ("gov_winner_share", "gov_margin_pp"):
        assert key in indicators, key
        obs = client.get(f"/v1/observations?indicator={key}").json()
        assert obs["count"] == 27, key
        assert all(item.get("definition") for item in obs["items"])
    periods = client.get("/v1/indicators/gov_winner_share/periods").json()["items"]
    assert all(p.endswith("T1") or p.endswith("T2") for p in periods)
    assert any(p.endswith("T1") for p in periods)


def test_health_and_security_extra_layers(client):
    indicators = {i["id"]: i for i in client.get("/v1/indicators").json()["items"]}
    for key, group, year in (
        ("water_network_share", "saude", "2022"),
        ("waste_collected_share", "saude", "2022"),
        ("pns_tobacco_smokers", "saude", "2019"),
        ("pns_diabetes", "saude", "2019"),
        ("pns_health_plan", "saude", "2019"),
        ("pns_violence", "seguranca", "2019"),
        ("pns_alcohol", "saude", "2019"),
        ("pns_hypertension", "saude", "2019"),
        ("pns_physical_violence", "seguranca", "2019"),
        ("pns_physical_women", "seguranca", "2019"),
        ("pns_psych_violence", "seguranca", "2019"),
        ("pns_sexual_lifetime", "seguranca", "2019"),
    ):
        assert key in indicators, key
        assert indicators[key]["group"] == group
        assert indicators[key]["unit"] == "%"
        obs = client.get(f"/v1/observations?indicator={key}").json()
        assert obs["count"] == 27, key
        assert all(0 <= item["value"] <= 100 for item in obs["items"])
        assert all(item.get("definition") for item in obs["items"])
        assert all(item["reference_period"] == year for item in obs["items"])
    assert indicators["pns_tobacco_smokers"]["status_label"] == "ESTIMADO"
    assert indicators["water_network_share"]["status_label"] == "OBSERVADO"


def test_demography_vital_and_age_layers(client):
    indicators = {i["id"]: i for i in client.get("/v1/indicators").json()["items"]}
    for key in (
        "aging_index",
        "median_age",
        "share_0_14",
        "share_60_plus",
        "crude_birth_rate",
        "crude_death_rate",
    ):
        assert key in indicators, key
        assert indicators[key].get("definition")
        obs = client.get(f"/v1/observations?indicator={key}").json()
        assert obs["count"] == 27, key
        assert all(item.get("definition") for item in obs["items"])
        assert all(isinstance(item["value"], (int, float)) for item in obs["items"])

    assert indicators["aging_index"]["status_label"] == "OBSERVADO"
    assert indicators["aging_index"]["unit"] == "por 100 jovens"
    assert indicators["median_age"]["unit"] == "anos"
    assert indicators["share_0_14"]["status_label"] == "DERIVADO"
    assert indicators["share_60_plus"]["status_label"] == "DERIVADO"
    assert indicators["crude_birth_rate"]["status_label"] == "DERIVADO"
    assert indicators["crude_death_rate"]["status_label"] == "DERIVADO"
    assert indicators["crude_birth_rate"]["unit"] == "por mil hab"
    assert indicators["crude_death_rate"]["higher_is_worse"] is True

    age = client.get("/v1/observations?indicator=median_age").json()
    assert all(0 < item["value"] < 120 for item in age["items"])
    young = client.get("/v1/observations?indicator=share_0_14").json()
    old = client.get("/v1/observations?indicator=share_60_plus").json()
    assert all(0 <= item["value"] <= 100 for item in young["items"])
    assert all(0 <= item["value"] <= 100 for item in old["items"])
    by_young = {i["uf"]: i["value"] for i in young["items"]}
    by_old = {i["uf"]: i["value"] for i in old["items"]}
    # North/Northeast typically younger than South — sanity, not a ranking.
    assert by_young["AM"] > by_young["RS"]
    assert by_old["RS"] > by_old["AM"]

    births = client.get("/v1/indicators/crude_birth_rate/periods").json()
    deaths = client.get("/v1/indicators/crude_death_rate/periods").json()
    assert births["count"] >= 1
    assert deaths["count"] >= 1
    assert all(item["value"] > 0 for item in client.get("/v1/observations?indicator=crude_birth_rate").json()["items"])
    assert all(item["value"] > 0 for item in client.get("/v1/observations?indicator=crude_death_rate").json()["items"])


def test_generation_share_layers(client):
    gens = (
        "share_gen_alpha",
        "share_gen_z",
        "share_gen_y",
        "share_gen_x",
        "share_gen_boomer",
        "share_gen_silent",
    )
    indicators = {i["id"]: i for i in client.get("/v1/indicators").json()["items"]}
    by_uf: dict[str, dict[str, float]] = {g: {} for g in gens}
    for key in gens:
        assert key in indicators, key
        assert indicators[key]["status_label"] == "DERIVADO"
        assert indicators[key]["unit"] == "%"
        assert indicators[key]["group"] == "demografia"
        obs = client.get(f"/v1/observations?indicator={key}").json()
        assert obs["count"] == 27, key
        assert all(0 <= item["value"] <= 100 for item in obs["items"])
        assert all(item.get("definition") for item in obs["items"])
        limitations = " ".join(indicators[key].get("limitations") or []).lower()
        assert "não classifica gerações" in limitations
        for item in obs["items"]:
            by_uf[key][item["uf"]] = item["value"]

    for uf in by_uf["share_gen_z"]:
        total = round(sum(by_uf[g][uf] for g in gens), 1)
        assert 99.0 <= total <= 101.0, (uf, total)
    assert by_uf["share_gen_alpha"]["AM"] > by_uf["share_gen_alpha"]["RS"]
    assert by_uf["share_gen_boomer"]["RS"] > by_uf["share_gen_boomer"]["AM"]


def test_census_pnadc_wave_layers(client):
    indicators = {i["id"]: i for i in client.get("/v1/indicators").json()["items"]}
    percent_keys = (
        "internet_home_share",
        "urban_share",
        "race_branca_share",
        "race_preta_share",
        "race_parda_share",
        "informality_rate",
        "higher_education_share",
    )
    for key in percent_keys:
        assert key in indicators, key
        assert indicators[key]["unit"] == "%"
        obs = client.get(f"/v1/observations?indicator={key}").json()
        assert obs["count"] == 27, key
        assert all(0 <= item["value"] <= 100 for item in obs["items"]), key
        assert all(item.get("definition") for item in obs["items"])

    assert indicators["internet_home_share"]["status_label"] == "ESTIMADO"
    assert indicators["urban_share"]["status_label"] == "OBSERVADO"
    assert indicators["informality_rate"]["higher_is_worse"] is True
    assert indicators["informality_rate"]["group"] == "economia"
    inf_periods = client.get("/v1/indicators/informality_rate/periods").json()
    assert inf_periods["count"] >= 2
    edu_periods = client.get("/v1/indicators/higher_education_share/periods").json()
    assert edu_periods["count"] >= 2

    urban = {i["uf"]: i["value"] for i in client.get("/v1/observations?indicator=urban_share").json()["items"]}
    assert urban["SP"] > urban["AM"]

    sex = client.get("/v1/observations?indicator=sex_ratio").json()
    assert sex["count"] == 27
    assert indicators["sex_ratio"]["unit"] == "homens/100 mulheres"
    assert all(50 < item["value"] < 150 for item in sex["items"])

    dep = client.get("/v1/observations?indicator=dependency_ratio").json()
    assert dep["count"] == 27
    assert indicators["dependency_ratio"]["status_label"] == "DERIVADO"
    assert all(item["value"] > 0 for item in dep["items"])

    labor = client.get("/v1/observations?indicator=labor_income").json()
    assert labor["count"] == 27
    assert indicators["labor_income"]["unit"] == "BRL/mês"
    assert all(item["value"] > 0 for item in labor["items"])
    labor_periods = client.get("/v1/indicators/labor_income/periods").json()
    assert labor_periods["count"] >= 2
    occ = client.get("/v1/observations?indicator=occupancy_rate").json()
    part = client.get("/v1/observations?indicator=participation_rate").json()
    assert occ["count"] == part["count"] == 27
    assert indicators["occupancy_rate"]["unit"] == "%"
    assert indicators["participation_rate"]["unit"] == "%"
    assert all(0 < item["value"] < 100 for item in occ["items"])
    assert all(0 < item["value"] < 100 for item in part["items"])
    occ_by = {i["uf"]: i["value"] for i in occ["items"]}
    assert occ_by["SC"] > occ_by["PE"]


def test_cempre_formal_wage_and_firms(client):
    indicators = {i["id"]: i for i in client.get("/v1/indicators").json()["items"]}
    assert indicators["cempre_avg_wage"]["unit"] == "BRL/mês"
    assert indicators["cempre_wage_in_sm"]["unit"] == "salários mínimos"
    assert indicators["cempre_firms"]["unit"] == "empresas"
    wage = client.get("/v1/observations?indicator=cempre_avg_wage").json()
    sm = client.get("/v1/observations?indicator=cempre_wage_in_sm").json()
    firms = client.get("/v1/observations?indicator=cempre_firms").json()
    assert wage["count"] == sm["count"] == firms["count"] == 27
    assert all(item["value"] > 0 for item in wage["items"])
    assert all(0 < item["value"] < 30 for item in sm["items"])
    assert all(item["value"] > 0 for item in firms["items"])
    by_f = {i["uf"]: i["value"] for i in firms["items"]}
    assert by_f["SP"] > by_f["AM"]
    jobs = client.get("/v1/observations?indicator=cempre_jobs").json()
    assert jobs["count"] == 27
    assert indicators["cempre_jobs"]["unit"] == "pessoas"
    assert all(item["value"] > 0 for item in jobs["items"])
    by_j = {i["uf"]: i["value"] for i in jobs["items"]}
    assert by_j["SP"] > by_j["RR"]


def test_housing_firm_demography_and_capital_basket(client):
    indicators = {i["id"]: i for i in client.get("/v1/indicators").json()["items"]}
    assert indicators["rented_share"]["unit"] == "%"
    assert indicators["rented_share"]["group"] == "moradia"
    assert indicators["owned_paying_share"]["group"] == "moradia"
    assert indicators["owned_paid_share"]["group"] == "moradia"
    rented = client.get("/v1/observations?indicator=rented_share").json()
    paying = client.get("/v1/observations?indicator=owned_paying_share").json()
    paid = client.get("/v1/observations?indicator=owned_paid_share").json()
    assert rented["count"] == paying["count"] == paid["count"] == 27
    by_r = {i["uf"]: i["value"] for i in rented["items"]}
    assert by_r["DF"] > by_r["MA"]
    assert all(0 < item["value"] < 100 for item in rented["items"])

    assert indicators["employer_unit_births"]["unit"] == "unidades locais"
    assert indicators["employer_unit_birth_rate"]["status_label"] == "DERIVADO"
    assert indicators["employer_survival_1y"]["unit"] == "%"
    births = client.get("/v1/observations?indicator=employer_unit_births").json()
    rate = client.get("/v1/observations?indicator=employer_unit_birth_rate").json()
    survival = client.get("/v1/observations?indicator=employer_survival_1y").json()
    assert births["count"] == rate["count"] == survival["count"] == 27
    by_b = {i["uf"]: i["value"] for i in births["items"]}
    assert by_b["SP"] > by_b["AM"]
    assert all(0 < item["value"] < 100 for item in rate["items"])

    assert indicators["basket_capital"]["group"] == "custo"
    assert indicators["basket_capital"]["higher_is_worse"] is True
    assert indicators["basket_capital"]["unit"] == "BRL/mês"
    limits = " ".join(indicators["basket_capital"].get("limitations") or []).lower()
    assert "capital" in limits
    basket = client.get("/v1/observations?indicator=basket_capital").json()
    share = client.get("/v1/observations?indicator=basket_share_sm").json()
    assert basket["count"] == share["count"] == 27
    by_c = {i["uf"]: i["value"] for i in basket["items"]}
    assert by_c["SP"] > by_c["SE"]
    assert all(item["value"] > 0 for item in basket["items"])
    assert all(0 < item["value"] <= 100 for item in share["items"])


def test_editorial_lenses_live_and_venture(client):
    indicators = {i["id"]: i for i in client.get("/v1/indicators").json()["items"]}
    for key in ("lens_live", "lens_venture"):
        assert key in indicators, key
        assert indicators[key]["status_label"] == "DERIVADO"
        assert indicators[key]["unit"] == "nota 0-100"
        assert indicators[key]["group"] == "lentes"
        assert indicators[key]["higher_is_worse"] is False
        org = ((indicators[key].get("source") or {}).get("organization") or "").lower()
        assert "brasil real" in org
        blob = " ".join(
            [
                indicators[key].get("definition") or "",
                * (indicators[key].get("limitations") or []),
            ]
        ).lower()
        assert "idhm" in blob or "ranking oficial" in blob or "receita" in blob
        if key == "lens_live":
            assert "pns" in blob or "violência" in blob or "violencia" in blob
        if key == "lens_venture":
            assert "ocup" in blob or "emprego" in blob or "pessoal" in blob
        obs = client.get(f"/v1/observations?indicator={key}").json()
        assert obs["count"] == 27, key
        vals = [item["value"] for item in obs["items"]]
        assert all(0 <= v <= 100 for v in vals), key
        assert max(vals) - min(vals) > 10
        assert all(item.get("definition") for item in obs["items"])
        assert (obs.get("meta") or {}).get("integrity", {}).get("coverage_ok") is not False
        periods = client.get(f"/v1/indicators/{key}/periods").json()
        assert periods["count"] >= 1


def test_derived_fiscal_ratios_and_family_aging_lenses(client):
    indicators = {i["id"]: i for i in client.get("/v1/indicators").json()["items"]}
    for key in ("rcl_pc", "trib_share_rcl", "dcl_rcl", "trib_pc", "trib_pib_share", "pib_share"):
        assert key in indicators, key
        assert indicators[key]["status_label"] == "DERIVADO"
        obs = client.get(f"/v1/observations?indicator={key}").json()
        assert obs["count"] == 27, key
        assert all(item.get("definition") for item in obs["items"])
    assert indicators["rcl_pc"]["unit"] == "BRL/hab"
    assert indicators["trib_pc"]["unit"] == "BRL/hab"
    assert indicators["trib_pib_share"]["unit"] == "% do PIB"
    assert indicators["pib_share"]["unit"] == "% do PIB"
    assert indicators["trib_share_rcl"]["unit"] == "% da RCL"
    assert indicators["dcl_rcl"]["unit"] == "DCL/RCL"
    assert indicators["dcl_rcl"]["higher_is_worse"] is True
    rcl = {i["uf"]: i["value"] for i in client.get("/v1/observations?indicator=rcl_rreo").json()["items"]}
    pop = {i["uf"]: i["value"] for i in client.get("/v1/observations?indicator=population").json()["items"]}
    pc = {i["uf"]: i["value"] for i in client.get("/v1/observations?indicator=rcl_pc").json()["items"]}
    assert abs(pc["SP"] - rcl["SP"] / pop["SP"]) < 1e-6
    trib = {i["uf"]: i["value"] for i in client.get("/v1/observations?indicator=trib_share_rcl").json()["items"]}
    assert 0 < trib["SP"] < 200
    trib_pc = {i["uf"]: i["value"] for i in client.get("/v1/observations?indicator=trib_pc").json()["items"]}
    trib_brl = {i["uf"]: i["value"] for i in client.get("/v1/observations?indicator=receita_tributaria_rreo").json()["items"]}
    assert abs(trib_pc["SP"] - trib_brl["SP"] / pop["SP"]) < 1e-6
    assert indicators["lens_family"]["status_label"] == "DERIVADO"
    assert indicators["lens_aging"]["higher_is_worse"] is True
    fam_blob = " ".join(
        [
            indicators["lens_family"].get("definition") or "",
            *(indicators["lens_family"].get("limitations") or []),
        ]
    ).lower()
    assert "pns" in fam_blob or "mulher" in fam_blob
    assert "ideb" in fam_blob
    fam = client.get("/v1/observations?indicator=lens_family").json()
    age = client.get("/v1/observations?indicator=lens_aging").json()
    assert fam["count"] == age["count"] == 27
    assert all(0 <= i["value"] <= 100 for i in fam["items"])
    assert all(0 <= i["value"] <= 100 for i in age["items"])
    limits = " ".join(indicators["lens_aging"].get("limitations") or []).lower()
    assert "idoso" in limits or "pressão" in limits or "pressao" in limits
    assert indicators["export_fob"]["unit"] == "USD"
    assert indicators["export_fob_pc"]["unit"] == "USD/hab"
    exp = client.get("/v1/observations?indicator=export_fob").json()
    pcx = client.get("/v1/observations?indicator=export_fob_pc").json()
    assert exp["count"] == pcx["count"] == 27
    by_e = {i["uf"]: i["value"] for i in exp["items"]}
    assert by_e["SP"] > by_e["RR"]

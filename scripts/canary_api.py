#!/usr/bin/env python3
"""Post-deploy canary — abort release if integrity gates fail in production."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any, Callable

CANARY_LAYERS = (
    ("population", None),
    ("pib", None),
    ("poverty_rate", None),
    ("pres_party_pt", "2022T2"),
    ("pib_per_capita", None),
    ("sanitation_adequate", None),
    ("area_km2", None),
    ("water_network_share", None),
    ("pns_violence", "2019"),
    ("gini_household", None),
    ("household_income_pc", None),
    ("pns_alcohol", "2019"),
    ("export_petroleum_fob", None),
    ("rcl_rreo", None),
    ("receita_tributaria_rreo", None),
    ("transf_uniao_rreo", None),
    ("despesa_empenhada_rreo", None),
    ("dcl_rreo", None),
    ("gov_winner_share", None),
    ("aging_index", "2022"),
    ("crude_birth_rate", None),
    ("share_gen_z", "2022"),
    ("internet_home_share", "2022"),
    ("informality_rate", None),
    ("urban_share", "2022"),
    ("cempre_avg_wage", None),
    ("rented_share", "2022"),
    ("employer_unit_birth_rate", None),
    ("basket_capital", None),
    ("lens_live", None),
    ("lens_venture", None),
    ("lens_family", None),
    ("lens_aging", None),
    ("rcl_pc", None),
    ("trib_share_rcl", None),
    ("dcl_rcl", None),
    ("export_fob", None),
    ("union_transfers", None),
    ("union_transfers_const", None),
    ("union_transfers_pc", None),
)


def get_json_http(base: str, path: str, timeout: int = 30) -> dict[str, Any]:
    url = base.rstrip("/") + path
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "BrasilReal-canary/1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def run_canary(get_json: Callable[[str], dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    ready = get_json("/ready")
    if ready.get("integrity") != "ok":
        errors.append(f"/ready integrity={ready.get('integrity')!r}")
    if ready.get("uf_count") != 27:
        errors.append(f"/ready uf_count={ready.get('uf_count')!r}")
    if not ready.get("fixtures_loaded"):
        errors.append("/ready fixtures not loaded")

    health = get_json("/health")
    if health.get("status") != "ok":
        errors.append(f"/health status={health.get('status')!r}")

    for indicator, period in CANARY_LAYERS:
        q = f"/v1/observations?indicator={indicator}"
        if period:
            q += f"&period={period}"
        data = get_json(q)
        integ = (data.get("meta") or {}).get("integrity") or {}
        if data.get("count") != 27:
            errors.append(f"{indicator}: count={data.get('count')} (want 27)")
        if integ.get("gated") is not True:
            errors.append(f"{indicator}: integrity.gated is not true")
        if integ.get("dropped_count"):
            errors.append(f"{indicator}: dropped_count={integ.get('dropped_count')}")
        if integ.get("coverage_ok") is False:
            errors.append(f"{indicator}: coverage_ok=false")
        if indicator == "population" and integ.get("population_reconcile_ok") is not True:
            errors.append("population_reconcile_ok is not true")
        if indicator == "pib" and integ.get("pib_reconcile_ok") is not True:
            errors.append("pib_reconcile_ok is not true")
        items = data.get("items") or []
        for item in items[:3]:
            if not item.get("definition"):
                errors.append(f"{indicator}: missing definition")
                break
            src = item.get("source") or {}
            if not src.get("organization") or not src.get("dataset"):
                errors.append(f"{indicator}: incomplete source")
                break
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Brasil Real integrity canary")
    parser.add_argument(
        "--url",
        default="https://brasil-real-api-928790342045.southamerica-east1.run.app",
        help="API base URL",
    )
    args = parser.parse_args(argv)
    try:
        errors = run_canary(lambda path: get_json_http(args.url, path))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"FAIL — canary could not reach API: {exc}")
        return 1
    if errors:
        print(f"FAIL — {len(errors)} canary check(s):")
        for err in errors:
            print(f"  - {err}")
        return 1
    print(f"OK — canary against {args.url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

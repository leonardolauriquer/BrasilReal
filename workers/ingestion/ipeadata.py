"""Ipeadata connector — UF series for violence / traffic (Atlas da Violência / DATASUS)."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from common import fetch_bytes, fixtures_dir, snapshot_raw, utc_now, write_json
from ipeadata_catalog import IPEADATA_SPECS

ODATA_BASE = "http://www.ipeadata.gov.br/api/odata4"
# API ignores $filter; full series must be downloaded then sliced locally.
UF_NIV = "Estados"


def _estados_meta() -> tuple[dict[str, str], dict[str, str]]:
    path = fixtures_dir() / "ibge" / "estados_refresh.json"
    sigla: dict[str, str] = {}
    nome: dict[str, str] = {}
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data.get("items", []):
            code = str(item["id"])
            sigla[code] = item["sigla"]
            nome[code] = item["nome"]
    return sigla, nome


def _is_uf_row(row: dict[str, Any]) -> bool:
    niv = (row.get("NIVNOME") or "").strip()
    if niv != UF_NIV:
        return False
    code = str(row.get("TERCODIGO") or "").strip()
    return code.isdigit() and len(code) in {1, 2} and code != "0"


def _normalize_uf_code(code: str) -> str:
    return str(int(code)).zfill(2) if code.isdigit() else code


def fetch_serie_raw(sercodigo: str) -> tuple[bytes, list[dict[str, Any]]]:
    url = f"{ODATA_BASE}/ValoresSerie(SERCODIGO='{sercodigo}')"
    raw = fetch_bytes(url, timeout=180)
    snapshot_raw(
        "ipeadata",
        f"{sercodigo}.json",
        raw,
        {"source_url": url, "connector": "ipeadata.valores_serie", "sercodigo": sercodigo},
    )
    payload = json.loads(raw.decode("utf-8"))
    rows = payload.get("value") or []
    if not isinstance(rows, list):
        raise RuntimeError(f"ipeadata {sercodigo}: unexpected payload shape")
    return raw, rows


def _build_series(
    rows: list[dict[str, Any]],
    *,
    sigla_by_code: dict[str, str],
    nome_by_code: dict[str, str],
    required_codes: set[str] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    want = required_codes or set(sigla_by_code)
    by_period: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        if not _is_uf_row(row):
            continue
        valor = row.get("VALVALOR")
        if valor is None:
            continue
        period = str(row.get("VALDATA") or "")[:4]
        if not period.isdigit():
            continue
        code = _normalize_uf_code(str(row["TERCODIGO"]))
        if want and code not in want:
            continue
        by_period.setdefault(period, {})[code] = {
            "ibge_code": code,
            "uf": sigla_by_code.get(code, ""),
            "name": nome_by_code.get(code, code),
            "value": float(valor),
        }

    out: dict[str, list[dict[str, Any]]] = {}
    for period, by_code in by_period.items():
        if want and set(by_code) != want:
            continue
        records = [by_code[c] for c in sorted(by_code)]
        out[period] = records
    return dict(sorted(out.items()))


def fetch_catalog_indicator(indicator_id: str) -> dict[str, Any]:
    if indicator_id not in IPEADATA_SPECS:
        raise KeyError(f"unknown ipeadata indicator: {indicator_id}")
    spec = IPEADATA_SPECS[indicator_id]
    sercodigo = spec["sercodigo"]
    url = f"{ODATA_BASE}/ValoresSerie(SERCODIGO='{sercodigo}')"
    _, rows = fetch_serie_raw(sercodigo)
    sigla_by_code, nome_by_code = _estados_meta()
    if len(sigla_by_code) != 27:
        raise RuntimeError("ipeadata: need data/fixtures/ibge/estados_refresh.json (27 UFs)")
    series = _build_series(
        rows,
        sigla_by_code=sigla_by_code,
        nome_by_code=nome_by_code,
        required_codes=set(sigla_by_code),
    )
    if not series:
        raise RuntimeError(f"{indicator_id}: no complete UF periods extracted from {sercodigo}")

    periods = list(series.keys())
    latest = periods[-1]
    records = series[latest]
    if len(records) != 27:
        raise RuntimeError(f"{indicator_id} {latest}: expected 27 UFs, got {len(records)}")

    canonical = json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    checksum = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    fixture = {
        "indicator_id": indicator_id,
        "dataset_id": f"ipeadata.{sercodigo}.{latest}",
        "title": f"{spec['name']} — UFs {latest}",
        "short_name": spec["short_name"],
        "status_label": spec["status_label"],
        "evidence_grade": spec["evidence_grade"],
        "unit": spec["unit"],
        "higher_is_worse": spec["higher_is_worse"],
        "kind": spec["kind"],
        "group": spec["group"],
        "group_label": spec["group_label"],
        "frequency": spec["frequency"],
        "reference_period": latest,
        "reference_date": f"{latest}-01-01",
        "release_date": None,
        "retrieved_at": utc_now(),
        "available_periods": periods,
        "definition": spec["definition"],
        "source": {
            "organization": spec["organization"],
            "dataset": f"Ipeadata {sercodigo}",
            "dataset_page": spec["dataset_page"],
            "serie_page": spec.get("serie_page"),
            "api_url": url,
            "sercodigo": sercodigo,
            "method_notes": spec["method_notes"],
        },
        "limitations": spec["limitations"],
        "checksum_sha256": checksum,
        "records": records,
        "series": series,
    }

    out_dir = fixtures_dir() / "ipeadata" / "indicators"
    out_dir.mkdir(parents=True, exist_ok=True)
    period_path = out_dir / f"{indicator_id}_{latest}.json"
    latest_path = out_dir / f"{indicator_id}_latest.json"
    write_json(period_path, fixture)
    write_json(latest_path, fixture)
    return {
        "indicator_id": indicator_id,
        "period": latest,
        "periods": len(periods),
        "ufs": len(records),
        "fixture": str(latest_path),
        "checksum": checksum,
    }


def fetch_bundle() -> dict[str, Any]:
    results = {}
    for indicator_id in IPEADATA_SPECS:
        results[indicator_id] = fetch_catalog_indicator(indicator_id)
    return {"retrieved_at": utc_now(), "indicators": results}

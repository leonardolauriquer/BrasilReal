"""MDIC ComexStat connector — annual UF export FOB series."""

from __future__ import annotations

import hashlib
import json
import time
import unicodedata
import urllib.error
import urllib.request
from typing import Any

from comex_catalog import COMEX_SPECS
from common import USER_AGENT, fixtures_dir, snapshot_raw, utc_now, write_json

API = "https://api-comexstat.mdic.gov.br/general?language=pt"
YEAR_FROM = 2018


def _fold(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in nfkd if not unicodedata.combining(c)).casefold().strip()


def _estados() -> list[dict[str, str]]:
    path = fixtures_dir() / "ibge" / "estados_refresh.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("items") or []
    if len(items) != 27:
        raise RuntimeError(f"comex: expected 27 UFs in estados_refresh, got {len(items)}")
    return [{"ibge_code": str(i["id"]), "uf": i["sigla"], "name": i["nome"]} for i in items]


def _name_index(estados: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    idx: dict[str, dict[str, str]] = {}
    for row in estados:
        idx[_fold(row["name"])] = row
        idx[_fold(row["uf"])] = row
    # Comex occasionally uses short forms
    aliases = {
        "sao paulo": "São Paulo",
        "rio de janeiro": "Rio de Janeiro",
        "rio grande do sul": "Rio Grande do Sul",
        "rio grande do norte": "Rio Grande do Norte",
        "mato grosso do sul": "Mato Grosso do Sul",
        "mato grosso": "Mato Grosso",
        "distrito federal": "Distrito Federal",
        "espirito santo": "Espírito Santo",
        "ceara": "Ceará",
        "paraiba": "Paraíba",
        "goias": "Goiás",
        "para": "Pará",
        "parana": "Paraná",
        "piaui": "Piauí",
        "rondonia": "Rondônia",
        "amapa": "Amapá",
    }
    by_name = {_fold(r["name"]): r for r in estados}
    for alias, canonical in aliases.items():
        if _fold(canonical) in by_name:
            idx[alias] = by_name[_fold(canonical)]
    return idx


def _post(body: dict[str, Any], *, retries: int = 6) -> dict[str, Any]:
    raw_last = b""
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                API,
                data=json.dumps(body).encode("utf-8"),
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw_last = resp.read()
            payload = json.loads(raw_last.decode("utf-8"))
            if not payload.get("success", True):
                raise RuntimeError(f"comexstat error: {payload.get('message') or payload}")
            return payload
        except urllib.error.HTTPError as exc:
            last_err = exc
            if exc.code in {429, 500, 502, 503, 504} and attempt < retries - 1:
                time.sleep(2.5 * (attempt + 1))
                continue
            raise
        except urllib.error.URLError as exc:
            last_err = exc
            if attempt < retries - 1:
                time.sleep(2.5 * (attempt + 1))
                continue
            raise
    raise RuntimeError(f"comexstat failed: {last_err}; raw={raw_last[:200]!r}")


def _query_year(year: int, filters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    body = {
        "flow": "export",
        "monthDetail": False,
        "period": {"from": f"{year}-01", "to": f"{year}-12"},
        "filters": filters,
        "details": ["state"],
        "metrics": ["metricFOB", "metricKG"],
    }
    payload = _post(body)
    snapshot_raw(
        "comex",
        f"general_{year}_{hashlib.sha1(json.dumps(filters, sort_keys=True).encode()).hexdigest()[:8]}.json",
        json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        {"source_url": API, "connector": "comex.general", "year": year, "filters": filters},
    )
    return list((payload.get("data") or {}).get("list") or [])


def _rows_to_values(
    rows: list[dict[str, Any]],
    *,
    name_idx: dict[str, dict[str, str]],
    metric: str,
) -> tuple[dict[str, float], float]:
    out: dict[str, float] = {}
    unknown: list[str] = []
    skipped_non_uf = 0.0
    for row in rows:
        state = str(row.get("state") or "")
        folded = _fold(state)
        if folded in {"", "nao declarada", "nd", "n/d", "nao informado"}:
            raw = row.get(metric)
            if raw not in (None, "", "-"):
                skipped_non_uf += float(str(raw).replace(",", "."))
            continue
        meta = name_idx.get(folded)
        if not meta:
            unknown.append(state)
            continue
        raw = row.get(metric)
        if raw in (None, "", "-"):
            continue
        value = float(str(raw).replace(",", "."))
        code = meta["ibge_code"]
        out[code] = out.get(code, 0.0) + value
    if unknown:
        raise RuntimeError(f"comex: unmapped UF names: {sorted(set(unknown))}")
    return out, skipped_non_uf


def _fetch_year_values(
    year: int,
    spec: dict[str, Any],
    name_idx: dict[str, dict[str, str]],
) -> tuple[dict[str, float], float]:
    metric = spec["metric"]
    skipped = 0.0
    if "filters_multi" in spec:
        acc: dict[str, float] = {}
        for filters in spec["filters_multi"]:
            time.sleep(2.2)
            part, skip = _rows_to_values(_query_year(year, filters), name_idx=name_idx, metric=metric)
            skipped += skip
            for code, val in part.items():
                acc[code] = acc.get(code, 0.0) + val
        return acc, skipped
    time.sleep(2.2)
    return _rows_to_values(_query_year(year, spec["filters"]), name_idx=name_idx, metric=metric)


def _complete_records(
    values: dict[str, float],
    estados: list[dict[str, str]],
) -> list[dict[str, Any]]:
    records = []
    for row in estados:
        code = row["ibge_code"]
        records.append(
            {
                "ibge_code": code,
                "uf": row["uf"],
                "name": row["name"],
                "value": float(values.get(code, 0.0)),
            }
        )
    records.sort(key=lambda r: r["ibge_code"])
    return records


def fetch_catalog_indicator(indicator_id: str, *, year_from: int = YEAR_FROM, year_to: int | None = None) -> dict[str, Any]:
    if indicator_id not in COMEX_SPECS:
        raise KeyError(indicator_id)
    spec = COMEX_SPECS[indicator_id]
    estados = _estados()
    name_idx = _name_index(estados)
    end = year_to or int(time.strftime("%Y")) - 1  # last complete calendar year
    candidates = list(range(year_from, end + 1))
    series: dict[str, list[dict[str, Any]]] = {}
    skipped_notes: list[str] = []
    for year in candidates:
        if year > end:
            # Ano civil em curso = parcial; não entra na série anual do mapa.
            continue
        try:
            values, skipped = _fetch_year_values(year, spec, name_idx)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"{indicator_id} {year}: {exc}") from exc
        records = _complete_records(values, estados)
        series[str(year)] = records
        if skipped > 0:
            skipped_notes.append(f"{year}: US$ {skipped:,.0f} em 'Não Declarada' excluídos do mapa UF")

    if not series:
        raise RuntimeError(f"{indicator_id}: no periods retrieved")

    periods = sorted(series)
    latest = periods[-1]
    records = series[latest]
    if len(records) != 27:
        raise RuntimeError(f"{indicator_id}: expected 27 UFs, got {len(records)}")

    canonical = json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    checksum = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    brazil_total = sum(r["value"] for r in records)
    limitations = list(spec["limitations"])
    limitations.append(
        "UF sem registro no Comex Stat no ano recebe valor 0 (sem operação declarada naquele recorte)."
    )
    limitations.append(
        "Série usa apenas anos-civis completos (jan–dez); ano corrente parcial não é publicado como camada."
    )
    if skipped_notes:
        limitations.extend(skipped_notes[-3:])

    fixture = {
        "indicator_id": indicator_id,
        "dataset_id": f"comex.{indicator_id}.{latest}",
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
        "reference_date": f"{latest}-12-31",
        "release_date": None,
        "retrieved_at": utc_now(),
        "available_periods": periods,
        "brazil_total": brazil_total,
        "definition": spec["definition"],
        "source": {
            "organization": spec["organization"],
            "dataset": f"Comex Stat / {indicator_id}",
            "dataset_page": spec["dataset_page"],
            "url": spec["api_docs"],
            "api_url": API,
            "method_notes": spec["method_notes"],
        },
        "limitations": limitations,
        "checksum_sha256": checksum,
        "records": records,
        "series": series,
    }

    out_dir = fixtures_dir() / "comex" / "indicators"
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / f"{indicator_id}_{latest}.json", fixture)
    write_json(out_dir / f"{indicator_id}_latest.json", fixture)
    return {
        "indicator_id": indicator_id,
        "period": latest,
        "periods": len(periods),
        "ufs": len(records),
        "brazil_total": brazil_total,
        "checksum": checksum,
    }


def fetch_bundle(year_from: int = YEAR_FROM) -> dict[str, Any]:
    results = {}
    for indicator_id in COMEX_SPECS:
        results[indicator_id] = fetch_catalog_indicator(indicator_id, year_from=year_from)
        time.sleep(3.0)
    return {"retrieved_at": utc_now(), "indicators": results}

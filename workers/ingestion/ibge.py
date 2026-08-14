"""IBGE connectors: localidades, malhas, estimativas via Agregados API."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from common import fetch_bytes, fetch_json, fixtures_dir, snapshot_raw, utc_now, write_json

ESTADOS_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/estados?orderBy=nome"
MALHAS_UF_URL = (
    "https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR"
    "?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=UF"
)
FTP_INDEX = "https://ftp.ibge.gov.br/Estimativas_de_Populacao/"
# Tabela 6579 = estimativas populacionais; variável 9324 = população residente
AGREGADO_POP = 6579
VAR_POP = 9324


def refresh_estados() -> dict[str, Any]:
    raw = fetch_bytes(ESTADOS_URL)
    snapshot_raw(
        "ibge",
        "estados.json",
        raw,
        {"source_url": ESTADOS_URL, "connector": "ibge.localidades.estados"},
    )
    data = json.loads(raw.decode("utf-8"))
    if len(data) != 27:
        raise RuntimeError(f"expected 27 UFs, got {len(data)}")
    payload = {
        "retrieved_at": utc_now(),
        "source_url": ESTADOS_URL,
        "checksum_sha256": hashlib.sha256(raw).hexdigest(),
        "count": len(data),
        "status_label": "OBSERVADO",
        "items": data,
    }
    out = fixtures_dir() / "ibge" / "estados_refresh.json"
    write_json(out, payload)
    return {"wrote": str(out), "count": payload["count"], "checksum": payload["checksum_sha256"]}


def refresh_malha_uf() -> dict[str, Any]:
    raw = fetch_bytes(MALHAS_UF_URL, timeout=120)
    snapshot_raw(
        "ibge",
        "uf_malha_minima.geojson",
        raw,
        {"source_url": MALHAS_UF_URL, "connector": "ibge.malhas.uf"},
    )
    geo = json.loads(raw.decode("utf-8"))
    if len(geo.get("features", [])) != 27:
        raise RuntimeError(f"expected 27 features, got {len(geo.get('features', []))}")

    # Enrich with UF metadata when available
    estados_path = fixtures_dir() / "ibge" / "estados_refresh.json"
    by_code: dict[str, dict[str, Any]] = {}
    if estados_path.exists():
        estados = json.loads(estados_path.read_text(encoding="utf-8"))
        by_code = {str(item["id"]): item for item in estados.get("items", [])}

    for feature in geo["features"]:
        code = str(feature["properties"].get("codarea"))
        estado = by_code.get(code, {})
        feature["properties"] = {
            "codarea": code,
            "ibge_code": code,
            "uf": estado.get("sigla"),
            "name": estado.get("nome"),
        }

    text = json.dumps(geo, ensure_ascii=False)
    fixtures_out = fixtures_dir() / "ibge" / "uf_malha_enriched.geojson"
    fixtures_out.write_text(text, encoding="utf-8")
    web_out = Path(__file__).resolve().parents[2] / "apps" / "web" / "public" / "geo" / "uf_br.geojson"
    web_out.parent.mkdir(parents=True, exist_ok=True)
    web_out.write_text(text, encoding="utf-8")
    return {
        "features": 27,
        "fixture": str(fixtures_out),
        "web": str(web_out),
        "checksum": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def detect_estimate_years() -> dict[str, Any]:
    html = fetch_bytes(FTP_INDEX, timeout=30).decode("utf-8", errors="replace")
    years = sorted({part for part in html.split('"') if part.startswith("Estimativas_")})
    return {
        "retrieved_at": utc_now(),
        "source_url": FTP_INDEX,
        "estimate_folders": years,
        "latest": years[-1] if years else None,
    }


def fetch_population_uf(year: int | str = "last") -> dict[str, Any]:
    """Pull UF population from IBGE Agregados API (structured; preferred over PDF typing)."""
    period = str(year)
    if period == "last":
        periods = fetch_json(f"https://servicodados.ibge.gov.br/api/v3/agregados/{AGREGADO_POP}/periodos")
        # API returns list of period ids as strings
        if isinstance(periods, list) and periods:
            # periods may be objects or strings depending on endpoint shape
            ids = []
            for item in periods:
                if isinstance(item, dict) and "id" in item:
                    ids.append(str(item["id"]))
                else:
                    ids.append(str(item))
            period = sorted(ids)[-1]
        else:
            raise RuntimeError("could not resolve latest population period from IBGE")

    url = (
        f"https://servicodados.ibge.gov.br/api/v3/agregados/{AGREGADO_POP}"
        f"/periodos/{period}/variaveis/{VAR_POP}?localidades=N3[all]"
    )
    raw = fetch_bytes(url)
    snapshot_raw(
        "ibge",
        f"populacao_uf_{period}.json",
        raw,
        {
            "source_url": url,
            "connector": "ibge.agregados.populacao_uf",
            "aggregate": AGREGADO_POP,
            "variable": VAR_POP,
            "period": period,
        },
    )
    payload = json.loads(raw.decode("utf-8"))
    series = payload[0]["resultados"][0]["series"]
    if len(series) != 27:
        raise RuntimeError(f"expected 27 UF series, got {len(series)}")

    # Optional UF metadata for names/siglas
    estados_path = fixtures_dir() / "ibge" / "estados_refresh.json"
    sigla_by_code: dict[str, str] = {}
    nome_by_code: dict[str, str] = {}
    if estados_path.exists():
        estados = json.loads(estados_path.read_text(encoding="utf-8"))
        for item in estados.get("items", []):
            sigla_by_code[str(item["id"])] = item["sigla"]
            nome_by_code[str(item["id"])] = item["nome"]

    # Preserve exploratory need index from previous fixture when present
    previous_path = fixtures_dir() / "ibge" / "population_uf_2025.json"
    need_by_code: dict[str, float] = {}
    if previous_path.exists():
        prev = json.loads(previous_path.read_text(encoding="utf-8"))
        for row in prev.get("records", []):
            need_by_code[str(row["ibge_code"])] = float(row["exploratory_need_index"])

    records = []
    for item in series:
        code = str(item["localidade"]["id"])
        value = int(str(item["serie"][period]).replace(".", "").replace(",", ""))
        records.append(
            {
                "ibge_code": code,
                "uf": sigla_by_code.get(code) or item["localidade"].get("nome", "")[:2].upper(),
                "name": nome_by_code.get(code) or item["localidade"]["nome"],
                "population": value,
                "exploratory_need_index": need_by_code.get(code, 0.5),
            }
        )
    records.sort(key=lambda r: r["ibge_code"])
    total = sum(r["population"] for r in records)
    canonical = json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    checksum = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    fixture = {
        "dataset_id": f"ibge.estimativas_populacao.uf.{period}",
        "title": f"Estimativas da população residente — Unidades da Federação {period}",
        "status_label": "ESTIMADO",
        "evidence_grade": "A",
        "unit": "habitantes",
        "reference_date": f"{period}-07-01",
        "release_date": None,
        "retrieved_at": utc_now(),
        "frequency": "annual",
        "source": {
            "organization": "IBGE",
            "dataset_page": "https://www.ibge.gov.br/estatisticas/sociais/populacao/9103-estimativas-de-populacao.html",
            "api_url": url,
            "aggregate_id": AGREGADO_POP,
            "variable_id": VAR_POP,
            "license_or_terms": "Dados públicos oficiais do IBGE; verificar termos de uso no portal.",
            "method_notes": (
                "Ingestão automática via API de Agregados do IBGE (N3=UF). "
                "Não usar scraping quando este canal estruturado estiver disponível."
            ),
        },
        "brazil_total": total,
        "checksum_sha256": checksum,
        "records": records,
        "limitations": [
            "Estimativa oficial anual (referência típica 1º de julho), não censo e não tempo real.",
            "Há defasagem entre referência, publicação no DOU e disponibilidade na API.",
            (
                "exploratory_need_index NÃO é oficial; índice sintético exploratório (grau D) "
                "mantido só para o cenário hipotético."
            ),
        ],
        "ingestion": {
            "connector": "ibge.agregados.populacao_uf",
            "connector_version": "0.2.0",
            "mode": "api",
        },
    }

    # Keep stable filename for current MVP runtime while also writing year-specific copy
    out_year = fixtures_dir() / "ibge" / f"population_uf_{period}.json"
    out_runtime = fixtures_dir() / "ibge" / "population_uf_2025.json"
    write_json(out_year, fixture)
    if str(period) == "2025":
        write_json(out_runtime, fixture)
    else:
        # Newer year becomes runtime source of truth for API fixtures path used today
        write_json(out_runtime, fixture)

    return {
        "period": period,
        "brazil_total": total,
        "n_ufs": len(records),
        "checksum": checksum,
        "wrote": [str(out_year), str(out_runtime)],
        "api_url": url,
    }


def fetch_pib_uf(year: int | str = "last") -> dict[str, Any]:
    """Pull UF GDP (PIB a preços correntes) from IBGE Agregados 5938 / var 37."""
    aggregate_id = 5938
    variable_id = 37
    period = str(year)
    if period == "last":
        periods = fetch_json(f"https://servicodados.ibge.gov.br/api/v3/agregados/{aggregate_id}/periodos")
        ids = [str(item["id"] if isinstance(item, dict) else item) for item in periods]
        period = sorted(ids)[-1]

    url = (
        f"https://servicodados.ibge.gov.br/api/v3/agregados/{aggregate_id}"
        f"/periodos/{period}/variaveis/{variable_id}?localidades=N3[all]"
    )
    raw = fetch_bytes(url)
    snapshot_raw(
        "ibge",
        f"pib_uf_{period}.json",
        raw,
        {
            "source_url": url,
            "connector": "ibge.agregados.pib_uf",
            "aggregate": aggregate_id,
            "variable": variable_id,
            "period": period,
        },
    )
    payload = json.loads(raw.decode("utf-8"))
    series = payload[0]["resultados"][0]["series"]
    if len(series) != 27:
        raise RuntimeError(f"expected 27 UF PIB series, got {len(series)}")

    estados_path = fixtures_dir() / "ibge" / "estados_refresh.json"
    meta_by_code: dict[str, dict[str, str]] = {}
    if estados_path.exists():
        estados = json.loads(estados_path.read_text(encoding="utf-8"))
        for item in estados.get("items", []):
            meta_by_code[str(item["id"])] = {"uf": item["sigla"], "name": item["nome"]}

    records = []
    for item in series:
        code = str(item["localidade"]["id"])
        value_mil = int(str(item["serie"][period]).replace(".", "").replace(",", ""))
        meta = meta_by_code.get(code, {})
        records.append(
            {
                "ibge_code": code,
                "uf": meta.get("uf") or item["localidade"]["nome"][:2].upper(),
                "name": meta.get("name") or item["localidade"]["nome"],
                "pib_mil_reais": value_mil,
                "pib_brl": value_mil * 1000,
            }
        )
    records.sort(key=lambda r: r["ibge_code"])
    total_mil = sum(r["pib_mil_reais"] for r in records)
    canonical = json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    checksum = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    fixture = {
        "dataset_id": f"ibge.contas_regionais.pib_uf.{period}",
        "title": f"PIB a preços correntes — Unidades da Federação {period}",
        "status_label": "ESTIMADO",
        "evidence_grade": "A",
        "unit": "BRL",
        "unit_source": "Mil Reais (convertido para BRL × 1.000)",
        "reference_date": f"{period}-01-01",
        "reference_period": period,
        "release_date": None,
        "retrieved_at": utc_now(),
        "frequency": "annual",
        "source": {
            "organization": "IBGE",
            "dataset_page": (
                "https://www.ibge.gov.br/estatisticas/economicas/contas-nacionais/"
                "9088-produto-interno-bruto-dos-municipios.html"
            ),
            "api_url": url,
            "aggregate_id": aggregate_id,
            "variable_id": variable_id,
            "variable_name": payload[0].get("variavel"),
            "method_notes": (
                "API Agregados IBGE 5938/variável 37 (N3=UF). "
                "Valores oficiais em Mil Reais; runtime expõe BRL."
            ),
        },
        "brazil_total_mil_reais": total_mil,
        "brazil_total_brl": total_mil * 1000,
        "checksum_sha256": checksum,
        "records": records,
        "limitations": [
            "Contas Regionais têm defasagem relevante.",
            "PIB estadual ≠ arrecadação federal territorializada nem renda disponível.",
            "Preços correntes: não comparar anos sem deflacionar.",
        ],
        "ingestion": {
            "connector": "ibge.agregados.pib_uf",
            "connector_version": "0.1.0",
            "mode": "api",
        },
    }
    out = fixtures_dir() / "ibge" / f"pib_uf_{period}.json"
    runtime = fixtures_dir() / "ibge" / "pib_uf_latest.json"
    write_json(out, fixture)
    write_json(runtime, fixture)
    return {
        "period": period,
        "brazil_total_brl": fixture["brazil_total_brl"],
        "n_ufs": len(records),
        "checksum": checksum,
        "wrote": [str(out), str(runtime)],
        "api_url": url,
    }


def _parse_number(raw: str) -> float:
    text = str(raw).strip().replace(",", ".")
    if text in {"", "...", "-", "X", "x"}:
        raise ValueError(f"missing value: {raw!r}")
    return float(text)


def fetch_catalog_indicator(indicator_id: str, year: str = "last") -> dict[str, Any]:
    from indicator_catalog import INDICATOR_SPECS

    if indicator_id not in INDICATOR_SPECS:
        raise KeyError(f"unknown indicator: {indicator_id}")
    spec = INDICATOR_SPECS[indicator_id]
    aggregate_id = spec["aggregate_id"]
    variable_id = spec["variable_id"]
    period = str(year)
    if period == "last":
        periods = fetch_json(f"https://servicodados.ibge.gov.br/api/v3/agregados/{aggregate_id}/periodos")
        ids = [str(item["id"] if isinstance(item, dict) else item) for item in periods]
        period = sorted(ids)[-1]

    url = (
        f"https://servicodados.ibge.gov.br/api/v3/agregados/{aggregate_id}"
        f"/periodos/{period}/variaveis/{variable_id}?localidades=N3[all]"
    )
    if spec.get("classificacao"):
        url += f"&classificacao={spec['classificacao']}"

    raw = fetch_bytes(url)
    snapshot_raw(
        "ibge",
        f"{indicator_id}_{period}.json",
        raw,
        {
            "source_url": url,
            "connector": f"ibge.agregados.{indicator_id}",
            "aggregate": aggregate_id,
            "variable": variable_id,
            "period": period,
        },
    )
    payload = json.loads(raw.decode("utf-8"))
    series = payload[0]["resultados"][0]["series"]
    if len(series) != 27:
        raise RuntimeError(f"{indicator_id}: expected 27 UFs, got {len(series)}")

    estados_path = fixtures_dir() / "ibge" / "estados_refresh.json"
    meta_by_code: dict[str, dict[str, str]] = {}
    if estados_path.exists():
        estados = json.loads(estados_path.read_text(encoding="utf-8"))
        for item in estados.get("items", []):
            meta_by_code[str(item["id"])] = {"uf": item["sigla"], "name": item["nome"]}

    records = []
    for item in series:
        code = str(item["localidade"]["id"])
        value = _parse_number(item["serie"][period])
        meta = meta_by_code.get(code, {})
        records.append(
            {
                "ibge_code": code,
                "uf": meta.get("uf") or item["localidade"]["nome"][:2].upper(),
                "name": meta.get("name") or item["localidade"]["nome"],
                "value": value,
            }
        )
    records.sort(key=lambda r: r["ibge_code"])
    canonical = json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    checksum = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    fixture = {
        "indicator_id": indicator_id,
        "dataset_id": f"ibge.{indicator_id}.{period}",
        "title": f"{spec['name']} — UFs {period}",
        "short_name": spec["short_name"],
        "status_label": spec["status_label"],
        "evidence_grade": spec["evidence_grade"],
        "unit": spec["unit"],
        "higher_is_worse": spec["higher_is_worse"],
        "kind": spec["kind"],
        "group": spec.get("group", "social"),
        "group_label": spec.get("group_label", "Social"),
        "frequency": spec["frequency"],
        "reference_period": period,
        "reference_date": period if len(period) == 4 else f"{period[:4]}-Q{period[4:].lstrip('0') or period[4:]}",
        "release_date": None,
        "retrieved_at": utc_now(),
        "source": {
            "organization": "IBGE",
            "dataset_page": spec["dataset_page"],
            "api_url": url,
            "aggregate_id": aggregate_id,
            "variable_id": variable_id,
            "variable_name": payload[0].get("variavel"),
            "method_notes": spec["method_notes"],
        },
        "checksum_sha256": checksum,
        "records": records,
        "limitations": spec["limitations"],
        "ingestion": {
            "connector": f"ibge.agregados.{indicator_id}",
            "connector_version": "0.1.0",
            "mode": "api",
        },
    }
    out_dir = fixtures_dir() / "ibge" / "indicators"
    out = out_dir / f"{indicator_id}_{period}.json"
    runtime = out_dir / f"{indicator_id}_latest.json"
    write_json(out, fixture)
    write_json(runtime, fixture)
    return {
        "indicator_id": indicator_id,
        "period": period,
        "n_ufs": len(records),
        "checksum": checksum,
        "wrote": [str(out), str(runtime)],
        "api_url": url,
    }


def fetch_social_bundle(year: str = "last") -> dict[str, Any]:
    from indicator_catalog import INDICATOR_SPECS

    results = {}
    for indicator_id in INDICATOR_SPECS:
        # literacy is census-tied; always prefer last available for that table
        results[indicator_id] = fetch_catalog_indicator(indicator_id, year="last")
    return results

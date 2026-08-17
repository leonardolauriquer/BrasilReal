"""Materialize extra UF choropleth layers from official IBGE tables already on disk or SIDRA.

Fail-closed: 27 finite UFs, definition + source + period, never invent missing cells
except IBGE '-' (zero absoluto) where the table publishes that symbol.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from common import fetch_bytes, fixtures_dir, snapshot_raw, utc_now, write_json

UF_CODES = {
    "11": "RO",
    "12": "AC",
    "13": "AM",
    "14": "RR",
    "15": "PA",
    "16": "AP",
    "17": "TO",
    "21": "MA",
    "22": "PI",
    "23": "CE",
    "24": "RN",
    "25": "PB",
    "26": "PE",
    "27": "AL",
    "28": "SE",
    "29": "BA",
    "31": "MG",
    "32": "ES",
    "33": "RJ",
    "35": "SP",
    "41": "PR",
    "42": "SC",
    "43": "RS",
    "50": "MS",
    "51": "MT",
    "52": "GO",
    "53": "DF",
}


def _estados() -> dict[str, dict[str, str]]:
    path = fixtures_dir() / "ibge" / "estados_refresh.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, dict[str, str]] = {}
    for item in data.get("items") or []:
        code = str(item["id"]).zfill(2)
        out[code] = {"ibge_code": code, "uf": item["sigla"], "name": item["nome"]}
    if set(out) != set(UF_CODES):
        raise RuntimeError("social_layers: estados_refresh must cover 27 UFs")
    return out


def _checksum(records: list[dict[str, Any]]) -> str:
    canonical = json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _write_ibge_indicator(fixture: dict[str, Any]) -> dict[str, Any]:
    ind = fixture["indicator_id"]
    period = fixture["reference_period"]
    out_dir = fixtures_dir() / "ibge" / "indicators"
    period_path = out_dir / f"{ind}_{period}.json"
    latest_path = out_dir / f"{ind}_latest.json"
    write_json(period_path, fixture)
    write_json(latest_path, fixture)
    return {
        "indicator_id": ind,
        "period": period,
        "n_ufs": len(fixture["records"]),
        "checksum": fixture["checksum_sha256"],
        "wrote": [str(period_path), str(latest_path)],
    }


def _sidra_float(raw: str, *, dash_as_zero: bool = False) -> float | None:
    text = str(raw).strip().replace(" ", "")
    if text in {"", "...", "X", "x", "None"}:
        return None
    if text == "-":
        return 0.0 if dash_as_zero else None
    if text.count(",") == 1 and text.count(".") >= 1:
        text = text.replace(".", "").replace(",", ".")
    elif text.count(",") == 1:
        text = text.replace(",", ".")
    elif text.count(".") > 1:
        text = text.replace(".", "")
    try:
        return float(text)
    except ValueError:
        return None


def _sidra_uf_map(rows: list[dict[str, Any]], *, dash_as_zero: bool = False) -> dict[str, float]:
    data = rows[1:]
    out: dict[str, float] = {}
    for row in data:
        code = str(row.get("D1C") or "")
        if code not in UF_CODES:
            continue
        val = _sidra_float(str(row.get("V") or ""), dash_as_zero=dash_as_zero)
        if val is None:
            continue
        out[code] = val
    return out


def _records_from_values(
    values: dict[str, float],
    estados: dict[str, dict[str, str]],
    *,
    dash_fill: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    filled = dict(values)
    if dash_fill:
        for code, val in dash_fill.items():
            filled.setdefault(code, val)
    if set(filled) != set(UF_CODES):
        missing = sorted(set(UF_CODES) - set(filled))
        extra = sorted(set(filled) - set(UF_CODES))
        raise RuntimeError(f"UF set mismatch missing={missing} extra={extra}")
    records = []
    for code in sorted(UF_CODES):
        meta = estados[code]
        records.append(
            {
                "ibge_code": code,
                "uf": meta["uf"],
                "name": meta["name"],
                "value": filled[code],
            }
        )
    return records


def _base_fixture(
    *,
    indicator_id: str,
    spec: dict[str, Any],
    period: str,
    records: list[dict[str, Any]],
    api_url: str | None = None,
    series: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    src = dict(spec["source"])
    if api_url:
        src["api_url"] = api_url
    payload: dict[str, Any] = {
        "indicator_id": indicator_id,
        "dataset_id": spec["dataset_id"].format(period=period),
        "title": f"{spec['name']} — UFs {period}",
        "short_name": spec["short_name"],
        "name": spec["name"],
        "status_label": spec["status_label"],
        "evidence_grade": spec.get("evidence_grade", "A"),
        "unit": spec["unit"],
        "higher_is_worse": spec["higher_is_worse"],
        "kind": spec["kind"],
        "group": spec["group"],
        "group_label": spec["group_label"],
        "frequency": spec["frequency"],
        "reference_period": period,
        "reference_date": period if len(period) == 4 else period,
        "release_date": None,
        "retrieved_at": utc_now(),
        "definition": spec["definition"],
        "source": src,
        "limitations": list(spec["limitations"]),
        "checksum_sha256": _checksum(records),
        "records": records,
    }
    if series:
        payload["series"] = series
        payload["available_periods"] = sorted(series)
    return payload


TERRITORY_LAYER_SPECS: dict[str, dict[str, Any]] = {
    "area_km2": {
        "name": "Área territorial",
        "short_name": "Área",
        "unit": "km²",
        "status_label": "OBSERVADO",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "territorio",
        "group_label": "Território",
        "frequency": "irregular",
        "dataset_id": "ibge.area_km2.{period}",
        "value_key": "area_km2",
        "territory_file": "area_2010.json",
        "dash_as_zero": False,
        "definition": (
            "Área total da unidade territorial publicada no agregado IBGE 1301 "
            "(referência 2010)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "Agregados 1301 / variável 615",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/1301",
            "url": "https://sidra.ibge.gov.br/tabela/1301",
        },
        "limitations": [
            "Período do agregado é 2010; limites territoriais posteriores podem diferir.",
        ],
    },
    "indigenous_population": {
        "name": "Pessoas indígenas",
        "short_name": "Indígenas",
        "unit": "pessoas",
        "status_label": "OBSERVADO",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "povos",
        "group_label": "Povos",
        "frequency": "census",
        "dataset_id": "ibge.indigenous_population.{period}",
        "value_key": "indigenous_population",
        "territory_file": "indigenous_2022.json",
        "dash_as_zero": False,
        "definition": (
            "Número de pessoas que se declararam indígenas no Censo Demográfico 2022 "
            "(quesito de declaração indígena, total)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "Agregados 9718 / variável 350",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/9718",
            "url": "https://sidra.ibge.gov.br/tabela/9718",
        },
        "limitations": [
            "Não lista etnias nem povos específicos.",
            "Baseado em autodeclaração no Censo; não é cadastro FUNAI.",
        ],
    },
    "indigenous_share": {
        "name": "Participação indígena na população",
        "short_name": "% indígenas",
        "unit": "%",
        "status_label": "OBSERVADO",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "povos",
        "group_label": "Povos",
        "frequency": "census",
        "dataset_id": "ibge.indigenous_share.{period}",
        "value_key": "indigenous_share",
        "territory_file": "indigenous_2022.json",
        "dash_as_zero": False,
        "definition": (
            "Percentual de pessoas indígenas no total da população residente "
            "(Censo Demográfico 2022)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "Agregados 9718 / variável 4727",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/9718",
            "url": "https://sidra.ibge.gov.br/tabela/9718",
        },
        "limitations": [
            "Comparar apenas com o mesmo recorte censitário.",
        ],
    },
    "quilombola_residents": {
        "name": "Moradores quilombolas",
        "short_name": "Quilombolas",
        "unit": "pessoas",
        "status_label": "OBSERVADO",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "povos",
        "group_label": "Povos",
        "frequency": "census",
        "dataset_id": "ibge.quilombola_residents.{period}",
        "value_key": "quilombola_residents",
        "territory_file": "quilombola_2022.json",
        "dash_as_zero": True,
        "definition": (
            "Moradores quilombolas em domicílios particulares permanentes ocupados "
            "(Censo Demográfico 2022)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "Agregados 9727 / variável 7097",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/9727",
            "url": "https://sidra.ibge.gov.br/tabela/9727",
        },
        "limitations": [
            "Autodeclaração no Censo; não substitui cadastros de territórios quilombolas.",
            (
                "IBGE publica '-' (zero absoluto / não se aplica) para AC e RR neste recorte; "
                "interpretado como 0 moradores quilombolas, não como célula omitida."
            ),
        ],
    },
}


def export_territory_layers() -> dict[str, Any]:
    estados = _estados()
    pop = json.loads((fixtures_dir() / "ibge" / "population_uf_2025.json").read_text(encoding="utf-8"))
    pop_by = {str(r["ibge_code"]): r for r in pop["records"]}
    pop_period = str(pop.get("reference_date") or "2025")[:4]
    results: dict[str, Any] = {}

    for indicator_id, spec in TERRITORY_LAYER_SPECS.items():
        payload = json.loads(
            (fixtures_dir() / "territory" / spec["territory_file"]).read_text(encoding="utf-8")
        )
        period = str(payload.get("reference_period") or "")
        by_uf = payload.get("by_uf") or {}
        values: dict[str, float] = {}
        for code, row in by_uf.items():
            raw = row.get(spec["value_key"])
            if raw is None:
                continue
            values[str(code).zfill(2)] = float(raw)
        dash_fill = None
        if spec.get("dash_as_zero"):
            # Only fill IBGE '-' cells already confirmed for this table (AC/RR on 9727).
            dash_fill = {c: 0.0 for c in ("12", "14") if c not in values}
        records = _records_from_values(values, estados, dash_fill=dash_fill)
        fixture = _base_fixture(
            indicator_id=indicator_id, spec=spec, period=period, records=records
        )
        results[indicator_id] = _write_ibge_indicator(fixture)

    # Density: pop estimate ÷ area 2010 (DERIVADO, mixed years labeled).
    area_fix = json.loads((fixtures_dir() / "ibge" / "indicators" / "area_km2_latest.json").read_text(encoding="utf-8"))
    area_by = {r["ibge_code"]: float(r["value"]) for r in area_fix["records"]}
    dens_records = []
    for code in sorted(UF_CODES):
        pop_n = float(pop_by[code]["population"])
        area = area_by[code]
        if area <= 0:
            raise RuntimeError(f"area_km2 <= 0 for {code}")
        meta = estados[code]
        dens_records.append(
            {
                "ibge_code": code,
                "uf": meta["uf"],
                "name": meta["name"],
                "value": round(pop_n / area, 4),
            }
        )
    dens_spec = {
        "name": "Densidade demográfica (derivada)",
        "short_name": "Densidade",
        "unit": "hab/km²",
        "status_label": "DERIVADO",
        "higher_is_worse": False,
        "kind": "derived",
        "group": "territorio",
        "group_label": "Território",
        "frequency": "annual",
        "dataset_id": "ibge.population_density.{period}",
        "definition": (
            f"População residente estimada IBGE 6579 ({pop_period}) dividida pela área "
            "territorial do agregado 1301 (2010)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": f"6579 (população {pop_period}) ÷ 1301/615 (área 2010)",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/1301",
            "url": "https://sidra.ibge.gov.br/tabela/1301",
        },
        "limitations": [
            f"Números de anos diferentes: população {pop_period} ÷ área 2010.",
            "Não usar como densidade oficial do Censo do mesmo ano.",
        ],
    }
    dens_fixture = _base_fixture(
        indicator_id="population_density",
        spec=dens_spec,
        period=pop_period,
        records=dens_records,
    )
    results["population_density"] = _write_ibge_indicator(dens_fixture)
    return results


def _fetch_sidra(url: str, name: str) -> list[dict[str, Any]]:
    raw = fetch_bytes(url, timeout=180)
    snapshot_raw("ibge", name, raw, {"source_url": url, "connector": "ibge.sidra"})
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, list) or len(payload) < 2:
        raise RuntimeError(f"SIDRA empty/unexpected: {url}")
    return payload


def fetch_sanitation_adequate() -> dict[str, Any]:
    """Censo 2022 SIDRA 6805: share of households with adequate sewage (IBGE category 46290 / total 46292)."""
    period = "2022"
    adeq_url = (
        "https://apisidra.ibge.gov.br/values/t/6805/n3/all/v/381/p/2022/c11558/46290?formato=json"
    )
    tot_url = (
        "https://apisidra.ibge.gov.br/values/t/6805/n3/all/v/381/p/2022/c11558/46292?formato=json"
    )
    adeq = _sidra_uf_map(_fetch_sidra(adeq_url, "sidra_6805_46290.json"))
    tot = _sidra_uf_map(_fetch_sidra(tot_url, "sidra_6805_46292.json"))
    if set(adeq) != set(UF_CODES) or set(tot) != set(UF_CODES):
        raise RuntimeError("sanitation: SIDRA 6805 did not return 27 UFs for num and den")
    estados = _estados()
    records = []
    for code in sorted(UF_CODES):
        den = tot[code]
        if den <= 0:
            raise RuntimeError(f"sanitation: zero households for {code}")
        share = round(100.0 * adeq[code] / den, 1)
        if not 0 <= share <= 100:
            raise RuntimeError(f"sanitation: share out of range for {code}: {share}")
        meta = estados[code]
        records.append(
            {
                "ibge_code": code,
                "uf": meta["uf"],
                "name": meta["name"],
                "value": share,
            }
        )
    spec = {
        "name": "Domicílios com esgotamento adequado",
        "short_name": "Esgoto adequado",
        "unit": "%",
        "status_label": "DERIVADO",
        "higher_is_worse": False,
        "kind": "derived",
        "group": "social",
        "group_label": "Social",
        "frequency": "census",
        "dataset_id": "ibge.sanitation_adequate.{period}",
        "definition": (
            "Percentual de domicílios particulares permanentes ocupados com esgotamento "
            "sanitário na categoria IBGE «Rede geral, rede pluvial ou fossa ligada à rede» "
            "(SIDRA 6805, Censo 2022): contagem da categoria 46290 dividida pelo total 46292."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 6805 / var 381 / c11558 46290÷46292",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/6805",
            "url": "https://sidra.ibge.gov.br/tabela/6805",
            "api_url": adeq_url,
        },
        "limitations": [
            "Razão de duas contagens oficiais da mesma tabela (rótulo DERIVADO); não é variável percentual pronta do SIDRA.",
            "«Adequado» segue o recorte IBGE da categoria 46290 — não inclui fossa não ligada à rede, vala, rio ou ausência de banheiro.",
            "Domicílios ocupados do Censo 2022; não é cobertura de rede por pessoa nem qualidade do tratamento.",
        ],
    }
    fixture = _base_fixture(
        indicator_id="sanitation_adequate",
        spec=spec,
        period=period,
        records=records,
        api_url=adeq_url,
    )
    return _write_ibge_indicator(fixture)


# Official SIDRA percent variables (not silent ratios). Fail if any of 27 UFs is missing.
SIDRA_PERCENT_SPECS: dict[str, dict[str, Any]] = {
    "water_network_share": {
        "name": "Domicílios cuja forma principal de água é a rede geral",
        "short_name": "Água da rede",
        "unit": "%",
        "status_label": "OBSERVADO",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "saude",
        "group_label": "Saúde",
        "frequency": "census",
        "dataset_id": "ibge.water_network_share.{period}",
        "table": "6803",
        "variable": "1000381",
        "period": "2022",
        "class_path": "c1821/72144",
        "definition": (
            "Percentual de domicílios particulares permanentes ocupados que possuem ligação "
            "à rede geral de distribuição de água e a utilizam como forma principal "
            "(SIDRA 6803 / variável percentual 1000381, categoria 72144, Censo 2022)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 6803 / var 1000381 / c1821 72144",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/6803",
            "url": "https://sidra.ibge.gov.br/tabela/6803",
        },
        "limitations": [
            "Forma principal de abastecimento — não mede qualidade, continuidade nem água encanada no interior do imóvel.",
            "Não inclui quem tem ligação à rede mas usa principalmente poço, carro-pipa ou outro manancial.",
        ],
    },
    "waste_collected_share": {
        "name": "Domicílios com lixo coletado",
        "short_name": "Lixo coletado",
        "unit": "%",
        "status_label": "OBSERVADO",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "saude",
        "group_label": "Saúde",
        "frequency": "census",
        "dataset_id": "ibge.waste_collected_share.{period}",
        "table": "6892",
        "variable": "1000381",
        "period": "2022",
        "class_path": "c67/2520",
        "definition": (
            "Percentual de domicílios particulares permanentes ocupados cujo destino do lixo "
            "é a categoria IBGE «Coletado» (SIDRA 6892 / variável percentual 1000381, "
            "categoria 2520, Censo 2022)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 6892 / var 1000381 / c67 2520",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/6892",
            "url": "https://sidra.ibge.gov.br/tabela/6892",
        },
        "limitations": [
            "«Coletado» agrupa coleta no domicílio e depósito em caçamba de serviço de limpeza.",
            "Não mede frequência da coleta, reciclagem nem destinação final (aterro, lixão).",
        ],
    },
    "internet_home_share": {
        "name": "Domicílios com conexão à internet (Censo 2022, amostra)",
        "short_name": "Internet no domicílio",
        "unit": "%",
        "status_label": "ESTIMADO",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "social",
        "group_label": "Social / saneamento",
        "frequency": "census",
        "dataset_id": "ibge.internet_home_share.{period}",
        "table": "9936",
        "variable": "1000381",
        "period": "2022",
        "class_path": "c2072/77585/c63/95826/c125/2932",
        "definition": (
            "Percentual de domicílios particulares permanentes ocupados com conexão "
            "domiciliar à internet (Censo 2022, resultados preliminares da amostra, "
            "SIDRA 9936 / variável 1000381, categoria Sim, totais de ocupação e tipo)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "Censo 2022 amostra SIDRA 9936 / var 1000381 / Sim",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/9936",
            "url": "https://sidra.ibge.gov.br/tabela/9936",
        },
        "limitations": [
            "Amostra (ESTIMADO), não universo do Censo; retrato 2022.",
            "Existência de conexão no domicílio — não mede qualidade, velocidade nem uso individual.",
        ],
    },
    "urban_share": {
        "name": "População em situação urbana (Censo 2022)",
        "short_name": "População urbana",
        "unit": "%",
        "status_label": "OBSERVADO",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "territorio",
        "group_label": "Território",
        "frequency": "census",
        "dataset_id": "ibge.urban_share.{period}",
        "table": "9923",
        "variable": "1000093",
        "period": "2022",
        "class_path": "c1/1",
        "definition": (
            "Percentual da população residente em situação urbana (Censo 2022, SIDRA 9923 / "
            "variável 1000093, categoria Urbana)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "Censo 2022 SIDRA 9923 / var 1000093 / Urbana",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/9923",
            "url": "https://sidra.ibge.gov.br/tabela/9923",
        },
        "limitations": [
            "Situação do domicílio do Censo — não é densidade nem «grau de urbanização» composto.",
        ],
    },
    "race_branca_share": {
        "name": "População branca (autodeclaração, Censo 2022)",
        "short_name": "Branca",
        "unit": "%",
        "status_label": "OBSERVADO",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "povos",
        "group_label": "Povos",
        "frequency": "census",
        "dataset_id": "ibge.race_branca_share.{period}",
        "table": "9605",
        "variable": "1000093",
        "period": "2022",
        "class_path": "c86/2776",
        "definition": (
            "Percentual da população residente que se declarou branca (Censo 2022, SIDRA 9605 / "
            "variável 1000093, categoria 2776)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "Censo 2022 SIDRA 9605 / var 1000093 / branca",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/9605",
            "url": "https://sidra.ibge.gov.br/tabela/9605",
        },
        "limitations": [
            "Autodeclaração no quesito cor ou raça; não é genética nem «diversidade» composta.",
        ],
    },
    "race_preta_share": {
        "name": "População preta (autodeclaração, Censo 2022)",
        "short_name": "Preta",
        "unit": "%",
        "status_label": "OBSERVADO",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "povos",
        "group_label": "Povos",
        "frequency": "census",
        "dataset_id": "ibge.race_preta_share.{period}",
        "table": "9605",
        "variable": "1000093",
        "period": "2022",
        "class_path": "c86/2777",
        "definition": (
            "Percentual da população residente que se declarou preta (Censo 2022, SIDRA 9605 / "
            "variável 1000093, categoria 2777)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "Censo 2022 SIDRA 9605 / var 1000093 / preta",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/9605",
            "url": "https://sidra.ibge.gov.br/tabela/9605",
        },
        "limitations": [
            "Autodeclaração; distinta da categoria parda. Não somar com parda para «população negra» sem rotular o recorte.",
        ],
    },
    "race_parda_share": {
        "name": "População parda (autodeclaração, Censo 2022)",
        "short_name": "Parda",
        "unit": "%",
        "status_label": "OBSERVADO",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "povos",
        "group_label": "Povos",
        "frequency": "census",
        "dataset_id": "ibge.race_parda_share.{period}",
        "table": "9605",
        "variable": "1000093",
        "period": "2022",
        "class_path": "c86/2779",
        "definition": (
            "Percentual da população residente que se declarou parda (Censo 2022, SIDRA 9605 / "
            "variável 1000093, categoria 2779)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "Censo 2022 SIDRA 9605 / var 1000093 / parda",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/9605",
            "url": "https://sidra.ibge.gov.br/tabela/9605",
        },
        "limitations": [
            "Autodeclaração; distinta da categoria preta.",
        ],
    },
    "informality_rate": {
        "name": "Taxa de informalidade (ocupados 14 anos ou mais)",
        "short_name": "Informalidade",
        "unit": "%",
        "status_label": "ESTIMADO",
        "higher_is_worse": True,
        "kind": "observed_estimate",
        "group": "economia",
        "group_label": "Economia / demografia",
        "frequency": "annual",
        "dataset_id": "ibge.informality_rate.{period}",
        "table": "4708",
        "variable": "12466",
        "period": "all",
        "class_path": "",
        "definition": (
            "Taxa de informalidade das pessoas de 14 anos ou mais ocupadas na semana de "
            "referência (PNAD Contínua anual, SIDRA 4708 / variável 12466)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "PNADC anual SIDRA 4708 / var 12466",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/4708",
            "url": "https://sidra.ibge.gov.br/tabela/4708",
        },
        "limitations": [
            "Estimativa amostral; definição IBGE de informalidade (não é só «sem carteira»).",
            "Não confundir com desocupação (tabela 4099).",
        ],
    },
    "occupancy_rate": {
        "name": "Nível da ocupação (14 anos ou mais)",
        "short_name": "Nível de ocupação",
        "unit": "%",
        "status_label": "ESTIMADO",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "economia",
        "group_label": "Economia / demografia",
        "frequency": "quarterly",
        "dataset_id": "ibge.occupancy_rate.{period}",
        "table": "4093",
        "variable": "4097",
        "period": "all",
        "class_path": "c2/6794",
        "definition": (
            "Nível da ocupação na semana de referência das pessoas de 14 anos ou mais "
            "(PNAD Contínua trimestral, SIDRA 4093 / variável 4097, sexo total): ocupados "
            "divididos pela população de 14 anos ou mais."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "PNADC SIDRA 4093 / var 4097 / sexo total",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/4093",
            "url": "https://sidra.ibge.gov.br/tabela/4093",
        },
        "limitations": [
            "Não é o complemento da desocupação: o denominador é a população 14+, não a força de trabalho.",
            "Estimativa amostral trimestral; sazonalidade.",
        ],
    },
    "participation_rate": {
        "name": "Taxa de participação na força de trabalho (14 anos ou mais)",
        "short_name": "Participação (força de trabalho)",
        "unit": "%",
        "status_label": "ESTIMADO",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "economia",
        "group_label": "Economia / demografia",
        "frequency": "quarterly",
        "dataset_id": "ibge.participation_rate.{period}",
        "table": "4093",
        "variable": "4096",
        "period": "all",
        "class_path": "c2/6794",
        "definition": (
            "Taxa de participação na força de trabalho na semana de referência das pessoas "
            "de 14 anos ou mais (PNAD Contínua trimestral, SIDRA 4093 / variável 4096, sexo total)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "PNADC SIDRA 4093 / var 4096 / sexo total",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/4093",
            "url": "https://sidra.ibge.gov.br/tabela/4093",
        },
        "limitations": [
            "Força de trabalho / população 14+ — não é taxa de emprego nem desocupação.",
            "Estimativa amostral trimestral.",
        ],
    },
    "higher_education_share": {
        "name": "Pessoas de 14 anos ou mais com superior completo",
        "short_name": "Superior completo",
        "unit": "%",
        "status_label": "ESTIMADO",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "social",
        "group_label": "Social / saneamento",
        "frequency": "annual",
        "dataset_id": "ibge.higher_education_share.{period}",
        "table": "7128",
        "variable": "4104",
        "period": "all",
        "class_path": "c2/6794/c1568/99713",
        "definition": (
            "Distribuição percentual das pessoas de 14 anos ou mais de idade cujo nível de "
            "instrução é ensino superior completo (PNAD Contínua, SIDRA 7128 / variável 4104 / "
            "sexo total, categoria 99713)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "PNADC SIDRA 7128 / var 4104 / superior completo",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/7128",
            "url": "https://sidra.ibge.gov.br/tabela/7128",
        },
        "limitations": [
            "Percentual sobre pessoas de 14 anos ou mais, não sobre a população total nem só 25+.",
            "Estimativa amostral; equivalências da PNADC (não é diploma conferido no ano).",
        ],
    },
    "pns_tobacco_smokers": {
        "name": "Fumantes atuais de tabaco (18 anos ou mais) — PNS 2019",
        "short_name": "Fumantes (PNS 2019)",
        "unit": "%",
        "status_label": "ESTIMADO",
        "higher_is_worse": True,
        "kind": "observed_estimate",
        "group": "saude",
        "group_label": "Saúde",
        "frequency": "irregular",
        "dataset_id": "ibge.pns_tobacco_smokers.{period}",
        "table": "4173",
        "variable": "4163",
        "period": "2019",
        "class_path": "c2/6794/c1/6795",
        "definition": (
            "Percentual de pessoas de 18 anos ou mais de idade fumantes atuais de tabaco "
            "(PNS 2019, SIDRA 4173 / variável 4163, sexo total, situação do domicílio total)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "PNS 2019 SIDRA 4173 / var 4163",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/4173",
            "url": "https://sidra.ibge.gov.br/tabela/4173",
        },
        "limitations": [
            "Retrato da PNS 2019 — não atualizar mentalmente para 2024/2025.",
            "Estimativa amostral com coeficiente de variação; não é censo.",
        ],
    },
    "pns_diabetes": {
        "name": "Diagnóstico médico de diabetes (18 anos ou mais) — PNS 2019",
        "short_name": "Diabetes (PNS 2019)",
        "unit": "%",
        "status_label": "ESTIMADO",
        "higher_is_worse": True,
        "kind": "observed_estimate",
        "group": "saude",
        "group_label": "Saúde",
        "frequency": "irregular",
        "dataset_id": "ibge.pns_diabetes.{period}",
        "table": "4487",
        "variable": "4465",
        "period": "2019",
        "class_path": "c2/6794/c1/6795",
        "definition": (
            "Percentual de pessoas de 18 anos ou mais de idade que referem diagnóstico médico "
            "de diabetes (PNS 2019, SIDRA 4487 / variável 4465, sexo total, situação total)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "PNS 2019 SIDRA 4487 / var 4465",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/4487",
            "url": "https://sidra.ibge.gov.br/tabela/4487",
        },
        "limitations": [
            "Retrato da PNS 2019 — não é prevalência clínica atual.",
            "Autoreferido («diagnóstico médico»); subdiagnóstico e diferenças de acesso afetam o indicador.",
        ],
    },
    "pns_health_plan": {
        "name": "Cobertura de plano de saúde médico — PNS 2019",
        "short_name": "Plano de saúde (PNS 2019)",
        "unit": "%",
        "status_label": "ESTIMADO",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "saude",
        "group_label": "Saúde",
        "frequency": "irregular",
        "dataset_id": "ibge.pns_health_plan.{period}",
        "table": "7570",
        "variable": "10908",
        "period": "2019",
        "class_path": "c2/6794/c1/6795",
        "definition": (
            "Percentual de pessoas que tinham algum plano de saúde médico "
            "(PNS 2019, SIDRA 7570 / variável 10908, sexo total, situação total)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "PNS 2019 SIDRA 7570 / var 10908",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/7570",
            "url": "https://sidra.ibge.gov.br/tabela/7570",
        },
        "limitations": [
            "Retrato da PNS 2019 — cobertura posterior pode ter mudado.",
            "Plano médico apenas; não inclui só odontológico nem mede qualidade da cobertura.",
        ],
    },
    "pns_violence": {
        "name": "Pessoas de 18+ que sofreram violência nos últimos 12 meses — PNS 2019",
        "short_name": "Violência 12 meses (PNS 2019)",
        "unit": "%",
        "status_label": "ESTIMADO",
        "higher_is_worse": True,
        "kind": "observed_estimate",
        "group": "seguranca",
        "group_label": "Segurança",
        "frequency": "irregular",
        "dataset_id": "ibge.pns_violence.{period}",
        "table": "8022",
        "variable": "11396",
        "period": "2019",
        "class_path": "c2/6794/c1/6795",
        "definition": (
            "Percentual de pessoas de 18 anos ou mais de idade que sofreram violência nos "
            "últimos 12 meses (PNS 2019, SIDRA 8022 / variável 11396, sexo total, situação total)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "PNS 2019 SIDRA 8022 / var 11396",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/8022",
            "url": "https://sidra.ibge.gov.br/tabela/8022",
        },
        "limitations": [
            "Retrato da PNS 2019 — não é série anual do SIM nem Anuário FBSP.",
            "Violência autorreferida (física, psicológica, sexual etc. no questionário PNS); não confundir com homicídios.",
            "Estimativa amostral; subnotificação por medo ou estigma é possível.",
        ],
    },
    "pns_physical_violence": {
        "name": "Pessoas de 18+ que sofreram violência física nos últimos 12 meses — PNS 2019",
        "short_name": "Violência física (PNS 2019)",
        "unit": "%",
        "status_label": "ESTIMADO",
        "higher_is_worse": True,
        "kind": "observed_estimate",
        "group": "seguranca",
        "group_label": "Segurança",
        "frequency": "irregular",
        "dataset_id": "ibge.pns_physical_violence.{period}",
        "table": "8058",
        "variable": "11458",
        "period": "2019",
        "class_path": "c2/6794/c1/6795",
        "definition": (
            "Percentual de pessoas de 18 anos ou mais de idade que sofreram violência física "
            "nos últimos 12 meses (PNS 2019, SIDRA 8058 / variável 11458, sexo total, "
            "situação total). Não é assalto/roubo policial nem homicídio."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "PNS 2019 SIDRA 8058 / var 11458",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/8058",
            "url": "https://sidra.ibge.gov.br/tabela/8058",
        },
        "limitations": [
            "Retrato da PNS 2019 — violência física autorreferida, não BO de assalto.",
            "Não há série nacional UF de «assalto a pessoa» no SIDRA; o SINESP VDE publica "
            "roubos específicos (veículo, carga, etc.), não esse recorte.",
            "Estimativa amostral; subnotificação por medo ou estigma é possível.",
        ],
    },
    "pns_physical_women": {
        "name": "Mulheres de 18+ que sofreram violência física nos últimos 12 meses — PNS 2019",
        "short_name": "Violência física — mulheres (PNS 2019)",
        "unit": "%",
        "status_label": "ESTIMADO",
        "higher_is_worse": True,
        "kind": "observed_estimate",
        "group": "seguranca",
        "group_label": "Segurança",
        "frequency": "irregular",
        "dataset_id": "ibge.pns_physical_women.{period}",
        "table": "8058",
        "variable": "11458",
        "period": "2019",
        "class_path": "c2/110096/c1/6795",
        "definition": (
            "Percentual de mulheres de 18 anos ou mais de idade que sofreram violência física "
            "nos últimos 12 meses (PNS 2019, SIDRA 8058 / variável 11458, sexo feminino, "
            "situação total). Não é feminicídio."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "PNS 2019 SIDRA 8058 / var 11458 / sexo feminino",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/8058",
            "url": "https://sidra.ibge.gov.br/tabela/8058",
        },
        "limitations": [
            "Não é feminicídio (categoria penal) nem homicídio de mulheres do SIM.",
            "Retrato amostral de 2019; violência física autorreferida.",
        ],
    },
    "pns_psych_violence": {
        "name": "Pessoas de 18+ que sofreram violência psicológica nos últimos 12 meses — PNS 2019",
        "short_name": "Violência psicológica (PNS 2019)",
        "unit": "%",
        "status_label": "ESTIMADO",
        "higher_is_worse": True,
        "kind": "observed_estimate",
        "group": "seguranca",
        "group_label": "Segurança",
        "frequency": "irregular",
        "dataset_id": "ibge.pns_psych_violence.{period}",
        "table": "8049",
        "variable": "11445",
        "period": "2019",
        "class_path": "c2/6794/c1/6795",
        "definition": (
            "Percentual de pessoas de 18 anos ou mais de idade que sofreram violência "
            "psicológica nos últimos 12 meses (PNS 2019, SIDRA 8049 / variável 11445, "
            "sexo total, situação total)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "PNS 2019 SIDRA 8049 / var 11445",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/8049",
            "url": "https://sidra.ibge.gov.br/tabela/8049",
        },
        "limitations": [
            "Retrato da PNS 2019; autorreferida — não é registro policial.",
            "Estimativa amostral; não confundir com violência física nem homicídio.",
        ],
    },
    "pns_sexual_lifetime": {
        "name": "Pessoas de 18+ que sofreram violência sexual alguma vez na vida — PNS 2019",
        "short_name": "Violência sexual na vida (PNS 2019)",
        "unit": "%",
        "status_label": "ESTIMADO",
        "higher_is_worse": True,
        "kind": "observed_estimate",
        "group": "seguranca",
        "group_label": "Segurança",
        "frequency": "irregular",
        "dataset_id": "ibge.pns_sexual_lifetime.{period}",
        "table": "8076",
        "variable": "11482",
        "period": "2019",
        "class_path": "c2/6794/c1/6795",
        "definition": (
            "Percentual de pessoas de 18 anos ou mais de idade que sofreram violência sexual "
            "alguma vez na vida (PNS 2019, SIDRA 8076 / variável 11482, sexo total, "
            "situação total). A tabela de violência sexual nos últimos 12 meses (SIDRA 8067) "
            "não tem recorte UF — por isso este mapa usa a prevalência na vida."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "PNS 2019 SIDRA 8076 / var 11482",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/8076",
            "url": "https://sidra.ibge.gov.br/tabela/8076",
        },
        "limitations": [
            "É prevalência na vida, não incidência nos últimos 12 meses.",
            "SIDRA 8067 (12 meses) não publica UF — não inventamos esse recorte.",
            "Autorreferida; amostral; subnotificação por medo ou estigma é possível.",
        ],
    },
    "pns_alcohol": {
        "name": "Consumo mensal de álcool (18 anos ou mais) — PNS 2019",
        "short_name": "Álcool mensal (PNS 2019)",
        "unit": "%",
        "status_label": "ESTIMADO",
        "higher_is_worse": True,
        "kind": "observed_estimate",
        "group": "saude",
        "group_label": "Saúde",
        "frequency": "irregular",
        "dataset_id": "ibge.pns_alcohol.{period}",
        "table": "4394",
        "variable": "4277",
        "period": "2019",
        "class_path": "c2/6794/c1/6795",
        "definition": (
            "Percentual de pessoas de 18 anos ou mais de idade que costumam consumir bebida "
            "alcoólica uma vez ou mais por mês (PNS 2019, SIDRA 4394 / variável 4277, "
            "sexo total, situação total)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "PNS 2019 SIDRA 4394 / var 4277",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/4394",
            "url": "https://sidra.ibge.gov.br/tabela/4394",
        },
        "limitations": [
            "Retrato da PNS 2019 — não é consumo atual nem diagnóstico de dependência.",
            "Frequência autorreferida (≥1 vez ao mês); não mede volume em doses.",
        ],
    },
    "pns_hypertension": {
        "name": "Diagnóstico médico de hipertensão arterial (18 anos ou mais) — PNS 2019",
        "short_name": "Hipertensão (PNS 2019)",
        "unit": "%",
        "status_label": "ESTIMADO",
        "higher_is_worse": True,
        "kind": "observed_estimate",
        "group": "saude",
        "group_label": "Saúde",
        "frequency": "irregular",
        "dataset_id": "ibge.pns_hypertension.{period}",
        "table": "4418",
        "variable": "4399",
        "period": "2019",
        "class_path": "c2/6794/c1/6795",
        "definition": (
            "Percentual de pessoas de 18 anos ou mais de idade que referem diagnóstico "
            "médico de hipertensão arterial (PNS 2019, SIDRA 4418 / variável 4399, "
            "sexo total, situação total)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "PNS 2019 SIDRA 4418 / var 4399",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/4418",
            "url": "https://sidra.ibge.gov.br/tabela/4418",
        },
        "limitations": [
            "Retrato da PNS 2019 — não é prevalência clínica atual.",
            "Autoreferido («diagnóstico médico»); subdiagnóstico e diferenças de acesso afetam o indicador.",
        ],
    },
    "rented_share": {
        "name": "Domicílios alugados (Censo 2022)",
        "short_name": "Domicílios alugados",
        "unit": "%",
        "status_label": "OBSERVADO",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "moradia",
        "group_label": "Moradia",
        "frequency": "census",
        "dataset_id": "ibge.rented_share.{period}",
        "table": "9930",
        "variable": "1000381",
        "period": "2022",
        "class_path": "c65/95810/c63/1055/c125/2932",
        "definition": (
            "Percentual de domicílios particulares permanentes ocupados na condição de ocupação "
            "«Alugado» (Censo 2022, SIDRA 9930 / variável percentual 1000381, cômodos total, "
            "tipo total)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "Censo 2022 SIDRA 9930 / var 1000381 / Alugado",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/9930",
            "url": "https://sidra.ibge.gov.br/tabela/9930",
        },
        "limitations": [
            "Condição de ocupação — não é valor do aluguel em reais (o SIDRA 2022 não publica média de aluguel por UF).",
            "Não inclui imóvel próprio ainda pagando (financiamento) nem cedido.",
        ],
    },
    "owned_paying_share": {
        "name": "Domicílios próprios ainda pagando (Censo 2022)",
        "short_name": "Próprio ainda pagando",
        "unit": "%",
        "status_label": "OBSERVADO",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "moradia",
        "group_label": "Moradia",
        "frequency": "census",
        "dataset_id": "ibge.owned_paying_share.{period}",
        "table": "9930",
        "variable": "1000381",
        "period": "2022",
        "class_path": "c65/95810/c63/4343/c125/2932",
        "definition": (
            "Percentual de domicílios particulares permanentes ocupados «próprio de algum morador "
            "— ainda pagando» (Censo 2022, SIDRA 9930 / variável percentual 1000381)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "Censo 2022 SIDRA 9930 / var 1000381 / ainda pagando",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/9930",
            "url": "https://sidra.ibge.gov.br/tabela/9930",
        },
        "limitations": [
            "Prestação/financiamento autorreferido no Censo — não é valor da parcela nem aluguel.",
            "Não usar como ranking de «custo de moradia».",
        ],
    },
    "owned_paid_share": {
        "name": "Domicílios próprios já pagos (Censo 2022)",
        "short_name": "Próprio já pago",
        "unit": "%",
        "status_label": "OBSERVADO",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "moradia",
        "group_label": "Moradia",
        "frequency": "census",
        "dataset_id": "ibge.owned_paid_share.{period}",
        "table": "9930",
        "variable": "1000381",
        "period": "2022",
        "class_path": "c65/95810/c63/73126/c125/2932",
        "definition": (
            "Percentual de domicílios particulares permanentes ocupados «próprio de algum morador "
            "— já pago, herdado ou ganho» (Censo 2022, SIDRA 9930 / variável percentual 1000381)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "Censo 2022 SIDRA 9930 / var 1000381 / já pago",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/9930",
            "url": "https://sidra.ibge.gov.br/tabela/9930",
        },
        "limitations": [
            "Inclui herdado ou ganho; não mede qualidade nem valor venal.",
        ],
    },
}

SIDRA_VALUE_SPECS: dict[str, dict[str, Any]] = {
    "gini_household": {
        "name": "Índice de Gini do rendimento domiciliar per capita",
        "short_name": "Gini (renda)",
        "unit": "índice",
        "status_label": "ESTIMADO",
        "higher_is_worse": True,
        "kind": "observed_estimate",
        "group": "economia",
        "group_label": "Economia / demografia",
        "frequency": "annual",
        "dataset_id": "ibge.gini_household.{period}",
        "table": "7435",
        "variable": "10681",
        "period": "all",
        "class_path": "",
        "definition": (
            "Índice de Gini do rendimento domiciliar per capita, a preços médios do ano "
            "(PNAD Contínua anual, SIDRA 7435 / variável 10681). 0 = igualdade; tende a 1 "
            "com maior desigualdade."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "PNADC anual SIDRA 7435 / var 10681",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/7435",
            "url": "https://sidra.ibge.gov.br/tabela/7435",
        },
        "limitations": [
            "Estimativa amostral da PNAD Contínua; não é censo.",
            "Não usar como IDHM nem como ranking de «melhor estado».",
        ],
    },
    "household_income_pc": {
        "name": "Rendimento médio mensal real domiciliar per capita",
        "short_name": "Renda domiciliar/hab",
        "unit": "BRL/mês",
        "status_label": "ESTIMADO",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "economia",
        "group_label": "Economia / demografia",
        "frequency": "annual",
        "dataset_id": "ibge.household_income_pc.{period}",
        "table": "7532",
        "variable": "10824",
        "period": "all",
        "class_path": "c1042/49283",
        "definition": (
            "Rendimento médio mensal real domiciliar per capita, a preços médios do ano, "
            "classe acumulada Total (PNAD Contínua, SIDRA 7532 / variável 10824 / "
            "classificação 1042 categoria 49283)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "PNADC SIDRA 7532 / var 10824 / Total",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/7532",
            "url": "https://sidra.ibge.gov.br/tabela/7532",
        },
        "limitations": [
            "Média do Total da distribuição — não é mediana nem renda do trabalho isolada.",
            "A preços médios do ano (deflacionamento PNADC); não confundir com PIB per capita.",
            "Série 2020–2022 usa quintas visitas por causa da pandemia (nota IBGE da tabela).",
        ],
    },
    "aging_index": {
        "name": "Índice de envelhecimento (Censo 2022)",
        "short_name": "Envelhecimento",
        "unit": "por 100 jovens",
        "status_label": "OBSERVADO",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "territorio",
        "group_label": "Território",
        "frequency": "census",
        "dataset_id": "ibge.aging_index.{period}",
        "table": "9515",
        "variable": "10612",
        "period": "2022",
        "class_path": "",
        "definition": (
            "Índice de envelhecimento da população residente (Censo 2022, SIDRA 9515 / "
            "variável 10612): razão IBGE entre o grupo etário de 65 anos ou mais e o de "
            "0 a 14 anos, expressa por 100 pessoas de 0 a 14 anos."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "Censo 2022 SIDRA 9515 / var 10612",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/9515",
            "url": "https://sidra.ibge.gov.br/tabela/9515",
        },
        "limitations": [
            "Variável oficial do Censo 2022 — não é esperança de vida nem taxa de mortalidade.",
            "O recorte IBGE usa 65+ no numerador; o Estatuto do Idoso usa 60 anos.",
            "Não usar como ranking de «estado mais velho para morar».",
        ],
    },
    "median_age": {
        "name": "Idade mediana da população (Censo 2022)",
        "short_name": "Idade mediana",
        "unit": "anos",
        "status_label": "OBSERVADO",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "territorio",
        "group_label": "Território",
        "frequency": "census",
        "dataset_id": "ibge.median_age.{period}",
        "table": "9515",
        "variable": "10613",
        "period": "2022",
        "class_path": "",
        "definition": (
            "Idade mediana da população residente (Censo 2022, SIDRA 9515 / variável 10613)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "Censo 2022 SIDRA 9515 / var 10613",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/9515",
            "url": "https://sidra.ibge.gov.br/tabela/9515",
        },
        "limitations": [
            "Retrato censitário de 2022; não atualizar com projeções posteriores.",
            "Mediana, não média etária.",
        ],
    },
    "sex_ratio": {
        "name": "Razão de sexo (Censo 2022)",
        "short_name": "Razão de sexo",
        "unit": "homens/100 mulheres",
        "status_label": "OBSERVADO",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "territorio",
        "group_label": "Território",
        "frequency": "census",
        "dataset_id": "ibge.sex_ratio.{period}",
        "table": "9515",
        "variable": "8845",
        "period": "2022",
        "class_path": "",
        "definition": (
            "Razão de sexo da população residente (Censo 2022, SIDRA 9515 / variável 8845): "
            "homens por 100 mulheres."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "Censo 2022 SIDRA 9515 / var 8845",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/9515",
            "url": "https://sidra.ibge.gov.br/tabela/9515",
        },
        "limitations": [
            "Razão demográfica oficial; não é índice de «equidade de gênero» nem mercado de trabalho.",
        ],
    },
    "labor_income": {
        "name": "Rendimento médio mensal real do trabalho (ocupados 14+)",
        "short_name": "Renda do trabalho",
        "unit": "BRL/mês",
        "status_label": "ESTIMADO",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "economia",
        "group_label": "Economia / demografia",
        "frequency": "quarterly",
        "dataset_id": "ibge.labor_income.{period}",
        "table": "6469",
        "variable": "5935",
        "period": "all",
        "class_path": "",
        "definition": (
            "Rendimento médio mensal real das pessoas de 14 anos ou mais ocupadas na semana "
            "de referência, com rendimento de trabalho, efetivamente recebido em todos os "
            "trabalhos (PNAD Contínua, SIDRA 6469 / variável 5935)."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "PNADC SIDRA 6469 / var 5935",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/6469",
            "url": "https://sidra.ibge.gov.br/tabela/6469",
        },
        "limitations": [
            "Média dos ocupados com rendimento de trabalho — não é renda domiciliar per capita nem PIB per capita.",
            "Série trimestral; a preços reais da PNADC.",
        ],
    },
    "cempre_avg_wage": {
        "name": "Salário médio mensal das empresas formais (CEMPRE)",
        "short_name": "Salário formal médio",
        "unit": "BRL/mês",
        "status_label": "OBSERVADO",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "economia",
        "group_label": "Economia / demografia",
        "frequency": "annual",
        "dataset_id": "ibge.cempre_avg_wage.{period}",
        "table": "9509",
        "variable": "10143",
        "period": "all",
        "class_path": "",
        "definition": (
            "Salário médio mensal em reais das unidades locais do Cadastro Central de Empresas "
            "(CEMPRE, SIDRA 9509 / variável 10143). Universo formal (CNPJ ativo), exclusive MEI."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "CEMPRE SIDRA 9509 / var 10143",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/9509",
            "url": "https://sidra.ibge.gov.br/tabela/9509",
        },
        "limitations": [
            "Salário do cadastro formal — não inclui informal nem MEI.",
            "Não confundir com rendimento PNADC (todas as ocupações) nem com salário mínimo legal.",
            "Série a partir de 2022 (quebra metodológica; não encadear com CEMPRE 2006–2021).",
        ],
    },
    "cempre_wage_in_sm": {
        "name": "Salário médio formal em salários mínimos (CEMPRE)",
        "short_name": "Salário formal / SM",
        "unit": "salários mínimos",
        "status_label": "OBSERVADO",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "economia",
        "group_label": "Economia / demografia",
        "frequency": "annual",
        "dataset_id": "ibge.cempre_wage_in_sm.{period}",
        "table": "9509",
        "variable": "1606",
        "period": "all",
        "class_path": "",
        "definition": (
            "Salário médio mensal expresso em salários mínimos do Cadastro Central de Empresas "
            "(CEMPRE, SIDRA 9509 / variável 1606). Quociente oficial do IBGE, não uma razão local nossa."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "CEMPRE SIDRA 9509 / var 1606",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/9509",
            "url": "https://sidra.ibge.gov.br/tabela/9509",
        },
        "limitations": [
            "Usa o salário mínimo de referência do IBGE no ano do CEMPRE, não o decreto vigente na data do mapa.",
            "Universo formal, exclusive MEI.",
        ],
    },
    "cempre_firms": {
        "name": "Empresas e organizações atuantes (CEMPRE)",
        "short_name": "Empresas formais",
        "unit": "empresas",
        "status_label": "OBSERVADO",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "economia",
        "group_label": "Economia / demografia",
        "frequency": "annual",
        "dataset_id": "ibge.cempre_firms.{period}",
        "table": "9509",
        "variable": "367",
        "period": "all",
        "class_path": "",
        "definition": (
            "Número de empresas e outras organizações atuantes no Cadastro Central de Empresas "
            "(CEMPRE, SIDRA 9509 / variável 367). Formalmente constituídas (CNPJ), exclusive MEI."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "CEMPRE SIDRA 9509 / var 367",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/9509",
            "url": "https://sidra.ibge.gov.br/tabela/9509",
        },
        "limitations": [
            "Estoque cadastral — não é abertura/fechamento no ano nem ambiente de negócios.",
            "Não incluir MEI; UF da unidade local, não da sede se diferirem no recorte da tabela.",
        ],
    },
    "cempre_jobs": {
        "name": "Pessoal ocupado total nas empresas formais (CEMPRE)",
        "short_name": "Empregos formais (CEMPRE)",
        "unit": "pessoas",
        "status_label": "OBSERVADO",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "economia",
        "group_label": "Economia / demografia",
        "frequency": "annual",
        "dataset_id": "ibge.cempre_jobs.{period}",
        "table": "9509",
        "variable": "707",
        "period": "all",
        "class_path": "",
        "definition": (
            "Pessoal ocupado total em 31 de dezembro nas unidades locais do Cadastro Central "
            "de Empresas (CEMPRE, SIDRA 9509 / variável 707). Universo formal (CNPJ), exclusive MEI."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "CEMPRE SIDRA 9509 / var 707",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/9509",
            "url": "https://sidra.ibge.gov.br/tabela/9509",
        },
        "limitations": [
            "Estoque formal em 31/12 — não é PNADC (inclui informal) nem empregos gerados no ano.",
            "Exclusive MEI. Contagem absoluta: UFs grandes dominam.",
        ],
    },
    "employer_unit_births": {
        "name": "Nascimentos de unidades locais empregadoras",
        "short_name": "Aberturas (empregadoras)",
        "unit": "unidades locais",
        "status_label": "OBSERVADO",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "economia",
        "group_label": "Economia / demografia",
        "frequency": "annual",
        "dataset_id": "ibge.employer_unit_births.{period}",
        "table": "9925",
        "variable": "13220",
        "period": "all",
        "class_path": "c12762/117897/c371/73120",
        "definition": (
            "Número de nascimentos de unidades locais empregadoras (Demografia das Empresas, "
            "SIDRA 9925 / variável 13220, evento 73120, CNAE Total). Exclusive MEI."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 9925 / var 13220 / nascimento",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/9925",
            "url": "https://sidra.ibge.gov.br/tabela/9925",
        },
        "limitations": [
            "Contagem absoluta — UFs grandes dominam; compare também a taxa de nascimento.",
            "Empregadoras (com assalariado); exclusive MEI. A tabela 9924 (empresa, não UL) não tem N3.",
            "SIDRA publica «-» para morte de unidade local por UF nesta tabela — mortalidade não entra.",
        ],
    },
    "employer_survival_1y": {
        "name": "Sobrevivência de 1 ano das unidades locais empregadoras",
        "short_name": "Sobrevivência 1 ano",
        "unit": "%",
        "status_label": "OBSERVADO",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "economia",
        "group_label": "Economia / demografia",
        "frequency": "annual",
        "dataset_id": "ibge.employer_survival_1y.{period}",
        "table": "9950",
        "variable": "13235",
        "period": "all",
        "class_path": "c12762/117897",
        "definition": (
            "Taxa de 1 ano de sobrevivência das unidades locais empregadoras (SIDRA 9950 / "
            "variável 13235, CNAE Total). Percentual oficial do IBGE, não uma razão local."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 9950 / var 13235",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/9950",
            "url": "https://sidra.ibge.gov.br/tabela/9950",
        },
        "limitations": [
            "O ano da tabela é o recorte SIDRA; a nota da tabela define a coorte — não inventar o ano de nascimento.",
            "Exclusive MEI; 5 anos de sobrevivência vem «...» no último ano e não entra.",
        ],
    },
}

SIDRA_UF_SPECS: dict[str, dict[str, Any]] = {**SIDRA_PERCENT_SPECS, **SIDRA_VALUE_SPECS}


def _assert_sidra_value(indicator_id: str, unit: str, code: str, val: float) -> None:
    if unit == "%" and not 0 <= val <= 100:
        raise RuntimeError(f"{indicator_id}: % out of range for {code}: {val}")
    if unit == "índice" and not 0 <= val <= 1:
        raise RuntimeError(f"{indicator_id}: Gini out of range for {code}: {val}")
    if unit == "anos" and not 0 < val < 120:
        raise RuntimeError(f"{indicator_id}: age out of range for {code}: {val}")
    if unit == "homens/100 mulheres" and not 50 < val < 150:
        raise RuntimeError(f"{indicator_id}: sex ratio out of range for {code}: {val}")
    if unit == "salários mínimos" and not 0 < val < 30:
        raise RuntimeError(f"{indicator_id}: SM multiple out of range for {code}: {val}")
    if unit.startswith("por ") and val < 0:
        raise RuntimeError(f"{indicator_id}: negative rate for {code}: {val}")
    if unit in {"BRL", "BRL/mês"} and val < 0:
        raise RuntimeError(f"{indicator_id}: negative income for {code}: {val}")
    if unit == "pessoas" and val < 0:
        raise RuntimeError(f"{indicator_id}: negative headcount for {code}: {val}")
    if unit == "unidades locais" and val < 0:
        raise RuntimeError(f"{indicator_id}: negative local units for {code}: {val}")


def fetch_sidra_uf_indicator(indicator_id: str) -> dict[str, Any]:
    if indicator_id not in SIDRA_UF_SPECS:
        raise KeyError(indicator_id)
    spec = SIDRA_UF_SPECS[indicator_id]
    period_token = str(spec["period"])
    class_path = str(spec.get("class_path") or "")
    url = (
        f"https://apisidra.ibge.gov.br/values/t/{spec['table']}/n3/all"
        f"/v/{spec['variable']}/p/{period_token}"
    )
    if class_path:
        url += f"/{class_path}"
    url += "?formato=json"
    rows = _fetch_sidra(url, f"sidra_{spec['table']}_{spec['variable']}_{period_token}.json")
    estados = _estados()
    unit = str(spec["unit"])

    def records_from(mapped: dict[str, float]) -> list[dict[str, Any]]:
        if set(mapped) != set(UF_CODES):
            raise RuntimeError(f"{indicator_id}: expected 27 UFs, got {sorted(mapped)}")
        out = []
        for code in sorted(UF_CODES):
            val = mapped[code]
            _assert_sidra_value(indicator_id, unit, code, val)
            meta = estados[code]
            out.append(
                {
                    "ibge_code": code,
                    "uf": meta["uf"],
                    "name": meta["name"],
                    "value": val,
                }
            )
        return out

    series: dict[str, list[dict[str, Any]]] | None = None
    if period_token in {"last", "all"}:
        by_year: dict[str, dict[str, float]] = {}
        for row in rows[1:]:
            code = str(row.get("D1C") or "")
            if code not in UF_CODES:
                continue
            year = str(row.get("D3C") or "")
            val = _sidra_float(str(row.get("V") or ""))
            if not year.isdigit() or val is None:
                continue
            by_year.setdefault(year, {})[code] = val
        complete = {
            year: mapped
            for year, mapped in by_year.items()
            if set(mapped) == set(UF_CODES)
        }
        if not complete:
            raise RuntimeError(f"{indicator_id}: no SIDRA year with 27 UFs")
        series = {year: records_from(mapped) for year, mapped in sorted(complete.items())}
        period = max(complete, key=int)
        records = series[period]
    else:
        period = period_token
        records = records_from(_sidra_uf_map(rows))

    fixture = _base_fixture(
        indicator_id=indicator_id,
        spec=spec,
        period=period,
        records=records,
        api_url=url,
        series=series,
    )
    return _write_ibge_indicator(fixture)


def fetch_sidra_percent_indicator(indicator_id: str) -> dict[str, Any]:
    return fetch_sidra_uf_indicator(indicator_id)


def fetch_health_security_layers() -> dict[str, Any]:
    return {ind: fetch_sidra_uf_indicator(ind) for ind in SIDRA_UF_SPECS}


def _population_by_uf(period: str) -> dict[str, float] | None:
    """Load UF population for a calendar year without touching population_uf_2025.json."""
    agg_url = (
        f"https://servicodados.ibge.gov.br/api/v3/agregados/6579/periodos/{period}"
        "/variaveis/9324?localidades=N3[all]"
    )
    try:
        raw = fetch_bytes(agg_url, timeout=90)
        payload = json.loads(raw.decode("utf-8"))
        series = payload[0]["resultados"][0]["series"]
        out: dict[str, float] = {}
        for item in series:
            code = str(item["localidade"]["id"]).zfill(2)
            raw_val = str(item["serie"][period]).replace(".", "").replace(",", "")
            out[code] = float(int(raw_val))
        if set(out) == set(UF_CODES):
            snapshot_raw(
                "ibge",
                f"populacao_uf_{period}_sidecar.json",
                raw,
                {"source_url": agg_url, "connector": "ibge.agregados.populacao_uf.sidecar"},
            )
            return out
    except Exception:
        pass
    sidra_url = f"https://apisidra.ibge.gov.br/values/t/6579/n3/all/v/9324/p/{period}?formato=json"
    try:
        mapped = _sidra_uf_map(_fetch_sidra(sidra_url, f"sidra_6579_{period}.json"))
        if set(mapped) == set(UF_CODES) and all(v > 0 for v in mapped.values()):
            return mapped
    except Exception:
        pass
    return None


def _population_periods() -> list[str]:
    url = "https://servicodados.ibge.gov.br/api/v3/agregados/6579/periodos"
    raw = fetch_bytes(url, timeout=60)
    payload = json.loads(raw.decode("utf-8"))
    return [str(item["id"] if isinstance(item, dict) else item) for item in payload]


def _nearest_available_pop_period(target: str) -> str | None:
    years = [p for p in _population_periods() if p.isdigit()]
    if not years:
        return None
    if target in years:
        return target
    later = [p for p in years if int(p) >= int(target)]
    if later:
        return min(later, key=int)
    return max(years, key=int)


def fetch_pib_per_capita() -> dict[str, Any]:
    pib = json.loads((fixtures_dir() / "ibge" / "pib_uf_latest.json").read_text(encoding="utf-8"))
    pib_period = str(pib.get("reference_period") or "")
    if len(pib_period) != 4:
        raise RuntimeError("pib_per_capita: PIB fixture missing calendar year")
    pop_period = _nearest_available_pop_period(pib_period) or pib_period
    pop_same = _population_by_uf(pop_period)
    if pop_same is None:
        pop_latest = json.loads(
            (fixtures_dir() / "ibge" / "population_uf_2025.json").read_text(encoding="utf-8")
        )
        pop_period = str(pop_latest.get("reference_date") or "2025")[:4]
        pop_same = {str(r["ibge_code"]): float(r["population"]) for r in pop_latest["records"]}
        if set(pop_same) != set(UF_CODES):
            raise RuntimeError("pib_per_capita: population fixture UF mismatch")
    mixed = pop_period != pib_period
    estados = _estados()
    records = []
    for row in sorted(pib["records"], key=lambda r: str(r["ibge_code"])):
        code = str(row["ibge_code"])
        pop_n = pop_same[code]
        if pop_n <= 0:
            raise RuntimeError(f"pib_per_capita: non-positive population for {code}")
        meta = estados[code]
        records.append(
            {
                "ibge_code": code,
                "uf": meta["uf"],
                "name": meta["name"],
                "value": round(float(row["pib_brl"]) / pop_n, 2),
            }
        )
    if mixed:
        definition = (
            f"PIB a preços correntes IBGE 5938/37 ({pib_period}) dividido pela população "
            f"residente estimada IBGE 6579 ({pop_period}). Anos diferentes — não é "
            "PIB per capita oficial da publicação de contas regionais. "
            f"A tabela 6579 não publica o ano {pib_period}; usa-se o período disponível mais próximo posterior."
        )
        limitations = [
            f"DERIVADO com anos mistos: PIB {pib_period} ÷ população {pop_period} "
            f"(6579 não tem {pib_period}).",
            "A tabela SIDRA 5938 não publica variável de PIB per capita; este recorte é razão local.",
            "Não usar como renda domiciliar nem como IDHM.",
        ]
        period = pib_period
        dataset = f"5938/37 (PIB {pib_period}) ÷ 6579 (pop {pop_period})"
    else:
        definition = (
            f"PIB a preços correntes IBGE 5938/37 ({pib_period}) dividido pela população "
            f"residente estimada IBGE 6579 do mesmo ano ({pib_period})."
        )
        limitations = [
            "Razão local de duas séries oficiais (rótulo DERIVADO); a tabela 5938 não traz PIB per capita.",
            "PIB a preços correntes ÷ habitantes estimados — não é PIB per capita da publicação de contas regionais se o IBGE usar outro denominador.",
            "Não usar como renda domiciliar nem como IDHM.",
        ]
        period = pib_period
        dataset = f"5938/37 ÷ 6579 ({pib_period})"
    spec = {
        "name": "PIB per capita (derivado)",
        "short_name": "PIB per capita",
        "unit": "BRL/hab",
        "status_label": "DERIVADO",
        "higher_is_worse": False,
        "kind": "derived",
        "group": "economia",
        "group_label": "Economia / demografia",
        "frequency": "annual",
        "dataset_id": "ibge.pib_per_capita.{period}",
        "definition": definition,
        "source": {
            "organization": "IBGE",
            "dataset": dataset,
            "dataset_page": "https://sidra.ibge.gov.br/tabela/5938",
            "url": "https://sidra.ibge.gov.br/tabela/5938",
        },
        "limitations": limitations,
    }
    fixture = _base_fixture(
        indicator_id="pib_per_capita", spec=spec, period=period, records=records
    )
    return _write_ibge_indicator(fixture)


_CENSUS_AGE_TOTAL = "100362"
_GEN_LIMITATIONS = [
    "Apelido geracional é recorte local sobre grupos etários oficiais de 5 anos (DERIVADO) — o IBGE não classifica gerações.",
    "Idade em anos completos no Censo 2022; anos de nascimento são aproximados e não coincidem com todas as definições (Pew, imprensa, etc.).",
    "Não somar com 0–14 ou 60+ para «fechar 100%»: esses recortes usam outros cortes de idade.",
]

_CENSUS_AGE_SHARES: dict[str, dict[str, Any]] = {
    "share_0_14": {
        "cats": ("93070", "93084", "93085"),
        "name": "População de 0 a 14 anos (Censo 2022)",
        "short_name": "0–14 anos",
        "group": "territorio",
        "group_label": "Território",
        "definition": (
            "Percentual de pessoas de 0 a 14 anos na população residente (Censo 2022, "
            "SIDRA 9514 / variável 93): soma dos grupos oficiais 0–4, 5–9 e 10–14 "
            "(categorias 93070+93084+93085) dividida pelo total (100362)."
        ),
        "limitations": [
            "Razão local de grupos etários oficiais da mesma tabela (rótulo DERIVADO).",
            "Não é «índice de juventude» nem a variável percentual pronta do SIDRA.",
        ],
    },
    "share_60_plus": {
        "cats": (
            "93095",
            "93096",
            "93097",
            "93098",
            "49108",
            "49109",
            "60040",
            "60041",
            "6653",
        ),
        "name": "População de 60 anos ou mais (Censo 2022)",
        "short_name": "60 anos ou mais",
        "group": "territorio",
        "group_label": "Território",
        "definition": (
            "Percentual de pessoas de 60 anos ou mais na população residente (Censo 2022, "
            "SIDRA 9514 / variável 93): soma dos grupos oficiais de 5 anos a partir de 60 "
            "(até 100 anos ou mais) dividida pelo total (100362)."
        ),
        "limitations": [
            "Razão local de grupos etários oficiais da mesma tabela (rótulo DERIVADO).",
            "Corte 60+ segue o Estatuto do Idoso; o índice de envelhecimento IBGE 9515 usa 65+.",
        ],
    },
    "share_gen_alpha": {
        "cats": ("93070", "93084"),
        "name": "Geração Alpha (0 a 9 anos) — Censo 2022",
        "short_name": "Alpha (0–9)",
        "group": "demografia",
        "group_label": "Gerações (Censo 2022)",
        "partition": "generations",
        "definition": (
            "Percentual de pessoas de 0 a 9 anos na população residente (Censo 2022, SIDRA 9514): "
            "grupos oficiais 0–4 e 5–9 ÷ total. Apelido Alpha = nascidos aproximadamente em 2013–2022."
        ),
        "limitations": _GEN_LIMITATIONS,
    },
    "share_gen_z": {
        "cats": ("93085", "93086", "93087"),
        "name": "Geração Z (10 a 24 anos) — Censo 2022",
        "short_name": "Geração Z (10–24)",
        "group": "demografia",
        "group_label": "Gerações (Censo 2022)",
        "partition": "generations",
        "definition": (
            "Percentual de pessoas de 10 a 24 anos na população residente (Censo 2022, SIDRA 9514): "
            "grupos oficiais 10–14, 15–19 e 20–24 ÷ total. Apelido Z = nascidos aproximadamente em 1998–2012."
        ),
        "limitations": _GEN_LIMITATIONS,
    },
    "share_gen_y": {
        "cats": ("93088", "93089", "93090"),
        "name": "Millennials (25 a 39 anos) — Censo 2022",
        "short_name": "Millennials (25–39)",
        "group": "demografia",
        "group_label": "Gerações (Censo 2022)",
        "partition": "generations",
        "definition": (
            "Percentual de pessoas de 25 a 39 anos na população residente (Censo 2022, SIDRA 9514): "
            "grupos oficiais 25–29, 30–34 e 35–39 ÷ total. Apelido millennial / Y = nascidos "
            "aproximadamente em 1983–1997."
        ),
        "limitations": _GEN_LIMITATIONS,
    },
    "share_gen_x": {
        "cats": ("93091", "93092", "93093", "93094"),
        "name": "Geração X (40 a 59 anos) — Censo 2022",
        "short_name": "Geração X (40–59)",
        "group": "demografia",
        "group_label": "Gerações (Censo 2022)",
        "partition": "generations",
        "definition": (
            "Percentual de pessoas de 40 a 59 anos na população residente (Censo 2022, SIDRA 9514): "
            "grupos oficiais 40–44 a 55–59 ÷ total. Apelido X = nascidos aproximadamente em 1963–1982."
        ),
        "limitations": _GEN_LIMITATIONS,
    },
    "share_gen_boomer": {
        "cats": ("93095", "93096", "93097", "93098"),
        "name": "Baby boomers (60 a 79 anos) — Censo 2022",
        "short_name": "Boomers (60–79)",
        "group": "demografia",
        "group_label": "Gerações (Censo 2022)",
        "partition": "generations",
        "definition": (
            "Percentual de pessoas de 60 a 79 anos na população residente (Censo 2022, SIDRA 9514): "
            "grupos oficiais 60–64 a 75–79 ÷ total. Apelido baby boom = nascidos aproximadamente em 1943–1962."
        ),
        "limitations": _GEN_LIMITATIONS,
    },
    "share_gen_silent": {
        "cats": ("49108", "49109", "60040", "60041", "6653"),
        "name": "80 anos ou mais (gerações anteriores) — Censo 2022",
        "short_name": "80+ (anteriores)",
        "group": "demografia",
        "group_label": "Gerações (Censo 2022)",
        "partition": "generations",
        "definition": (
            "Percentual de pessoas de 80 anos ou mais na população residente (Censo 2022, SIDRA 9514): "
            "grupos oficiais 80–84 até 100 anos ou mais ÷ total. Nascidos aproximadamente até 1942."
        ),
        "limitations": _GEN_LIMITATIONS,
    },
}

_DEPENDENCY_WORKING_CATS = (
    "93086",
    "93087",
    "93088",
    "93089",
    "93090",
    "93091",
    "93092",
    "93093",
    "93094",
)


def _sidra_year_uf_map(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    by_year: dict[str, dict[str, float]] = {}
    for row in rows[1:]:
        code = str(row.get("D1C") or "")
        if code not in UF_CODES:
            continue
        year = str(row.get("D3C") or "")
        val = _sidra_float(str(row.get("V") or ""))
        if not year.isdigit() or val is None:
            continue
        bucket = by_year.setdefault(year, {})
        if code in bucket:
            raise RuntimeError(f"SIDRA duplicate cell {code}@{year}")
        bucket[code] = val
    return {year: mapped for year, mapped in by_year.items() if set(mapped) == set(UF_CODES)}


def _population_series_map() -> dict[str, dict[str, float]]:
    url = "https://apisidra.ibge.gov.br/values/t/6579/n3/all/v/9324/p/all?formato=json"
    return _sidra_year_uf_map(_fetch_sidra(url, "sidra_6579_all.json"))


def fetch_census_age_shares() -> dict[str, Any]:
    """Censo 2022 SIDRA 9514: official 5-year groups → % layers (idade e gerações)."""
    period = "2022"
    cats = [_CENSUS_AGE_TOTAL]
    for spec in _CENSUS_AGE_SHARES.values():
        cats.extend(spec["cats"])
    cats.extend(_DEPENDENCY_WORKING_CATS)
    cat_path = ",".join(dict.fromkeys(cats))
    url = (
        "https://apisidra.ibge.gov.br/values/t/9514/n3/all/v/93/p/2022"
        f"/c2/6794/c287/{cat_path}/c286/113635?formato=json"
    )
    rows = _fetch_sidra(url, "sidra_9514_age_groups.json")
    by_cat: dict[str, dict[str, float]] = {}
    for row in rows[1:]:
        code = str(row.get("D1C") or "")
        cat = str(row.get("D5C") or "")
        val = _sidra_float(str(row.get("V") or ""))
        if code not in UF_CODES or val is None:
            continue
        by_cat.setdefault(cat, {})[code] = val
    total = by_cat.get(_CENSUS_AGE_TOTAL) or {}
    if set(total) != set(UF_CODES) or any(v <= 0 for v in total.values()):
        raise RuntimeError("share_age: SIDRA 9514 total missing or non-positive")
    estados = _estados()
    summed_by_id: dict[str, dict[str, float]] = {}
    wrote: dict[str, Any] = {}
    for indicator_id, age_spec in _CENSUS_AGE_SHARES.items():
        summed: dict[str, float] = {}
        for cat in age_spec["cats"]:
            mapped = by_cat.get(cat) or {}
            if set(mapped) != set(UF_CODES):
                raise RuntimeError(f"{indicator_id}: SIDRA 9514 cat {cat} missing UFs")
            for code, val in mapped.items():
                summed[code] = summed.get(code, 0.0) + val
        summed_by_id[indicator_id] = summed
        records = []
        for code in sorted(UF_CODES):
            share = round(100.0 * summed[code] / total[code], 1)
            if not 0 <= share <= 100:
                raise RuntimeError(f"{indicator_id}: % out of range for {code}: {share}")
            meta = estados[code]
            records.append(
                {
                    "ibge_code": code,
                    "uf": meta["uf"],
                    "name": meta["name"],
                    "value": share,
                }
            )
        spec = {
            "name": age_spec["name"],
            "short_name": age_spec["short_name"],
            "unit": "%",
            "status_label": "DERIVADO",
            "higher_is_worse": False,
            "kind": "derived",
            "group": age_spec.get("group") or "territorio",
            "group_label": age_spec.get("group_label") or "Território",
            "frequency": "census",
            "dataset_id": f"ibge.{indicator_id}.{{period}}",
            "definition": age_spec["definition"],
            "source": {
                "organization": "IBGE",
                "dataset": f"SIDRA 9514 / var 93 / grupos÷{_CENSUS_AGE_TOTAL}",
                "dataset_page": "https://sidra.ibge.gov.br/tabela/9514",
                "url": "https://sidra.ibge.gov.br/tabela/9514",
            },
            "limitations": list(age_spec["limitations"]),
        }
        fixture = _base_fixture(
            indicator_id=indicator_id, spec=spec, period=period, records=records, api_url=url
        )
        wrote[indicator_id] = _write_ibge_indicator(fixture)
    gen_ids = [k for k, spec in _CENSUS_AGE_SHARES.items() if spec.get("partition") == "generations"]
    for code in UF_CODES:
        covered = sum(summed_by_id[gid][code] for gid in gen_ids)
        if abs(covered - total[code]) > 1:
            raise RuntimeError(
                f"generation partition: {code} sum={covered} total={total[code]}"
            )
    working: dict[str, float] = {}
    for cat in _DEPENDENCY_WORKING_CATS:
        mapped = by_cat.get(cat) or {}
        if set(mapped) != set(UF_CODES):
            raise RuntimeError(f"dependency_ratio: SIDRA 9514 cat {cat} missing UFs")
        for code, val in mapped.items():
            working[code] = working.get(code, 0.0) + val
    dep_records = []
    for code in sorted(UF_CODES):
        den = working[code]
        if den <= 0:
            raise RuntimeError(f"dependency_ratio: non-positive working-age for {code}")
        young = summed_by_id["share_0_14"][code]
        old = summed_by_id["share_60_plus"][code]
        ratio = round(100.0 * (young + old) / den, 1)
        if ratio < 0 or ratio > 200:
            raise RuntimeError(f"dependency_ratio: implausible for {code}: {ratio}")
        meta = estados[code]
        dep_records.append(
            {
                "ibge_code": code,
                "uf": meta["uf"],
                "name": meta["name"],
                "value": ratio,
            }
        )
    dep_spec = {
        "name": "Razão de dependência etária (0–14 + 60+ ÷ 15–59)",
        "short_name": "Dependência etária",
        "unit": "por 100 adultos",
        "status_label": "DERIVADO",
        "higher_is_worse": False,
        "kind": "derived",
        "group": "territorio",
        "group_label": "Território",
        "frequency": "census",
        "dataset_id": "ibge.dependency_ratio.{period}",
        "definition": (
            "Razão entre a soma dos grupos oficiais de 0 a 14 anos e de 60 anos ou mais e o "
            "grupo de 15 a 59 anos (Censo 2022, SIDRA 9514 / variável 93), × 100. Corte 60+ "
            "segue o Estatuto do Idoso, não o recorte IBGE clássico 15–64 / 65+."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 9514 / (0–14 + 60+) ÷ 15–59",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/9514",
            "url": "https://sidra.ibge.gov.br/tabela/9514",
            "api_url": url,
        },
        "limitations": [
            "DERIVADO de grupos etários oficiais; não é o índice de dependência publicado pelo IBGE (15–64 e 65+).",
            "Não usar como ranking de «carga» sobre o mercado de trabalho.",
        ],
    }
    wrote["dependency_ratio"] = _write_ibge_indicator(
        _base_fixture(
            indicator_id="dependency_ratio",
            spec=dep_spec,
            period=period,
            records=dep_records,
            api_url=url,
        )
    )
    return wrote


def _write_vital_rate(
    *,
    indicator_id: str,
    events: dict[str, dict[str, float]],
    population: dict[str, dict[str, float]],
    spec: dict[str, Any],
    api_url: str,
) -> dict[str, Any]:
    complete: dict[str, dict[str, float]] = {}
    for year, mapped in events.items():
        pop = population.get(year)
        if pop is None:
            continue
        rates: dict[str, float] = {}
        for code in UF_CODES:
            den = pop[code]
            if den <= 0:
                rates = {}
                break
            rate = round(1000.0 * mapped[code] / den, 2)
            if rate < 0 or rate > 80:
                raise RuntimeError(f"{indicator_id}: implausible rate for {code}@{year}: {rate}")
            rates[code] = rate
        if set(rates) == set(UF_CODES):
            complete[year] = rates
    if not complete:
        raise RuntimeError(f"{indicator_id}: no year with 27 UF events and matching 6579 population")
    estados = _estados()
    series = {
        year: [
            {
                "ibge_code": code,
                "uf": estados[code]["uf"],
                "name": estados[code]["name"],
                "value": mapped[code],
            }
            for code in sorted(UF_CODES)
        ]
        for year, mapped in sorted(complete.items())
    }
    period = max(complete, key=int)
    fixture = _base_fixture(
        indicator_id=indicator_id,
        spec=spec,
        period=period,
        records=series[period],
        api_url=api_url,
        series=series,
    )
    years = ", ".join(sorted(complete))
    fixture["definition"] = str(spec["definition"]).format(years=years, latest=period)
    return _write_ibge_indicator(fixture)


def fetch_vital_rates() -> dict[str, Any]:
    """Crude birth/death rates: Registro Civil ÷ população 6579 do mesmo ano × 1000."""
    pop = _population_series_map()
    birth_url = (
        "https://apisidra.ibge.gov.br/values/t/2609/n3/all/v/217/p/all"
        "/c232/0/c240/0/c2/0?formato=json"
    )
    death_url = (
        "https://apisidra.ibge.gov.br/values/t/2682/n3/all/v/223/p/all"
        "/c255/0/c1836/0/c2/0/c260/0?formato=json"
    )
    births = _sidra_year_uf_map(_fetch_sidra(birth_url, "sidra_2609_births_all.json"))
    deaths = _sidra_year_uf_map(_fetch_sidra(death_url, "sidra_2682_deaths_all.json"))
    birth_spec = {
        "name": "Nascidos vivos por mil habitantes",
        "short_name": "Natalidade bruta",
        "unit": "por mil hab",
        "status_label": "DERIVADO",
        "higher_is_worse": False,
        "kind": "derived",
        "group": "territorio",
        "group_label": "Território",
        "frequency": "annual",
        "dataset_id": "ibge.crude_birth_rate.{period}",
        "definition": (
            "Nascidos vivos registrados no ano (Registro Civil, SIDRA 2609 / variável 217, "
            "totais de ano de nascimento, idade da mãe e sexo) divididos pela população "
            "residente estimada IBGE 6579 do mesmo ano, × 1000. Série com 27 UFs: {years}. "
            "Mapa mostra o ano {latest}."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 2609/217 ÷ 6579 (mesmo ano)",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/2609",
            "url": "https://sidra.ibge.gov.br/tabela/2609",
        },
        "limitations": [
            "Taxa bruta (DERIVADO): não é taxa de fecundidade total nem padronizada por idade.",
            "Numerador é registro civil do ano; denominador é estimativa 6579 do mesmo ano.",
            "Não preenche ano se 6579 não publicar as 27 UFs naquele período.",
        ],
    }
    death_spec = {
        "name": "Óbitos registrados por mil habitantes",
        "short_name": "Mortalidade bruta",
        "unit": "por mil hab",
        "status_label": "DERIVADO",
        "higher_is_worse": True,
        "kind": "derived",
        "group": "territorio",
        "group_label": "Território",
        "frequency": "annual",
        "dataset_id": "ibge.crude_death_rate.{period}",
        "definition": (
            "Óbitos registrados no ano (Registro Civil, SIDRA 2682 / variável 223, totais de "
            "ano de ocorrência, natureza, sexo e idade) divididos pela população residente "
            "estimada IBGE 6579 do mesmo ano, × 1000. Série com 27 UFs: {years}. "
            "Mapa mostra o ano {latest}."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 2682/223 ÷ 6579 (mesmo ano)",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/2682",
            "url": "https://sidra.ibge.gov.br/tabela/2682",
        },
        "limitations": [
            "Taxa bruta (DERIVADO): UFs mais velhas tendem a mortalidade maior — não padroniza idade.",
            "Não é mortalidade infantil, esperança de vida nem causa específica (SIDRA 7362 está em revisão 2018).",
            "Numerador é registro civil; denominador é estimativa 6579 do mesmo ano.",
        ],
    }
    return {
        "crude_birth_rate": _write_vital_rate(
            indicator_id="crude_birth_rate",
            events=births,
            population=pop,
            spec=birth_spec,
            api_url=birth_url,
        ),
        "crude_death_rate": _write_vital_rate(
            indicator_id="crude_death_rate",
            events=deaths,
            population=pop,
            spec=death_spec,
            api_url=death_url,
        ),
    }


def fetch_employer_unit_birth_rate() -> dict[str, Any]:
    """IBGE birth rate = nascimentos ÷ unidades locais empregadoras ativas (mesma tabela 9925)."""
    url = (
        "https://apisidra.ibge.gov.br/values/t/9925/n3/all/v/13220/p/all"
        "/c12762/117897/c371/73119,73120?formato=json"
    )
    rows = _fetch_sidra(url, "sidra_9925_birth_rate.json")
    by_year: dict[str, dict[str, dict[str, float]]] = {}
    for row in rows[1:]:
        code = str(row.get("D1C") or "")
        year = str(row.get("D3C") or "")
        event = str(row.get("D5C") or "")
        val = _sidra_float(str(row.get("V") or ""))
        if code not in UF_CODES or not year.isdigit() or val is None:
            continue
        slot = by_year.setdefault(year, {"active": {}, "births": {}})
        if event == "73119":
            slot["active"][code] = val
        elif event == "73120":
            slot["births"][code] = val
    complete: dict[str, dict[str, float]] = {}
    for year, slot in by_year.items():
        active = slot["active"]
        births = slot["births"]
        if set(active) != set(UF_CODES) or set(births) != set(UF_CODES):
            continue
        if any(v <= 0 for v in active.values()) or any(v < 0 for v in births.values()):
            continue
        complete[year] = {
            code: round(100.0 * births[code] / active[code], 2) for code in UF_CODES
        }
        for code, rate in complete[year].items():
            if not 0 <= rate <= 100:
                raise RuntimeError(f"employer_unit_birth_rate: implausible {year}/{code}: {rate}")
    if not complete:
        raise RuntimeError("employer_unit_birth_rate: no SIDRA year with 27 UFs")
    estados = _estados()

    def records_from(mapped: dict[str, float]) -> list[dict[str, Any]]:
        out = []
        for code in sorted(UF_CODES):
            meta = estados[code]
            out.append(
                {
                    "ibge_code": code,
                    "uf": meta["uf"],
                    "name": meta["name"],
                    "value": mapped[code],
                }
            )
        return out

    series = {year: records_from(mapped) for year, mapped in sorted(complete.items())}
    period = max(complete, key=int)
    spec = {
        "name": "Taxa de nascimento de unidades locais empregadoras",
        "short_name": "Taxa de abertura",
        "unit": "%",
        "status_label": "DERIVADO",
        "higher_is_worse": False,
        "kind": "derived",
        "group": "economia",
        "group_label": "Economia / demografia",
        "frequency": "annual",
        "dataset_id": "ibge.employer_unit_birth_rate.{period}",
        "definition": (
            "Nascimentos de unidades locais empregadoras divididos pelas unidades locais "
            "empregadoras ativas da mesma UF e ano (SIDRA 9925 / var 13220, eventos 73120÷73119, "
            "CNAE Total). É a definição de taxa de nascimento usada pelo IBGE na divulgação, "
            "calculada aqui a partir das duas células oficiais — a tabela não publica o percentual pronto em N3."
        ),
        "source": {
            "organization": "IBGE",
            "dataset": "SIDRA 9925 / nascimento ÷ ativas (UL empregadoras)",
            "dataset_page": "https://sidra.ibge.gov.br/tabela/9925",
            "url": "https://sidra.ibge.gov.br/tabela/9925",
        },
        "limitations": [
            "DERIVADO: razão de duas contagens oficiais da mesma tabela.",
            "Exclusive MEI. UFs com mais estoque não têm necessariamente taxa maior.",
            "SIDRA publica «-» para morte de unidade local por UF — não há taxa de mortalidade no mapa.",
        ],
    }
    fixture = _base_fixture(
        indicator_id="employer_unit_birth_rate",
        spec=spec,
        period=period,
        records=series[period],
        api_url=url,
        series=series,
    )
    return _write_ibge_indicator(fixture)


def _sync_metric_catalog() -> dict[str, Any]:
    from territory_catalog import METRIC_DEFINITIONS

    path = fixtures_dir() / "territory" / "catalog.json"
    catalog = json.loads(path.read_text(encoding="utf-8"))
    catalog["metrics"] = METRIC_DEFINITIONS
    catalog["retrieved_at"] = utc_now()
    write_json(path, catalog)
    return {"catalog": str(path), "n_metrics": len(METRIC_DEFINITIONS)}


def materialize_offline() -> dict[str, Any]:
    return {"territory": export_territory_layers()}


def fetch_live() -> dict[str, Any]:
    out: dict[str, Any] = {
        "sanitation_adequate": fetch_sanitation_adequate(),
        "pib_per_capita": fetch_pib_per_capita(),
    }
    out.update(fetch_health_security_layers())
    out.update(fetch_census_age_shares())
    out.update(fetch_vital_rates())
    out["employer_unit_birth_rate"] = fetch_employer_unit_birth_rate()
    from dieese_cesta import fetch_dieese_basket

    out["dieese"] = fetch_dieese_basket()
    from derived_layers import materialize_derived

    out["derived"] = materialize_derived()
    from lenses import materialize_lenses

    out["lenses"] = materialize_lenses()
    out["catalog_metrics"] = _sync_metric_catalog()
    return out


def materialize_all() -> dict[str, Any]:
    out = materialize_offline()
    out["live"] = fetch_live()
    return out

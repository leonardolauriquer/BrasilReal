"""Derived UF layers from official fixtures already on disk.

Ratios and per-capita — never invent a missing cell. 27 UFs or refuse.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from common import fixtures_dir, utc_now, write_json
from social_layers import UF_CODES, _estados


def _checksum(records: list[dict[str, Any]]) -> str:
    canonical = json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _load(rel: str, indicator_id: str) -> dict[str, Any]:
    path = fixtures_dir() / rel / f"{indicator_id}_latest.json"
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _load_pop() -> dict[str, float]:
    path = fixtures_dir() / "ibge" / "population_uf_2025.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, float] = {}
    for row in payload["records"]:
        code = str(row["ibge_code"])
        if code in UF_CODES:
            out[code] = float(row["population"])
    if set(out) != set(UF_CODES):
        raise RuntimeError("derived: population must cover 27 UFs")
    return out


def _year_maps(payload: dict[str, Any]) -> dict[str, dict[str, float]]:
    series = payload.get("series") if isinstance(payload.get("series"), dict) else None
    out: dict[str, dict[str, float]] = {}
    if series:
        items = series.items()
    else:
        ref = str(payload.get("reference_period") or "")
        items = [(ref, payload.get("records") or [])] if ref else []
    for year, rows in items:
        mapped: dict[str, float] = {}
        for row in rows:
            code = str(row.get("ibge_code") or "")
            val = row.get("value")
            if code in UF_CODES and isinstance(val, (int, float)):
                mapped[code] = float(val)
        if set(mapped) == set(UF_CODES):
            out[str(year)] = mapped
    return out


def _records(mapped: dict[str, float], estados: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
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


def _write(
    *,
    rel: str,
    indicator_id: str,
    name: str,
    short_name: str,
    unit: str,
    definition: str,
    limitations: list[str],
    source: dict[str, str],
    records: list[dict[str, Any]],
    period: str,
    group: str,
    group_label: str,
    higher_is_worse: bool = False,
    series: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    periods = sorted(series) if series else [period]
    fixture: dict[str, Any] = {
        "indicator_id": indicator_id,
        "dataset_id": f"brasilreal.{indicator_id}.{period}",
        "title": f"{name} — UFs {period}",
        "short_name": short_name,
        "name": name,
        "status_label": "DERIVADO",
        "evidence_grade": "B",
        "unit": unit,
        "higher_is_worse": higher_is_worse,
        "kind": "derived",
        "group": group,
        "group_label": group_label,
        "frequency": "annual",
        "reference_period": period,
        "reference_date": period,
        "release_date": None,
        "retrieved_at": utc_now(),
        "available_periods": periods,
        "definition": definition,
        "source": source,
        "limitations": limitations,
        "checksum_sha256": _checksum(records),
        "records": records,
    }
    if series:
        fixture["series"] = series
    out_dir = fixtures_dir() / rel
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / f"{indicator_id}_{period}.json", fixture)
    write_json(out_dir / f"{indicator_id}_latest.json", fixture)
    return {"indicator_id": indicator_id, "period": period, "n_ufs": len(records)}


def materialize_derived() -> dict[str, Any]:
    estados = _estados()
    pop = _load_pop()
    wrote: dict[str, Any] = {}

    rcl = _load("siconfi/indicators", "rcl_rreo")
    trib = _load("siconfi/indicators", "receita_tributaria_rreo")
    dcl = _load("siconfi/indicators", "dcl_rreo")
    rcl_years = _year_maps(rcl)
    trib_years = _year_maps(trib)
    dcl_years = _year_maps(dcl)
    rcl_latest = str(rcl.get("reference_period") or "")
    if rcl_latest not in rcl_years:
        raise RuntimeError("derived: RCL latest year missing 27 UFs")

    pc = {code: rcl_years[rcl_latest][code] / pop[code] for code in UF_CODES}
    if any(v <= 0 for v in pc.values()):
        raise RuntimeError("derived: non-positive RCL/hab")
    wrote["rcl_pc"] = _write(
        rel="siconfi/indicators",
        indicator_id="rcl_pc",
        name="Receita corrente líquida por habitante",
        short_name="RCL / hab",
        unit="BRL/hab",
        definition=(
            f"RCL do RREO {rcl_latest} (Anexo 14, até o 6º bimestre) dividida pela "
            "população residente estimada IBGE 2025. Razão local; o Tesouro não publica RCL/hab."
        ),
        limitations=[
            "Denominador é a estimativa de população 2025, não a população do SICONFI.",
            "Nominal; não deflacionado. Não usar como renda.",
            "Só o exercício em que RCL e população 2025 coincidem no recorte latest.",
        ],
        source={
            "organization": "Brasil Real",
            "dataset": "RCL RREO ÷ população IBGE 2025",
            "url": "https://apidatalake.tesouro.gov.br/docs/siconfi/",
        },
        records=_records(pc, estados),
        period=rcl_latest,
        group="fiscal",
        group_label="Fiscal",
    )

    share_series: dict[str, list[dict[str, Any]]] = {}
    for year in sorted(set(rcl_years) & set(trib_years)):
        mapped = {}
        for code in UF_CODES:
            den = rcl_years[year][code]
            if den == 0:
                raise RuntimeError(f"derived: RCL zero in {year} {code}")
            mapped[code] = round(100.0 * trib_years[year][code] / den, 2)
        share_series[year] = _records(mapped, estados)
    share_latest = max(share_series)
    wrote["trib_share_rcl"] = _write(
        rel="siconfi/indicators",
        indicator_id="trib_share_rcl",
        name="Receita tributária como % da RCL",
        short_name="Tributária / RCL",
        unit="% da RCL",
        definition=(
            "Receita tributária realizada (RREO Anexo 01) dividida pela RCL (Anexo 14), "
            "mesmo exercício, 6º bimestre. Pode ultrapassar 100 se as contas não forem o mesmo agregado."
        ),
        limitations=[
            "Não é autonomia fiscal da LRF nem qualidade da gestão.",
            "Numerador e denominador vêm de anexos diferentes do mesmo RREO.",
        ],
        source={
            "organization": "Brasil Real",
            "dataset": "Receita tributária ÷ RCL (RREO mesmo ano)",
            "url": "https://apidatalake.tesouro.gov.br/docs/siconfi/",
        },
        records=share_series[share_latest],
        period=share_latest,
        group="fiscal",
        group_label="Fiscal",
        series=share_series,
    )

    debt_series: dict[str, list[dict[str, Any]]] = {}
    for year in sorted(set(rcl_years) & set(dcl_years)):
        mapped = {}
        for code in UF_CODES:
            den = rcl_years[year][code]
            if den == 0:
                raise RuntimeError(f"derived: RCL zero in {year} {code}")
            mapped[code] = round(dcl_years[year][code] / den, 4)
        debt_series[year] = _records(mapped, estados)
    debt_latest = max(debt_series)
    wrote["dcl_rcl"] = _write(
        rel="siconfi/indicators",
        indicator_id="dcl_rcl",
        name="Dívida consolidada líquida / RCL",
        short_name="DCL / RCL",
        unit="DCL/RCL",
        higher_is_worse=True,
        definition=(
            "DCL (RREO Anexo 06) dividida pela RCL (Anexo 14), mesmo exercício, 6º bimestre. "
            "Razão pode ser negativa se a DCL for credora."
        ),
        limitations=[
            "Não é o limite da LRF aplicado automaticamente. Superávit de DCL entra negativo.",
            "Nominal. Anexos diferentes do mesmo RREO.",
        ],
        source={
            "organization": "Brasil Real",
            "dataset": "DCL ÷ RCL (RREO mesmo ano)",
            "url": "https://apidatalake.tesouro.gov.br/docs/siconfi/",
        },
        records=debt_series[debt_latest],
        period=debt_latest,
        group="fiscal",
        group_label="Fiscal",
        series=debt_series,
    )

    export_path = fixtures_dir() / "comex" / "indicators" / "export_fob_latest.json"
    if export_path.exists():
        exp = json.loads(export_path.read_text(encoding="utf-8"))
        exp_map = _year_maps(exp)
        latest = str(exp.get("reference_period") or "")
        if latest not in exp_map:
            raise RuntimeError("derived: export_fob latest missing 27 UFs")
        pc_exp = {code: exp_map[latest][code] / pop[code] for code in UF_CODES}
        wrote["export_fob_pc"] = _write(
            rel="comex/indicators",
            indicator_id="export_fob_pc",
            name="Exportação FOB por habitante",
            short_name="Export. / hab",
            unit="USD/hab",
            definition=(
                f"Valor FOB total das exportações da UF ({latest}, Comex Stat / MDIC) "
                "dividido pela população IBGE 2025. O MDIC não publica FOB/hab."
            ),
            limitations=[
                "Denominador população 2025 mesmo se o FOB for de outro ano civil.",
                "Inclui a pauta inteira da UF, não um capítulo SH. Linhas «Não Declarada» não pintam UF.",
                "Dólar FOB nominal; não é volume nem preço interno.",
            ],
            source={
                "organization": "Brasil Real",
                "dataset": "Comex Stat FOB total ÷ população IBGE 2025",
                "url": "https://api-comexstat.mdic.gov.br/docs",
            },
            records=_records(pc_exp, estados),
            period=latest,
            group="agro",
            group_label="Agro / comércio exterior",
        )
    else:
        wrote["export_fob_pc"] = {"skipped": "missing export_fob_latest.json"}

    return wrote

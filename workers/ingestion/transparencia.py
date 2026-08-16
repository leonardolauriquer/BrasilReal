"""CGU Portal da Transparência — transferências da União por UF.

Official monthly CSVs (no API token, no person-level microdata).
UF in the file is the favoured ente's federation unit — not where money was spent.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import unicodedata
import urllib.error
import zipfile
from datetime import datetime, timezone
from typing import Any

from common import fetch_bytes, fixtures_dir, raw_dir, utc_now, write_json
from social_layers import UF_CODES, _estados

DOWNLOAD = "https://portaldatransparencia.gov.br/download-de-dados/transferencias/{ym}"
DICT_URL = "https://portaldatransparencia.gov.br/download-de-dados/transferencias"
SOURCE_PAGE = "https://portaldatransparencia.gov.br/api-de-dados"


def _fold(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in nfkd if not unicodedata.combining(c)).casefold().strip()


def _parse_brl(raw: str) -> float:
    s = (raw or "").strip().replace(" ", "")
    if not s:
        raise ValueError("empty BRL")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    return float(s)


def _col(header: list[str], *needles: str) -> int:
    folded = [_fold(h) for h in header]
    for needle in needles:
        want = _fold(needle)
        for i, name in enumerate(folded):
            if name == want:
                return i
    for needle in needles:
        want = _fold(needle)
        for i, name in enumerate(folded):
            if want and want in name.split():
                return i
    raise RuntimeError(f"transparencia: missing column {needles} in {header[:12]}")


def _is_constitutional(tipo: str) -> bool:
    return _fold(tipo).startswith("constitucionais")


def _year_has_december(year: int) -> bool:
    """Complete calendar year iff the December zip is published (GET)."""
    try:
        raw = _load_month_zip(f"{year}12")
    except urllib.error.HTTPError as exc:
        if exc.code in {403, 404}:
            return False
        raise
    return raw[:2] == b"PK"


def complete_calendar_years(*, min_year: int = 2024) -> list[int]:
    now = datetime.now(timezone.utc).year
    found: list[int] = []
    for year in range(min_year, now + 1):
        if _year_has_december(year):
            found.append(year)
    if not found:
        raise RuntimeError("transparencia: no complete calendar year of CGU zips")
    return found


def _load_month_zip(ym: str) -> bytes:
    dest = raw_dir() / "cgu" / "transferencias" / f"{ym}.zip"
    if dest.exists() and dest.stat().st_size > 1_000:
        data = dest.read_bytes()
        if data[:2] == b"PK":
            return data
    raw = fetch_bytes(DOWNLOAD.format(ym=ym), timeout=120, retries=4)
    if raw[:2] != b"PK":
        raise RuntimeError(f"transparencia: {ym} response is not a zip")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(raw)
    return raw


def _sum_month(raw_zip: bytes) -> tuple[dict[str, float], dict[str, float]]:
    total: dict[str, float] = {sigla: 0.0 for sigla in UF_CODES.values()}
    const: dict[str, float] = {sigla: 0.0 for sigla in UF_CODES.values()}
    with zipfile.ZipFile(io.BytesIO(raw_zip)) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not names:
            raise RuntimeError("transparencia: zip without CSV")
        with zf.open(names[0]) as blob:
            wrapper = io.TextIOWrapper(blob, encoding="latin-1", newline="")
            reader = csv.reader(wrapper, delimiter=";")
            header = next(reader)
            i_uf = _col(header, "UF")
            i_tipo = _col(header, "TIPO TRANSFERENCIA", "TIPO TRANSFERÊNCIA")
            i_val = _col(header, "VALOR TRANSFERIDO")
            allowed = set(total)
            for row in reader:
                if len(row) <= max(i_uf, i_tipo, i_val):
                    continue
                uf = (row[i_uf] or "").strip().upper()
                if uf not in allowed:
                    continue
                try:
                    value = _parse_brl(row[i_val])
                except ValueError:
                    continue
                if not (value >= 0) or value != value:
                    continue
                total[uf] += value
                if _is_constitutional(row[i_tipo]):
                    const[uf] += value
    return total, const


def _checksum(records: list[dict[str, Any]]) -> str:
    canonical = json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _records(mapped: dict[str, float], estados: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    out = []
    for code in sorted(UF_CODES):
        meta = estados[code]
        sigla = UF_CODES[code]
        out.append(
            {
                "ibge_code": code,
                "uf": sigla,
                "name": meta["name"],
                "value": round(mapped[sigla], 2),
            }
        )
    return out


LIMITS_TOTAL = [
    "UF = unidade da federação do favorecido no arquivo da CGU — não é o local onde o recurso foi gasto.",
    "Inclui estados, DF, municípios e outros favorecidos cuja UF está preenchida. Não confundir com a linha de transferências do RREO estadual (SICONFI).",
    "Tipos oficiais do arquivo: Constitucionais e Royalties + Legais, Voluntárias e Específicas.",
    "Nominal; não deflacionado. Exercício = soma dos 12 CSVs mensais oficiais.",
    "Não há NIS, CPF, nome de pessoa nem microdado de beneficiário neste recorte.",
]

LIMITS_CONST = [
    "Recorte do tipo «Constitucionais e Royalties» no CSV da CGU — FPM/FPE/FUNDEB/royalties etc., conforme o dicionário da CGU.",
    "UF do favorecido, não território de impacto. Não é a RCL nem a linha SICONFI de transferências correntes.",
    "Nominal; soma dos 12 meses. Sem microdado pessoal.",
]


def _write_indicator(
    *,
    indicator_id: str,
    name: str,
    short_name: str,
    definition: str,
    limitations: list[str],
    series: dict[str, list[dict[str, Any]]],
    latest: str,
) -> dict[str, Any]:
    records = series[latest]
    brazil_total = round(sum(float(r["value"]) for r in records), 2)
    fixture = {
        "indicator_id": indicator_id,
        "dataset_id": f"cgu.{indicator_id}.{latest}",
        "title": f"{name} — UFs {latest}",
        "short_name": short_name,
        "name": name,
        "status_label": "OBSERVADO",
        "evidence_grade": "A",
        "unit": "BRL",
        "higher_is_worse": False,
        "kind": "observed_estimate",
        "group": "uniao",
        "group_label": "União (CGU)",
        "frequency": "annual",
        "reference_period": latest,
        "reference_date": f"{latest}-12-31",
        "release_date": None,
        "retrieved_at": utc_now(),
        "available_periods": sorted(series),
        "brazil_total": brazil_total,
        "definition": definition,
        "source": {
            "organization": "CGU — Portal da Transparência",
            "dataset": "Download de dados / Transferencias (CSV mensal)",
            "dataset_page": DICT_URL,
            "url": DOWNLOAD.format(ym=f"{latest}12"),
            "method_notes": (
                "ZIP oficial mensal, CSV latin-1 separado por ponto e vírgula. "
                "Soma VALOR TRANSFERIDO por coluna UF. Sem chave de API."
            ),
        },
        "limitations": limitations,
        "checksum_sha256": _checksum(records),
        "records": records,
        "series": series,
    }
    out_dir = fixtures_dir() / "cgu" / "indicators"
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / f"{indicator_id}_{latest}.json", fixture)
    write_json(out_dir / f"{indicator_id}_latest.json", fixture)
    return {
        "indicator_id": indicator_id,
        "period": latest,
        "n_ufs": len(records),
        "brazil_total": brazil_total,
    }


def fetch_bundle(*, min_year: int = 2024) -> dict[str, Any]:
    estados = _estados()
    years = complete_calendar_years(min_year=min_year)
    totals_year: dict[str, dict[str, float]] = {}
    const_year: dict[str, dict[str, float]] = {}
    months_ok: dict[str, list[str]] = {}

    for year in years:
        acc_t = {sigla: 0.0 for sigla in UF_CODES.values()}
        acc_c = {sigla: 0.0 for sigla in UF_CODES.values()}
        seen: list[str] = []
        for month in range(1, 13):
            ym = f"{year}{month:02d}"
            month_t, month_c = _sum_month(_load_month_zip(ym))
            for sigla in UF_CODES.values():
                acc_t[sigla] += month_t[sigla]
                acc_c[sigla] += month_c[sigla]
            seen.append(ym)
        if len(seen) != 12:
            raise RuntimeError(f"transparencia: {year} incomplete {seen}")
        key = str(year)
        totals_year[key] = acc_t
        const_year[key] = acc_c
        months_ok[key] = seen
        missing_t = [s for s, v in acc_t.items() if v <= 0]
        missing_c = [s for s, v in acc_c.items() if v <= 0]
        if missing_t:
            raise RuntimeError(f"transparencia: total missing/zero {year} {missing_t}")
        if missing_c:
            raise RuntimeError(f"transparencia: constitutional missing/zero {year} {missing_c}")

    latest = max(totals_year)
    series_t = {y: _records(m, estados) for y, m in totals_year.items()}
    series_c = {y: _records(m, estados) for y, m in const_year.items()}

    return {
        "years": years,
        "months": months_ok,
        "union_transfers": _write_indicator(
            indicator_id="union_transfers",
            name="Transferências da União ao favorecido na UF",
            short_name="Transf. União (CGU)",
            definition=(
                "Soma anual do campo VALOR TRANSFERIDO nos CSVs mensais de Transferências do "
                "Portal da Transparência (CGU), agrupada pela UF do favorecido. "
                "Recursos que a União registrou como transferência àquele ente/favorecido — "
                "não é execução de despesa no território da UF."
            ),
            limitations=LIMITS_TOTAL,
            series=series_t,
            latest=latest,
        ),
        "union_transfers_const": _write_indicator(
            indicator_id="union_transfers_const",
            name="Transferências constitucionais e royalties (CGU)",
            short_name="Transf. constitucionais",
            definition=(
                "Mesma base CGU, apenas linhas cujo tipo é «Constitucionais e Royalties» "
                f"(FPE/FPM/FUNDEB/royalties etc. no recorte do CSV). Exercício {latest}."
            ),
            limitations=LIMITS_CONST,
            series=series_c,
            latest=latest,
        ),
        "source_page": SOURCE_PAGE,
    }

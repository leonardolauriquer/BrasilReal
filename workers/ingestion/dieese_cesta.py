"""DIEESE/Conab basic-food basket — 27 state capitals, never the interior of the UF."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
import urllib.error
from datetime import date
from io import BytesIO
from typing import Any

from common import fetch_bytes, fixtures_dir, snapshot_raw, utc_now, write_json
from social_layers import UF_CODES, _estados

# Capital of the UF (official DIEESE PNCBA cities). Macaé is extra and dropped.
CAPITAL_TO_CODE: dict[str, str] = {
    "aracaju": "28",
    "belem": "15",
    "belo horizonte": "31",
    "boa vista": "14",
    "brasilia": "53",
    "campo grande": "50",
    "cuiaba": "51",
    "curitiba": "41",
    "florianopolis": "42",
    "fortaleza": "23",
    "goiania": "52",
    "joao pessoa": "25",
    "macapa": "16",
    "maceio": "27",
    "manaus": "13",
    "natal": "24",
    "palmas": "17",
    "porto alegre": "43",
    "porto velho": "11",
    "recife": "26",
    "rio branco": "12",
    "rio de janeiro": "33",
    "salvador": "29",
    "sao luis": "21",
    "sao paulo": "35",
    "teresina": "22",
    "vitoria": "32",
}

BULLETIN_URL = (
    "https://www.dieese.org.br/analisecestabasica/{year}/{year}{month:02d}cestabasica.pdf"
)
_CAPITAL_LINE = re.compile(
    r"(?P<name>[A-ZÁÉÍÓÚÂÊÔÃÕÇa-záéíóúâêôãõçü .'’-]+(?:\s+\(\d+\))?)\s+"
    r"(?P<value>\d{1,3},\d{2})\s+"
    r"(?P<mom>[-+]?\d+,\d+)\s+"
    r"(?P<share>\d{1,2},\d{2})\b"
)


def _fold(text: str) -> str:
    return (
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
        .strip()
    )


def _parse_br_float(raw: str) -> float:
    return float(raw.replace(".", "").replace(",", "."))


def parse_tabela1(text: str) -> dict[str, dict[str, float]]:
    start = _fold(text).find("tabela 1")
    chunk = text[start:] if start >= 0 else text
    end_m = re.search(r"Fonte:\s*Conab/DIEESE", chunk, re.I)
    if end_m:
        chunk = chunk[: end_m.start()]
    found: dict[str, dict[str, float]] = {}
    for match in _CAPITAL_LINE.finditer(chunk):
        key = _fold(re.sub(r"\s*\(\d+\)\s*", " ", match.group("name")))
        code = CAPITAL_TO_CODE.get(key)
        if not code:
            continue
        found[code] = {
            "value": _parse_br_float(match.group("value")),
            "share": _parse_br_float(match.group("share")),
        }
    if set(found) != set(UF_CODES):
        missing = sorted(set(UF_CODES) - set(found))
        extra = sorted(set(found) - set(UF_CODES))
        raise RuntimeError(f"dieese cesta: expected 27 capitals, missing={missing} extra={extra}")
    return found


def _extract_pdf_text(raw: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("dieese cesta: pip install pypdf to refresh this fixture") from exc
    reader = PdfReader(BytesIO(raw))
    parts: list[str] = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts)


def _candidate_months(*, n: int = 8) -> list[tuple[int, int]]:
    today = date.today()
    year, month = today.year, today.month
    out: list[tuple[int, int]] = []
    for _ in range(n):
        out.append((year, month))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return out


def _checksum(records: list[dict[str, Any]]) -> str:
    canonical = json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _write_layer(
    *,
    indicator_id: str,
    name: str,
    short_name: str,
    unit: str,
    higher_is_worse: bool,
    period: str,
    records: list[dict[str, Any]],
    pdf_url: str,
    definition: str,
    limitations: list[str],
    series: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    fixture = {
        "indicator_id": indicator_id,
        "dataset_id": f"dieese.{indicator_id}.{period}",
        "title": f"{name} — capitais {period}",
        "short_name": short_name,
        "name": name,
        "status_label": "OBSERVADO",
        "evidence_grade": "A",
        "unit": unit,
        "higher_is_worse": higher_is_worse,
        "kind": "observed_estimate",
        "group": "custo",
        "group_label": "Custo na capital",
        "frequency": "monthly",
        "reference_period": period,
        "reference_date": period,
        "release_date": None,
        "retrieved_at": utc_now(),
        "definition": definition,
        "source": {
            "organization": "DIEESE / Conab",
            "dataset": "Pesquisa Nacional da Cesta Básica de Alimentos — Tabela 1",
            "dataset_page": "https://www.dieese.org.br/analisecestabasica/",
            "url": pdf_url,
        },
        "limitations": limitations,
        "checksum_sha256": _checksum(records),
        "records": records,
    }
    if series:
        fixture["series"] = series
        fixture["available_periods"] = sorted(series)
    out_dir = fixtures_dir() / "dieese" / "indicators"
    out_dir.mkdir(parents=True, exist_ok=True)
    period_token = period.replace("-", "")
    write_json(out_dir / f"{indicator_id}_{period_token}.json", fixture)
    write_json(out_dir / f"{indicator_id}_latest.json", fixture)
    return {
        "indicator_id": indicator_id,
        "period": period,
        "n_ufs": len(records),
        "checksum": fixture["checksum_sha256"],
    }


def fetch_dieese_basket() -> dict[str, Any]:
    estados = _estados()
    series_value: dict[str, list[dict[str, Any]]] = {}
    series_share: dict[str, list[dict[str, Any]]] = {}
    latest_url = ""
    latest_period = ""
    for year, month in _candidate_months():
        url = BULLETIN_URL.format(year=year, month=month)
        try:
            raw = fetch_bytes(url, timeout=90)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                continue
            raise
        if raw[:4] != b"%PDF":
            continue
        snapshot_raw(
            "dieese",
            f"cestabasica_{year}{month:02d}.pdf",
            raw,
            {"source_url": url, "connector": "dieese.pncba.pdf"},
        )
        parsed = parse_tabela1(_extract_pdf_text(raw))
        period = f"{year:04d}-{month:02d}"
        value_rows = []
        share_rows = []
        for code in sorted(UF_CODES):
            meta = estados[code]
            row = parsed[code]
            if not (50 < row["value"] < 5000):
                raise RuntimeError(f"dieese cesta: implausible value {code}: {row['value']}")
            if not (0 < row["share"] <= 100):
                raise RuntimeError(f"dieese cesta: implausible SM share {code}: {row['share']}")
            value_rows.append(
                {
                    "ibge_code": code,
                    "uf": meta["uf"],
                    "name": meta["name"],
                    "value": row["value"],
                }
            )
            share_rows.append(
                {
                    "ibge_code": code,
                    "uf": meta["uf"],
                    "name": meta["name"],
                    "value": row["share"],
                }
            )
        series_value[period] = value_rows
        series_share[period] = share_rows
        if not latest_period or period > latest_period:
            latest_period = period
            latest_url = url
    if not latest_period:
        raise RuntimeError("dieese cesta: no bulletin PDF with 27 capitals")
    limitations_value = [
        "Preço da cesta na CAPITAL — pintar a UF inteira com esse número é um recorte de cidade, não do interior.",
        "A composição da cesta do Norte/Nordeste é diferente do Centro-Sul (DIEESE/Conab).",
        "Não é IPC/IPCA nem POF; não inclui aluguel, transporte nem energia.",
    ]
    limitations_share = [
        "Percentual do salário mínimo LÍQUIDO (desconto de 7,5% da Previdência) na CAPITAL.",
        "Não é poder de compra do interior da UF nem da mediana de renda.",
        *limitations_value[:2],
    ]
    wrote = {
        "basket_capital": _write_layer(
            indicator_id="basket_capital",
            name="Cesta básica na capital (DIEESE/Conab)",
            short_name="Cesta na capital",
            unit="BRL/mês",
            higher_is_worse=True,
            period=latest_period,
            records=series_value[latest_period],
            pdf_url=latest_url,
            definition=(
                "Custo mensal da cesta básica de alimentos na capital da UF, Pesquisa Nacional "
                "da Cesta Básica de Alimentos (DIEESE em parceria com a Conab, Tabela 1 do boletim). "
                "Valor da capital, não média estadual."
            ),
            limitations=limitations_value,
            series=series_value,
        ),
        "basket_share_sm": _write_layer(
            indicator_id="basket_share_sm",
            name="Cesta básica da capital em % do salário mínimo líquido",
            short_name="Cesta / SM líquido (capital)",
            unit="%",
            higher_is_worse=True,
            period=latest_period,
            records=series_share[latest_period],
            pdf_url=latest_url,
            definition=(
                "Participação do custo da cesta básica da capital no salário mínimo líquido "
                "(DIEESE/Conab, Tabela 1). Mínimo líquido = piso nacional menos 7,5% de Previdência."
            ),
            limitations=limitations_share,
            series=series_share,
        ),
    }
    return wrote

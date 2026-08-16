from __future__ import annotations

import csv
import io
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "workers" / "ingestion"))

import transparencia as t  # noqa: E402


def _zip_csv(rows: list[list[str]]) -> bytes:
    buf = io.BytesIO()
    text = io.StringIO()
    writer = csv.writer(text, delimiter=";")
    writer.writerows(rows)
    payload = text.getvalue().encode("latin-1")
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("202412_Transferencias.csv", payload)
    return buf.getvalue()


def test_parse_brl_thousands_and_decimal():
    assert t._parse_brl("1.234.567,89") == 1234567.89
    assert t._parse_brl("10,50") == 10.5
    assert t._parse_brl("1000") == 1000.0


def test_constitutional_type_fold():
    assert t._is_constitutional("Constitucionais e Royalties") is True
    assert t._is_constitutional("Legais, Voluntárias e Específicas") is False


def test_sum_month_aggregates_by_uf_without_inventing():
    raw = _zip_csv(
        [
            ["ANO", "MÊS", "TIPO TRANSFERÊNCIA", "UF", "VALOR TRANSFERIDO"],
            ["2024", "12", "Constitucionais e Royalties", "SP", "1.000,50"],
            ["2024", "12", "Legais, Voluntárias e Específicas", "SP", "500,00"],
            ["2024", "12", "Constitucionais e Royalties", "RR", "10,00"],
            ["2024", "12", "Constitucionais e Royalties", "XX", "99,00"],
        ]
    )
    total, const = t._sum_month(raw)
    assert abs(total["SP"] - 1500.50) < 1e-9
    assert abs(const["SP"] - 1000.50) < 1e-9
    assert total["RR"] == 10.0
    assert const["RR"] == 10.0
    assert total["AC"] == 0.0
    assert "XX" not in total

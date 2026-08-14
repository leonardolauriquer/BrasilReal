"""Territorial attributes: indigenous, quilombola, biome, area (official IBGE only)."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from common import fetch_bytes, fetch_json, fixtures_dir, snapshot_raw, utc_now, write_json
from territory_catalog import METRIC_DEFINITIONS, TERRITORY_SPECS

BIOME_CSV_URL = (
    "https://geoftp.ibge.gov.br/informacoes_ambientais/estudos_ambientais/"
    "biomas/documentos/Bioma_Predominante_por_Municipio_2024.csv"
)
COASTAL_XLS_URL = (
    "https://geoftp.ibge.gov.br/informacoes_ambientais/estudos_ambientais/"
    "biomas/documentos/Lista_Municipio_CosteiroMarinho_250mil.xls"
)

# Censo 2022 — indígenas
INDIGENOUS_AGG = 9718
INDIGENOUS_COUNT_VAR = 350
INDIGENOUS_SHARE_VAR = 4727
INDIGENOUS_CLASS = "1714[60024]|2661[32776]"

# Censo 2022 — quilombolas (moradores quilombolas)
QUILOMBOLA_AGG = 9727
QUILOMBOLA_VAR = 7097

# Área territorial
AREA_AGG = 1301
AREA_VAR = 615
AREA_PERIOD = "2010"


def _parse_number(raw: str) -> float | None:
    text = str(raw).strip().replace(",", ".")
    if text in {"", "...", "-", "X", "x", "None"}:
        return None
    # IBGE sometimes uses thousand separators as dots
    if text.count(".") > 1:
        text = text.replace(".", "")
    try:
        return float(text)
    except ValueError:
        return None


def _series_map(payload: list[dict[str, Any]], period: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for block in payload:
        for resultado in block.get("resultados", []):
            for item in resultado.get("series", []):
                loc = item["localidade"]
                code = str(loc["id"])
                value = _parse_number(str(item["serie"].get(period, "")))
                if value is None:
                    continue
                out[code] = {
                    "ibge_code": code,
                    "name": loc.get("nome"),
                    "value": value,
                }
    return out


def _fetch_aggregate(
    aggregate: int,
    period: str,
    variable: int,
    localities: str,
    classificacao: str | None = None,
) -> list[dict[str, Any]]:
    url = (
        f"https://servicodados.ibge.gov.br/api/v3/agregados/{aggregate}"
        f"/periodos/{period}/variaveis/{variable}?localidades={localities}"
    )
    if classificacao:
        url += f"&classificacao={classificacao}"
    raw = fetch_bytes(url, timeout=180)
    snapshot_raw(
        "ibge",
        f"agg_{aggregate}_v{variable}_{period}_{localities[:40].replace('[','').replace(']','')}.json",
        raw,
        {"source_url": url, "connector": "territory.aggregate"},
    )
    return json.loads(raw.decode("utf-8"))


def fetch_indigenous() -> dict[str, Any]:
    period = "2022"
    uf_count = _series_map(
        _fetch_aggregate(
            INDIGENOUS_AGG, period, INDIGENOUS_COUNT_VAR, "N3[all]", INDIGENOUS_CLASS
        ),
        period,
    )
    uf_share = _series_map(
        _fetch_aggregate(
            INDIGENOUS_AGG, period, INDIGENOUS_SHARE_VAR, "N3[all]", INDIGENOUS_CLASS
        ),
        period,
    )
    mun_count = _series_map(
        _fetch_aggregate(
            INDIGENOUS_AGG, period, INDIGENOUS_COUNT_VAR, "N6[all]", INDIGENOUS_CLASS
        ),
        period,
    )
    mun_share = _series_map(
        _fetch_aggregate(
            INDIGENOUS_AGG, period, INDIGENOUS_SHARE_VAR, "N6[all]", INDIGENOUS_CLASS
        ),
        period,
    )

    by_uf: dict[str, dict[str, Any]] = {}
    for code, row in uf_count.items():
        by_uf[code] = {
            "ibge_code": code,
            "name": row["name"],
            "indigenous_population": int(row["value"]),
            "indigenous_share": uf_share.get(code, {}).get("value"),
        }

    by_mun: dict[str, dict[str, Any]] = {}
    for code, row in mun_count.items():
        by_mun[code] = {
            "ibge_code": code,
            "name": row["name"],
            "uf_code": code[:2],
            "indigenous_population": int(row["value"]),
            "indigenous_share": mun_share.get(code, {}).get("value"),
        }

    payload = {
        "retrieved_at": utc_now(),
        "reference_period": period,
        "status_label": "OBSERVADO",
        "source": TERRITORY_SPECS["indigenous_population"]["source"],
        "uf_count": len(by_uf),
        "mun_count": len(by_mun),
        "by_uf": by_uf,
        "by_mun": by_mun,
    }
    out = fixtures_dir() / "territory" / "indigenous_2022.json"
    write_json(out, payload)
    return {"wrote": str(out), "uf": len(by_uf), "mun": len(by_mun)}


def fetch_quilombola() -> dict[str, Any]:
    period = "2022"
    uf_map = _series_map(
        _fetch_aggregate(QUILOMBOLA_AGG, period, QUILOMBOLA_VAR, "N3[all]"),
        period,
    )
    mun_map = _series_map(
        _fetch_aggregate(QUILOMBOLA_AGG, period, QUILOMBOLA_VAR, "N6[all]"),
        period,
    )
    by_uf = {
        code: {
            "ibge_code": code,
            "name": row["name"],
            "quilombola_residents": int(row["value"]),
        }
        for code, row in uf_map.items()
    }
    by_mun = {
        code: {
            "ibge_code": code,
            "name": row["name"],
            "uf_code": code[:2],
            "quilombola_residents": int(row["value"]),
        }
        for code, row in mun_map.items()
    }
    payload = {
        "retrieved_at": utc_now(),
        "reference_period": period,
        "status_label": "OBSERVADO",
        "source": TERRITORY_SPECS["quilombola_residents"]["source"],
        "uf_count": len(by_uf),
        "mun_count": len(by_mun),
        "by_uf": by_uf,
        "by_mun": by_mun,
    }
    out = fixtures_dir() / "territory" / "quilombola_2022.json"
    write_json(out, payload)
    return {"wrote": str(out), "uf": len(by_uf), "mun": len(by_mun)}


def fetch_area() -> dict[str, Any]:
    period = AREA_PERIOD
    uf_map = _series_map(
        _fetch_aggregate(AREA_AGG, period, AREA_VAR, "N3[all]"),
        period,
    )
    mun_map = _series_map(
        _fetch_aggregate(AREA_AGG, period, AREA_VAR, "N6[all]"),
        period,
    )
    by_uf = {
        code: {"ibge_code": code, "name": row["name"], "area_km2": row["value"]}
        for code, row in uf_map.items()
    }
    by_mun = {
        code: {
            "ibge_code": code,
            "name": row["name"],
            "uf_code": code[:2],
            "area_km2": row["value"],
        }
        for code, row in mun_map.items()
    }
    payload = {
        "retrieved_at": utc_now(),
        "reference_period": period,
        "status_label": "OBSERVADO",
        "source": TERRITORY_SPECS["area_km2"]["source"],
        "uf_count": len(by_uf),
        "mun_count": len(by_mun),
        "by_uf": by_uf,
        "by_mun": by_mun,
    }
    out = fixtures_dir() / "territory" / "area_2010.json"
    write_json(out, payload)
    return {"wrote": str(out), "uf": len(by_uf), "mun": len(by_mun)}


def _decode_csv(raw: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", errors="replace")


def fetch_biomes() -> dict[str, Any]:
    raw = fetch_bytes(BIOME_CSV_URL, timeout=120)
    snapshot_raw(
        "ibge",
        "Bioma_Predominante_por_Municipio_2024.csv",
        raw,
        {"source_url": BIOME_CSV_URL, "connector": "territory.biome"},
    )
    text = _decode_csv(raw)
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    if not reader.fieldnames:
        reader = csv.DictReader(io.StringIO(text), delimiter=",")

    def pick(row: dict[str, str], *candidates: str) -> str:
        keys = {k.lower().strip(): k for k in row}
        for cand in candidates:
            for key_l, key in keys.items():
                if cand in key_l.replace(" ", ""):
                    return (row.get(key) or "").strip()
        # fallback: try exact
        for cand in candidates:
            if cand in row:
                return (row.get(cand) or "").strip()
        return ""

    by_mun: dict[str, dict[str, Any]] = {}
    uf_biomes: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for row in reader:
        code = pick(row, "cd_mun", "cod_mun", "geocódigo", "geocodigo", "codigo", "código")
        digits = "".join(ch for ch in code if ch.isdigit())
        if len(digits) == 7:
            mun_code = digits
        elif len(digits) == 6:
            mun_code = digits.zfill(7)
        else:
            continue
        biome = pick(row, "bioma", "biomapredominante", "bioma_predominante")
        uf = pick(row, "sigla", "uf", "sg_uf") or mun_code[:2]
        name = pick(row, "nm_mun", "nome", "municipio", "município")
        if not biome:
            continue
        by_mun[mun_code] = {
            "ibge_code": mun_code,
            "name": name or mun_code,
            "uf": uf,
            "uf_code": mun_code[:2],
            "biome_predominant": biome,
        }
        uf_biomes[mun_code[:2]][biome] += 1

    by_uf: dict[str, dict[str, Any]] = {}
    for uf_code, counts in uf_biomes.items():
        ordered = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
        by_uf[uf_code] = {
            "ibge_code": uf_code,
            "biomes_present": [
                {"biome": name, "municipality_count": n} for name, n in ordered
            ],
            "text": ", ".join(f"{name} ({n})" for name, n in ordered),
        }

    payload = {
        "retrieved_at": utc_now(),
        "reference_period": "2024",
        "status_label": "OBSERVADO",
        "source": TERRITORY_SPECS["biome_predominant"]["source"],
        "mun_count": len(by_mun),
        "uf_count": len(by_uf),
        "by_mun": by_mun,
        "by_uf": by_uf,
    }
    out = fixtures_dir() / "territory" / "biomes_2024.json"
    write_json(out, payload)
    return {"wrote": str(out), "mun": len(by_mun), "uf": len(by_uf)}


def fetch_coastal() -> dict[str, Any]:
    """Parse coastal municipality list if downloadable; otherwise empty set with provenance."""
    coastal: set[str] = set()
    note = "ok"
    try:
        raw = fetch_bytes(COASTAL_XLS_URL, timeout=120)
        snapshot_raw(
            "ibge",
            "Lista_Municipio_CosteiroMarinho_250mil.xls",
            raw,
            {"source_url": COASTAL_XLS_URL, "connector": "territory.coastal"},
        )
        # Legacy .xls: extract digit sequences that look like IBGE mun codes
        text = raw.decode("latin-1", errors="ignore")
        import re

        for match in re.findall(r"\b(\d{7})\b", text):
            coastal.add(match)
        if not coastal:
            # try utf-8 csv-ish
            text2 = _decode_csv(raw)
            for match in re.findall(r"\b(\d{7})\b", text2):
                coastal.add(match)
        note = f"codes={len(coastal)}"
    except Exception as exc:  # noqa: BLE001
        note = f"unavailable:{exc}"

    payload = {
        "retrieved_at": utc_now(),
        "reference_period": "2019",
        "status_label": "OBSERVADO" if coastal else "SEM DADO",
        "source": TERRITORY_SPECS["coastal_marine"]["source"],
        "note": note,
        "codes": sorted(coastal),
        "count": len(coastal),
    }
    out = fixtures_dir() / "territory" / "coastal_marine.json"
    write_json(out, payload)
    return {"wrote": str(out), "count": len(coastal), "note": note}


def refresh_all() -> dict[str, Any]:
    catalog_path = fixtures_dir() / "territory" / "catalog.json"
    write_json(
        catalog_path,
        {
            "retrieved_at": utc_now(),
            "territory": TERRITORY_SPECS,
            "metrics": METRIC_DEFINITIONS,
        },
    )
    return {
        "catalog": str(catalog_path),
        "indigenous": fetch_indigenous(),
        "quilombola": fetch_quilombola(),
        "area": fetch_area(),
        "biomes": fetch_biomes(),
        "coastal": fetch_coastal(),
        "catalog_checksum": hashlib.sha256(
            json.dumps(TERRITORY_SPECS, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16],
    }

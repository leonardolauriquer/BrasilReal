"""TSE open-data connector — presidential results by UF (party + turn).

Source: Portal de Dados Abertos do TSE
  votacao_candidato_munzona_{year}.zip → *_BR.csv (cargo Presidente)
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

from common import fetch_bytes, fixtures_dir, raw_dir, utc_now, write_json
from tse_catalog import (
    CORE_PARTY_CODES,
    DATASET_PAGE,
    GOV_MARGIN_SPEC,
    GOV_WINNER_SPEC,
    MARGIN_SPEC,
    ORGANIZATION,
    TSE_YEARS,
    WINNER_SPEC,
    party_spec,
)

ZIP_URL = (
    "https://cdn.tse.jus.br/estatistica/sead/odsele/"
    "votacao_candidato_munzona/votacao_candidato_munzona_{year}.zip"
)


def _estados_meta() -> tuple[dict[str, str], dict[str, str]]:
    """sigla→ibge_code, sigla→name"""
    path = fixtures_dir() / "ibge" / "estados_refresh.json"
    code_by_uf: dict[str, str] = {}
    name_by_uf: dict[str, str] = {}
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data.get("items", []):
            uf = item["sigla"]
            code_by_uf[uf] = str(item["id"]).zfill(2)
            name_by_uf[uf] = item["nome"]
    return code_by_uf, name_by_uf


def _zip_path(year: int) -> Path:
    return raw_dir() / "tse" / f"votacao_candidato_munzona_{year}.zip"


def ensure_zip(year: int, *, force: bool = False) -> Path:
    path = _zip_path(year)
    path.parent.mkdir(parents=True, exist_ok=True)
    scratch = Path(__file__).resolve().parents[2] / "scratch" / f"votacao_candidato_munzona_{year}.zip"
    if not force and path.exists() and path.stat().st_size > 1_000_000:
        return path
    if not force and scratch.exists() and scratch.stat().st_size > 1_000_000:
        path.write_bytes(scratch.read_bytes())
        return path
    url = ZIP_URL.format(year=year)
    raw = fetch_bytes(url, timeout=600, retries=2)
    path.write_bytes(raw)
    meta = {
        "source_url": url,
        "connector": "tse.votacao_candidato_munzona",
        "year": year,
        "retrieved_at": utc_now(),
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    (path.parent / f"votacao_candidato_munzona_{year}.meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


SKIP_UF_FILES = {"BR", "ZZ", "VT", "BRASIL"}


def _pick_br_csv(z: zipfile.ZipFile, year: int) -> str:
    names = z.namelist()
    prefer = [
        f"votacao_candidato_munzona_{year}_BR.csv",
        f"votacao_candidato_munzona_{year}_br.csv",
    ]
    for p in prefer:
        if p in names:
            return p
    for n in names:
        upper = n.upper()
        if upper.endswith("_BR.CSV") and "BRASIL" not in upper:
            return n
    raise RuntimeError(f"TSE {year}: BR CSV not found in zip ({len(names)} files)")


def _csv_members_for_cargo(z: zipfile.ZipFile, year: int, cargo_contains: str) -> list[str]:
    """Presidente lives in *_BR.csv; governador is split across the 27 UF CSVs."""
    if cargo_contains.upper() == "PRESIDENTE":
        return [_pick_br_csv(z, year)]
    members: list[str] = []
    for name in z.namelist():
        if not name.lower().endswith(".csv"):
            continue
        stem = Path(name).stem.upper()
        suf = stem.rsplit("_", 1)[-1]
        if len(suf) == 2 and suf.isalpha() and suf not in SKIP_UF_FILES:
            members.append(name)
    if len(members) != 27:
        raise RuntimeError(
            f"TSE {year}: expected 27 UF CSVs for {cargo_contains}, got {len(members)}"
        )
    return members


def parse_votes_by_uf_party(
    year: int,
    zip_path: Path,
    *,
    cargo_contains: str,
) -> dict[str, dict[str, dict[str, int]]]:
    """Return {period: {uf: {party: votes}}} for a TSE cargo needle (PRESIDENTE / GOVERNADOR)."""
    needle = cargo_contains.upper()
    out: dict[str, dict[str, dict[str, int]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    with zipfile.ZipFile(zip_path) as z:
        for member in _csv_members_for_cargo(z, year, needle):
            with z.open(member) as fh:
                reader = csv.DictReader(io.TextIOWrapper(fh, encoding="latin-1"), delimiter=";")

                def norm(row: dict[str, Any]) -> dict[str, str]:
                    return {
                        (k or "").strip(): (v.strip() if isinstance(v, str) else str(v or ""))
                        for k, v in row.items()
                    }

                for row in reader:
                    r = norm(row)
                    cargo = (r.get("DS_CARGO") or "").upper()
                    if needle not in cargo:
                        continue
                    if "VICE" in cargo:
                        continue
                    uf = r.get("SG_UF", "")
                    if not uf or uf in {"ZZ", "VT"}:
                        continue
                    turno = r.get("NR_TURNO", "")
                    if turno not in {"1", "2"}:
                        continue
                    party = (r.get("SG_PARTIDO") or "").upper()
                    if not party or party in {"#NULO#", "#NE#", "-1"}:
                        continue
                    raw_v = r.get("QT_VOTOS_NOMINAIS_VALIDOS") or r.get("QT_VOTOS_NOMINAIS") or "0"
                    try:
                        votes = int(str(raw_v).replace(".", "").replace(",", ""))
                    except ValueError:
                        continue
                    period = f"{year}T{turno}"
                    out[period][uf][party] += votes
    return {p: {uf: dict(parties) for uf, parties in ufs.items()} for p, ufs in out.items()}


def parse_president_by_uf_party(year: int, zip_path: Path) -> dict[str, dict[str, dict[str, int]]]:
    """Return {period: {uf: {party: votes}}} for presidential races."""
    return parse_votes_by_uf_party(year, zip_path, cargo_contains="PRESIDENTE")


def _records_for_share(
    party_votes: dict[str, dict[str, int]],
    *,
    code_by_uf: dict[str, str],
    name_by_uf: dict[str, str],
    party: str | None,
    mode: str,
) -> list[dict[str, Any]]:
    """mode: party | winner | margin"""
    records: list[dict[str, Any]] = []
    for uf in sorted(code_by_uf):
        parties = party_votes.get(uf) or {}
        total = sum(parties.values())
        if total <= 0:
            continue
        ranked = sorted(parties.items(), key=lambda x: -x[1])
        if mode == "party":
            assert party is not None
            value = round(100.0 * parties.get(party, 0) / total, 4)
        elif mode == "winner":
            value = round(100.0 * ranked[0][1] / total, 4)
        elif mode == "margin":
            first = ranked[0][1] if ranked else 0
            second = ranked[1][1] if len(ranked) > 1 else 0
            value = round(100.0 * (first - second) / total, 4)
        else:
            raise ValueError(mode)
        records.append(
            {
                "ibge_code": code_by_uf[uf],
                "uf": uf,
                "name": name_by_uf.get(uf, uf),
                "value": value,
            }
        )
    return records


def _write_indicator(
    spec: dict[str, Any],
    series: dict[str, list[dict[str, Any]]],
    *,
    source_files: list[str],
    cargo_label: str = "Presidente",
) -> dict[str, Any]:
    periods = sorted(series.keys())
    if not periods:
        raise RuntimeError(f"{spec['id']}: no periods")
    latest = periods[-1]
    records = series[latest]
    if len(records) != 27:
        raise RuntimeError(f"{spec['id']} {latest}: expected 27 UFs, got {len(records)}")
    canonical = json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    checksum = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    payload = {
        "indicator_id": spec["id"],
        "dataset_id": f"tse.{spec['id']}.{latest}",
        "title": f"{spec['name']} — {latest}",
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
        "retrieved_at": utc_now(),
        "available_periods": periods,
        "definition": spec["definition"],
        "source": {
            "organization": ORGANIZATION,
            "dataset": f"votacao_candidato_munzona ({cargo_label}) / {spec['id']}",
            "dataset_page": DATASET_PAGE,
            "url": DATASET_PAGE,
            "method_notes": (
                f"ZIP oficial TSE; CSV *_BR.csv; cargo {cargo_label}; "
                "agregação SG_UF × SG_PARTIDO × NR_TURNO; "
                "percentual sobre soma QT_VOTOS_NOMINAIS_VALIDOS."
            ),
            "files": source_files,
        },
        "limitations": list(spec.get("limitations") or []),
        "checksum_sha256": checksum,
        "records": records,
        "series": series,
    }
    out_dir = fixtures_dir() / "tse" / "indicators"
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / f"{spec['id']}_latest.json", payload)
    return {
        "indicator": spec["id"],
        "periods": periods,
        "latest": latest,
        "path": str(out_dir / f"{spec['id']}_latest.json"),
    }


def fetch_bundle(years: tuple[int, ...] = TSE_YEARS, *, force: bool = False) -> dict[str, Any]:
    code_by_uf, name_by_uf = _estados_meta()
    if len(code_by_uf) != 27:
        raise RuntimeError("tse: need data/fixtures/ibge/estados_refresh.json (27 UFs)")

    # period -> uf -> party -> votes
    merged: dict[str, dict[str, dict[str, int]]] = {}
    source_files: list[str] = []
    for year in years:
        zpath = ensure_zip(year, force=force)
        source_files.append(zpath.name)
        parsed = parse_president_by_uf_party(year, zpath)
        for period, uf_map in parsed.items():
            if len(uf_map) != 27:
                raise RuntimeError(f"tse {period}: expected 27 UFs, got {len(uf_map)}")
            merged[period] = uf_map

    # Party set: core codes that appear with any votes
    parties_present: set[str] = set()
    for uf_map in merged.values():
        for parties in uf_map.values():
            parties_present.update(parties)

    results: list[dict[str, Any]] = []

    winner_series: dict[str, list[dict[str, Any]]] = {}
    margin_series: dict[str, list[dict[str, Any]]] = {}
    for period, uf_map in sorted(merged.items()):
        winner_series[period] = _records_for_share(
            uf_map, code_by_uf=code_by_uf, name_by_uf=name_by_uf, party=None, mode="winner"
        )
        margin_series[period] = _records_for_share(
            uf_map, code_by_uf=code_by_uf, name_by_uf=name_by_uf, party=None, mode="margin"
        )
    results.append(_write_indicator(WINNER_SPEC, winner_series, source_files=source_files))
    results.append(_write_indicator(MARGIN_SPEC, margin_series, source_files=source_files))

    for code in CORE_PARTY_CODES:
        if code not in parties_present:
            continue
        series: dict[str, list[dict[str, Any]]] = {}
        for period, uf_map in sorted(merged.items()):
            # Skip period if party has zero votes in all UFs
            if not any(parties.get(code, 0) > 0 for parties in uf_map.values()):
                continue
            series[period] = _records_for_share(
                uf_map, code_by_uf=code_by_uf, name_by_uf=name_by_uf, party=code, mode="party"
            )
        if series:
            results.append(_write_indicator(party_spec(code), series, source_files=source_files))

    return {
        "status": "ok",
        "years": list(years),
        "indicators": results,
        "retrieved_at": utc_now(),
    }


def fetch_governor_bundle(years: tuple[int, ...] = TSE_YEARS, *, force: bool = False) -> dict[str, Any]:
    """Governor winner/margin — a period is kept only when all 27 UFs have votes."""
    code_by_uf, name_by_uf = _estados_meta()
    if len(code_by_uf) != 27:
        raise RuntimeError("tse: need data/fixtures/ibge/estados_refresh.json (27 UFs)")

    merged: dict[str, dict[str, dict[str, int]]] = {}
    source_files: list[str] = []
    skipped: list[str] = []
    for year in years:
        zpath = ensure_zip(year, force=force)
        source_files.append(zpath.name)
        parsed = parse_votes_by_uf_party(year, zpath, cargo_contains="GOVERNADOR")
        for period, uf_map in parsed.items():
            if len(uf_map) != 27:
                skipped.append(f"{period}:{len(uf_map)} UFs")
                continue
            merged[period] = uf_map

    if not merged:
        return {
            "status": "skipped",
            "reason": "no governor period with 27 UFs",
            "skipped": skipped,
            "retrieved_at": utc_now(),
        }

    winner_series: dict[str, list[dict[str, Any]]] = {}
    margin_series: dict[str, list[dict[str, Any]]] = {}
    for period, uf_map in sorted(merged.items()):
        winner_series[period] = _records_for_share(
            uf_map, code_by_uf=code_by_uf, name_by_uf=name_by_uf, party=None, mode="winner"
        )
        margin_series[period] = _records_for_share(
            uf_map, code_by_uf=code_by_uf, name_by_uf=name_by_uf, party=None, mode="margin"
        )
        if len(winner_series[period]) != 27:
            raise RuntimeError(f"gov_winner_share {period}: expected 27 UFs")

    results = [
        _write_indicator(
            GOV_WINNER_SPEC, winner_series, source_files=source_files, cargo_label="Governador"
        ),
        _write_indicator(
            GOV_MARGIN_SPEC, margin_series, source_files=source_files, cargo_label="Governador"
        ),
    ]
    return {
        "status": "ok",
        "years": list(years),
        "skipped_periods": skipped,
        "indicators": results,
        "retrieved_at": utc_now(),
    }


if __name__ == "__main__":
    print(json.dumps(fetch_bundle(), ensure_ascii=False, indent=2))

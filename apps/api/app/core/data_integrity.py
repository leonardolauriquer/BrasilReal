"""Data integrity gates — fail closed; never ship inventable / unlabeled numbers."""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
from pathlib import Path
from typing import Any

integrity_log = logging.getLogger("brasilreal.integrity")

# Official UF set (IBGE codes + siglas).
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
UF_SIGLAS = set(UF_CODES.values())
EXPECTED_UF_COUNT = 27

PERIOD_RE = re.compile(r"^(\d{4}|\d{4}T[12]|\d{6}|\d{4}-\d{2}|\d{4}-\d{2}-\d{2})$")
FIXTURE_INDICATOR_RELDIRS = (
    "ibge/indicators",
    "ipeadata/indicators",
    "comex/indicators",
    "tse/indicators",
    "siconfi/indicators",
    "dieese/indicators",
    "lentes/indicators",
)


class DataIntegrityError(RuntimeError):
    """Raised when fixtures or observation rows violate honesty rules."""


def has_provenance(row: dict[str, Any]) -> bool:
    src = row.get("source")
    if not isinstance(src, dict):
        return False
    return bool(
        row.get("definition")
        and src.get("organization")
        and src.get("dataset")
        and row.get("reference_period")
        and row.get("status_label")
    )


def assert_period_key(period: str | None, *, field: str = "period") -> None:
    if period is None or period == "":
        return
    if not PERIOD_RE.match(str(period)):
        raise DataIntegrityError(f"Invalid {field} key: {period!r}")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def validate_population_fixture(payload: dict[str, Any], *, path: Path | None = None) -> list[str]:
    errors: list[str] = []
    records = payload.get("records") or []
    if len(records) != EXPECTED_UF_COUNT:
        errors.append(f"population: expected {EXPECTED_UF_COUNT} UFs, got {len(records)}")
    codes = {str(r.get("ibge_code")) for r in records}
    missing = set(UF_CODES) - codes
    if missing:
        errors.append(f"population: missing UF codes {sorted(missing)}")
    extras = codes - set(UF_CODES)
    if extras:
        errors.append(f"population: unknown UF codes {sorted(extras)}")
    for r in records:
        code = str(r.get("ibge_code"))
        uf = r.get("uf")
        if code in UF_CODES and uf != UF_CODES[code]:
            errors.append(f"population: code {code} expected UF {UF_CODES[code]}, got {uf}")
        pop = r.get("population")
        if not isinstance(pop, (int, float)) or pop <= 0 or not math.isfinite(float(pop)):
            errors.append(f"population: invalid value for {uf}: {pop!r}")
    declared = payload.get("brazil_total")
    if declared is not None:
        total = sum(int(r["population"]) for r in records if isinstance(r.get("population"), (int, float)))
        if int(declared) != total:
            errors.append(f"population: brazil_total {declared} != sum(records) {total}")
    if path and payload.get("checksum_sha256"):
        # Checksum is of canonical content excluding itself — keep as soft check of presence.
        if not re.fullmatch(r"[0-9a-f]{64}", str(payload["checksum_sha256"])):
            errors.append("population: checksum_sha256 malformed")
    src = payload.get("source") or {}
    if not src.get("organization"):
        errors.append("population: source.organization missing")
    if not (payload.get("dataset_id") or src.get("dataset") or src.get("dataset_page")):
        errors.append("population: dataset identity missing")
    return errors


def validate_pib_fixture(payload: dict[str, Any]) -> list[str]:
    if not payload:
        return []
    errors: list[str] = []
    records = payload.get("records") or []
    if len(records) != EXPECTED_UF_COUNT:
        errors.append(f"pib: expected {EXPECTED_UF_COUNT} UFs, got {len(records)}")
    for r in records:
        val = r.get("pib_brl")
        if not isinstance(val, (int, float)) or val < 0 or not math.isfinite(float(val)):
            errors.append(f"pib: invalid pib_brl for {r.get('uf')}: {val!r}")
    declared = payload.get("brazil_total_brl")
    if declared is not None and records:
        total = sum(float(r["pib_brl"]) for r in records)
        if abs(float(declared) - total) > 1.0:  # BRL cents tolerance
            errors.append(f"pib: brazil_total_brl {declared} != sum {total}")
    src = payload.get("source") or {}
    if not src.get("organization"):
        errors.append("pib: source.organization missing")
    if not payload.get("reference_period"):
        errors.append("pib: reference_period missing")
    return errors


def validate_social_fixture(payload: dict[str, Any], *, path: str = "") -> list[str]:
    errors: list[str] = []
    ind = payload.get("indicator_id") or path
    if not payload.get("definition"):
        errors.append(f"{ind}: definition missing")
    if not payload.get("unit"):
        errors.append(f"{ind}: unit missing")
    if not payload.get("status_label"):
        errors.append(f"{ind}: status_label missing")
    src = payload.get("source") or {}
    if not src.get("organization"):
        errors.append(f"{ind}: source.organization missing")
    if not (
        src.get("dataset")
        or src.get("dataset_page")
        or src.get("serie_page")
        or payload.get("dataset_id")
    ):
        errors.append(f"{ind}: source.dataset identity missing")

    unit = str(payload.get("unit") or "")
    series = payload.get("series") if isinstance(payload.get("series"), dict) else None
    periods: dict[str, list] = {}
    if series:
        for k, rows in series.items():
            try:
                assert_period_key(str(k), field=f"{ind}.series key")
            except DataIntegrityError as exc:
                errors.append(str(exc))
            if not isinstance(rows, list):
                errors.append(f"{ind}: series[{k}] not a list")
                continue
            periods[str(k)] = rows
    elif isinstance(payload.get("records"), list):
        ref = str(payload.get("reference_period") or "")
        if ref:
            try:
                assert_period_key(ref, field=f"{ind}.reference_period")
            except DataIntegrityError as exc:
                errors.append(str(exc))
        periods[ref or "default"] = payload["records"]

    for period, rows in periods.items():
        if len(rows) != EXPECTED_UF_COUNT:
            # Party layers may omit empty turnos entirely (period absent), but a present period must be 27.
            errors.append(f"{ind}@{period}: expected {EXPECTED_UF_COUNT} rows, got {len(rows)}")
            continue
        codes = {str(r.get("ibge_code")) for r in rows}
        if codes != set(UF_CODES):
            errors.append(f"{ind}@{period}: UF code set mismatch")
        for r in rows:
            val = r.get("value")
            if not isinstance(val, (int, float)) or not math.isfinite(float(val)):
                errors.append(f"{ind}@{period}: non-finite value {r.get('uf')}")
                continue
            if unit == "%" and not (0 <= float(val) <= 100):
                errors.append(f"{ind}@{period}: % out of range for {r.get('uf')}: {val}")
            if "nota" in unit.lower() and not (0 <= float(val) <= 100):
                errors.append(f"{ind}@{period}: nota out of range for {r.get('uf')}: {val}")
            if unit == "índice" and not (0 <= float(val) <= 1):
                errors.append(f"{ind}@{period}: índice out of range for {r.get('uf')}: {val}")
            if (
                unit
                in {
                    "habitantes",
                    "homicídios",
                    "USD",
                    "BRL",
                    "BRL/mês",
                    "pessoas",
                    "km²",
                    "anos",
                    "unidades locais",
                }
                and float(val) < 0
                and ind != "dcl_rreo"
            ):
                errors.append(f"{ind}@{period}: negative additive for {r.get('uf')}: {val}")
            if unit.lower().startswith("por ") and float(val) < 0:
                errors.append(f"{ind}@{period}: negative rate for {r.get('uf')}: {val}")
            if unit == "anos" and not 0 < float(val) < 120:
                errors.append(f"{ind}@{period}: age out of range for {r.get('uf')}: {val}")
            if unit == "homens/100 mulheres" and not 50 < float(val) < 150:
                errors.append(f"{ind}@{period}: sex ratio out of range for {r.get('uf')}: {val}")
            if unit == "salários mínimos" and not 0 < float(val) < 30:
                errors.append(f"{ind}@{period}: SM multiple out of range for {r.get('uf')}: {val}")
            if unit == "empresas" and float(val) < 0:
                errors.append(f"{ind}@{period}: negative firms for {r.get('uf')}: {val}")
    return errors


def validate_loaded_store(store: Any) -> None:
    """Hard gate after fixture load — refuse to serve if broken."""
    errors: list[str] = []
    errors.extend(validate_population_fixture(store.population or {}))
    if store.pib:
        errors.extend(validate_pib_fixture(store.pib))
    for ind_id, payload in (store.social or {}).items():
        errors.extend(validate_social_fixture(payload, path=ind_id))
    if errors:
        preview = "; ".join(errors[:12])
        more = f" (+{len(errors) - 12} more)" if len(errors) > 12 else ""
        raise DataIntegrityError(f"Fixture integrity failed: {preview}{more}")


def gate_observation_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Drop unlabeled / inventable-looking rows before they leave the API."""
    kept: list[dict[str, Any]] = []
    dropped: list[dict[str, str]] = []
    for row in rows:
        ind = str(row.get("indicator") or "")
        geo = str(row.get("geography_ibge_code") or row.get("uf") or "")
        if not has_provenance(row):
            dropped.append({"indicator": ind, "geography": geo, "reason": "missing_provenance"})
            continue
        val = row.get("value")
        if not isinstance(val, (int, float)) or not math.isfinite(float(val)):
            dropped.append({"indicator": ind, "geography": geo, "reason": "non_finite_value"})
            continue
        unit = str(row.get("unit") or "")
        if unit == "%" and not (0 <= float(val) <= 100):
            dropped.append({"indicator": ind, "geography": geo, "reason": "percent_out_of_range"})
            continue
        if unit == "índice" and not (0 <= float(val) <= 1):
            dropped.append({"indicator": ind, "geography": geo, "reason": "index_out_of_range"})
            continue
        try:
            assert_period_key(str(row.get("reference_period") or ""), field="reference_period")
        except DataIntegrityError:
            dropped.append({"indicator": ind, "geography": geo, "reason": "bad_reference_period"})
            continue
        code = str(row.get("geography_ibge_code") or "")
        uf = str(row.get("uf") or "")
        if code in UF_CODES and uf and uf != UF_CODES[code]:
            dropped.append({"indicator": ind, "geography": geo, "reason": "uf_code_mismatch"})
            continue
        kept.append(row)
    return kept, dropped


MANIFEST_NAME = "MANIFEST.json"
VOLATILE_KEYS = frozenset({"retrieved_at", "checksum_sha256"})
LAYER_VALUE_KEYS = ("value", "population", "pib_brl")


def locked_fixture_paths(root: Path) -> list[Path]:
    """Observation-painting fixtures that must be checksum-locked."""
    paths: list[Path] = []
    for rel in ("ibge/population_uf_2025.json", "ibge/pib_uf_latest.json"):
        p = root / rel
        if p.exists():
            paths.append(p)
    for rel in FIXTURE_INDICATOR_RELDIRS:
        d = root / rel
        if not d.exists():
            continue
        paths.extend(sorted(d.glob("*_latest.json")))
    return paths


def _strip_volatile(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _strip_volatile(v) for k, v in obj.items() if k not in VOLATILE_KEYS}
    if isinstance(obj, list):
        return [_strip_volatile(i) for i in obj]
    return obj


def canonical_sha256(payload: Any) -> str:
    blob = json.dumps(
        _strip_volatile(payload),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _record_pairs(records: list[Any]) -> list[list[Any]]:
    pairs: list[list[Any]] = []
    for row in records:
        if not isinstance(row, dict):
            continue
        code = str(row.get("ibge_code") or "")
        val = None
        for key in LAYER_VALUE_KEYS:
            if key in row:
                val = row[key]
                break
        pairs.append([code, val])
    pairs.sort(key=lambda p: p[0])
    return pairs


def layer_fingerprints(payload: dict[str, Any], *, indicator_id: str) -> dict[str, Any]:
    series = payload.get("series") if isinstance(payload.get("series"), dict) else None
    periods: dict[str, list[Any]] = {}
    if series:
        for k, rows in series.items():
            if isinstance(rows, list):
                periods[str(k)] = rows
    elif isinstance(payload.get("records"), list):
        ref = str(payload.get("reference_period") or payload.get("reference_date") or "default")
        periods[ref] = payload["records"]
    out: dict[str, Any] = {"indicator": indicator_id, "periods": {}}
    for period, rows in sorted(periods.items()):
        pairs = _record_pairs(rows)
        digest = hashlib.sha256(
            json.dumps({"indicator": indicator_id, "period": period, "pairs": pairs}, separators=(",", ":")).encode(
                "utf-8"
            )
        ).hexdigest()
        out["periods"][period] = {"n": len(pairs), "values_sha256": digest}
    return out


def build_manifest(root: Path) -> dict[str, Any]:
    files: dict[str, Any] = {}
    layers: dict[str, Any] = {}
    for path in locked_fixture_paths(root):
        rel = path.relative_to(root).as_posix()
        payload = json.loads(path.read_text(encoding="utf-8"))
        files[rel] = {"sha256": canonical_sha256(payload)}
        if rel.endswith("population_uf_2025.json"):
            layers["population"] = layer_fingerprints(payload, indicator_id="population")
            layers["population"]["brazil_total"] = payload.get("brazil_total")
        elif rel.endswith("pib_uf_latest.json"):
            layers["pib"] = layer_fingerprints(payload, indicator_id="pib")
            layers["pib"]["brazil_total_brl"] = payload.get("brazil_total_brl")
        else:
            ind = str(payload.get("indicator_id") or path.stem.replace("_latest", ""))
            layers[ind] = layer_fingerprints(payload, indicator_id=ind)
    return {
        "schema": "brasilreal.fixtures.manifest.v1",
        "algorithm": "sha256-canonical-strip-volatile",
        "files": files,
        "layers": layers,
    }


def write_manifest(root: Path) -> Path:
    man = root / MANIFEST_NAME
    payload = build_manifest(root)
    man.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return man


def validate_manifest(root: Path) -> list[str]:
    man_path = root / MANIFEST_NAME
    if not man_path.exists():
        return [f"missing {MANIFEST_NAME} — run python scripts/write_fixture_manifest.py"]
    try:
        locked = json.loads(man_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{MANIFEST_NAME} is not valid JSON: {exc}"]
    expected = build_manifest(root)
    errors: list[str] = []
    if locked.get("schema") != expected["schema"]:
        errors.append(f"{MANIFEST_NAME} schema mismatch")
    locked_files = locked.get("files") or {}
    expected_files = expected["files"]
    for rel in sorted(set(locked_files) | set(expected_files)):
        if rel not in locked_files:
            errors.append(f"manifest missing file {rel}")
            continue
        if rel not in expected_files:
            errors.append(f"manifest extra file {rel} (fixture deleted?)")
            continue
        got = expected_files[rel]["sha256"]
        want = (locked_files[rel] or {}).get("sha256")
        if got != want:
            errors.append(f"canonical sha256 mismatch: {rel}")
    locked_layers = locked.get("layers") or {}
    for ind, spec in expected["layers"].items():
        have = locked_layers.get(ind) or {}
        if have.get("periods") != spec.get("periods"):
            errors.append(f"golden layer mismatch: {ind}")
        if ind == "population" and have.get("brazil_total") != spec.get("brazil_total"):
            errors.append("golden brazil_total mismatch")
        if ind == "pib" and have.get("brazil_total_brl") != spec.get("brazil_total_brl"):
            errors.append("golden brazil_total_brl mismatch")
    extra_layers = set(locked_layers) - set(expected["layers"])
    if extra_layers:
        errors.append(f"manifest extra layers {sorted(extra_layers)}")
    return errors


def enforce_uf_coverage(
    items: list[dict[str, Any]],
    dropped: list[dict[str, str]],
    *,
    indicator: str | None,
    geography: str | None,
) -> tuple[list[dict[str, Any]], list[dict[str, str]], bool | None]:
    """National UF layers must be complete (27) or empty — never a partial map."""
    if geography or not items:
        return items, dropped, None
    codes = {str(row.get("geography_ibge_code") or "") for row in items}
    uf_codes = {c for c in codes if len(c) == 2}
    looking_at_ufs = bool(items) and all(len(str(row.get("geography_ibge_code") or "")) == 2 for row in items)
    if not looking_at_ufs:
        return items, dropped, None
    if len(items) != EXPECTED_UF_COUNT or uf_codes != set(UF_CODES):
        dropped.append(
            {
                "indicator": str(indicator or "*"),
                "geography": "*",
                "reason": f"uf_coverage:{len(items)}!={EXPECTED_UF_COUNT}",
            }
        )
        return [], dropped, False
    return items, dropped, True


def enforce_additive_totals(
    items: list[dict[str, Any]],
    dropped: list[dict[str, str]],
    *,
    indicator: str | None,
    expected_total: Any,
    field: str,
    tolerance: float = 0.0,
) -> tuple[list[dict[str, Any]], list[dict[str, str]], bool | None]:
    if expected_total is None or not items:
        return items, dropped, None
    total = sum(float(row["value"]) for row in items)
    ok = abs(total - float(expected_total)) <= tolerance
    if not ok:
        dropped.append(
            {
                "indicator": str(indicator or "*"),
                "geography": "*",
                "reason": f"{field}_mismatch:{total}!={expected_total}",
            }
        )
        return [], dropped, False
    return items, dropped, True


def log_integrity_drops(
    *,
    indicator: str | None,
    raw_count: int,
    kept_count: int,
    dropped: list[dict[str, str]],
) -> None:
    if not dropped:
        return
    integrity_log.warning(
        "integrity_drop indicator=%s raw=%s kept=%s dropped=%s sample=%s",
        indicator or "*",
        raw_count,
        kept_count,
        len(dropped),
        json.dumps(dropped[:20], ensure_ascii=False),
    )


def inspect_write_payload(path: Path, payload: Any) -> list[str]:
    """Refuse ingestion writes that would break the honesty gate."""
    if not isinstance(payload, dict):
        return []
    name = path.name
    if name.startswith("population_uf") and name.endswith(".json"):
        return validate_population_fixture(payload, path=path)
    if name.startswith("pib_uf") and name.endswith(".json"):
        return validate_pib_fixture(payload)
    if path.parent.name == "indicators" and name.endswith(".json"):
        return validate_social_fixture(payload, path=name)
    return []


def validate_fixture_payloads(root: Path) -> list[str]:
    """Schema / coverage of fixtures — does not compare MANIFEST locks."""
    errors: list[str] = []
    pop = root / "ibge" / "population_uf_2025.json"
    if pop.exists():
        errors.extend(validate_population_fixture(json.loads(pop.read_text(encoding="utf-8")), path=pop))
    else:
        errors.append("missing population_uf_2025.json")
    pib = root / "ibge" / "pib_uf_latest.json"
    if pib.exists():
        errors.extend(validate_pib_fixture(json.loads(pib.read_text(encoding="utf-8"))))
    for rel in FIXTURE_INDICATOR_RELDIRS:
        d = root / rel
        if not d.exists():
            continue
        for path in sorted(d.glob("*_latest.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            errors.extend(validate_social_fixture(payload, path=path.name))
    return errors


def validate_fixtures_tree(root: Path) -> list[str]:
    """Scan on-disk fixtures (for CI / scripts)."""
    errors = validate_fixture_payloads(root)
    errors.extend(validate_manifest(root))
    return errors


def validate_disk_locks(root: Path) -> None:
    errors = validate_manifest(root)
    if errors:
        preview = "; ".join(errors[:12])
        more = f" (+{len(errors) - 12} more)" if len(errors) > 12 else ""
        raise DataIntegrityError(f"Fixture lock failed: {preview}{more}")

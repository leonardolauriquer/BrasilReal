#!/usr/bin/env python3
"""Fail if TS / Python / JSON Schema observation contracts drift."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "packages" / "contracts" / "schema" / "observation.json"
TS = ROOT / "packages" / "contracts" / "typescript" / "atlas.ts"
PY = ROOT / "packages" / "contracts" / "python" / "atlas_types.py"


def _ts_block(src: str, type_name: str) -> str:
    match = re.search(
        rf"export type {re.escape(type_name)} = \{{(.*?)\n\}};",
        src,
        re.S,
    )
    if not match:
        raise SystemExit(f"could not find TypeScript type {type_name}")
    return match.group(1)


def _ts_fields(src: str, type_name: str) -> set[str]:
    return set(re.findall(r"^\s{2}([A-Za-z_][A-Za-z0-9_]*)\??:", _ts_block(src, type_name), re.M))


def _ts_optional(src: str, type_name: str) -> set[str]:
    return set(re.findall(r"^\s{2}([A-Za-z_][A-Za-z0-9_]*)\?:", _ts_block(src, type_name), re.M))


def _py_fields(src: str, class_name: str) -> tuple[set[str], set[str]]:
    match = re.search(
        rf"class {re.escape(class_name)}\(TypedDict\):(.*?)(?:\nclass |\Z)",
        src,
        re.S,
    )
    if not match:
        raise SystemExit(f"could not find Python TypedDict {class_name}")
    body = match.group(1)
    fields = set(re.findall(r"^\s{4}([A-Za-z_][A-Za-z0-9_]*)\s*:", body, re.M))
    optional = set(re.findall(r"^\s{4}([A-Za-z_][A-Za-z0-9_]*)\s*:\s*NotRequired", body, re.M))
    return fields, optional


def main() -> int:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    required = set(schema["required"])
    properties = set(schema["properties"])
    source_required = set(schema["properties"]["source"]["required"])

    ts = TS.read_text(encoding="utf-8")
    py = PY.read_text(encoding="utf-8")
    ts_obs = _ts_fields(ts, "Observation")
    ts_opt = _ts_optional(ts, "Observation")
    py_obs, py_opt = _py_fields(py, "Observation")
    ts_src = _ts_fields(ts, "SourceInfo")
    py_src, _ = _py_fields(py, "SourceInfo")

    errors: list[str] = []
    for field in sorted(required):
        if field not in ts_obs:
            errors.append(f"TS Observation missing required {field}")
        elif field in ts_opt:
            errors.append(f"TS Observation required field {field} is optional")
        if field not in py_obs:
            errors.append(f"Python Observation missing required {field}")
        elif field in py_opt:
            errors.append(f"Python Observation required field {field} is NotRequired")
        if field not in properties:
            errors.append(f"schema properties missing {field}")
    for field in sorted(source_required):
        if field not in ts_src:
            errors.append(f"TS SourceInfo missing required {field}")
        if field not in py_src:
            errors.append(f"Python SourceInfo missing required {field}")

    extra_ts = ts_obs - properties
    extra_py = py_obs - properties
    if extra_ts:
        errors.append(f"TS Observation fields not in schema: {sorted(extra_ts)}")
    if extra_py:
        errors.append(f"Python Observation fields not in schema: {sorted(extra_py)}")

    if errors:
        print(f"FAIL — {len(errors)} contract drift(s):")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("OK — TS / Python / schema observation contracts aligned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

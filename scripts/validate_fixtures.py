#!/usr/bin/env python3
"""Validate Brasil Real fixtures — fail closed for CI / pre-deploy."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "apps" / "api"
sys.path.insert(0, str(API))

from app.core.data_integrity import validate_fixtures_tree  # noqa: E402


def main() -> int:
    fixtures = ROOT / "data" / "fixtures"
    errors = validate_fixtures_tree(fixtures)
    if errors:
        print(f"FAIL — {len(errors)} integrity issue(s):")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("OK — fixtures integrity gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

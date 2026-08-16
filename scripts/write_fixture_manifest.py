#!/usr/bin/env python3
"""Regenerate data/fixtures/MANIFEST.json after an intentional fixture change."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.core.data_integrity import write_manifest  # noqa: E402


def main() -> int:
    path = write_manifest(ROOT / "data" / "fixtures")
    print(f"OK — wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

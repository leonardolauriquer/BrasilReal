"""Backward-compatible CLI wrapper. Prefer: python run.py --source ibge """

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ibge


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="IBGE connector (compat)")
    parser.add_argument("--detect-years", action="store_true")
    parser.add_argument("--pop", default=None, help="Population year or 'last'")
    parser.add_argument("--estados", action="store_true")
    args = parser.parse_args(argv)

    if args.detect_years:
        print(json.dumps(ibge.detect_estimate_years(), ensure_ascii=False, indent=2))
        return 0
    if args.pop:
        print(json.dumps(ibge.fetch_population_uf(args.pop), ensure_ascii=False, indent=2))
        return 0
    # default: estados
    print(json.dumps(ibge.refresh_estados(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

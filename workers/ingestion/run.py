"""Brasil Real ingestion runner — automate official open-data pulls.

Examples:
  python run.py --all
  python run.py --source ibge --ibge-pop 2025
  python run.py --source siconfi
  python run.py --source tesouro
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running as a script from this directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

import comex
import ibge
import ipeadata
import siconfi
import territory
import tesouro
from common import utc_now


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Brasil Real official data ingestion")
    parser.add_argument("--all", action="store_true", help="Run IBGE + SICONFI + Tesouro")
    parser.add_argument(
        "--source",
        choices=["ibge", "siconfi", "tesouro", "territory", "ipeadata", "comex"],
        action="append",
        default=[],
        help="Source to run (repeatable)",
    )
    parser.add_argument("--ibge-pop", default="2025", help="Population period year or 'last'")
    parser.add_argument("--ibge-pib", default="last", help="PIB period year or 'last'")
    parser.add_argument("--comex-from", type=int, default=2018, help="First year for ComexStat series")
    parser.add_argument("--skip-malha", action="store_true")
    parser.add_argument("--skip-pib", action="store_true")
    args = parser.parse_args(argv)

    sources = set(args.source)
    if args.all:
        sources = {"ibge", "siconfi", "tesouro", "territory", "ipeadata", "comex"}
    elif not sources:
        sources = {"ibge", "siconfi", "tesouro"}

    report: dict = {"started_at": utc_now(), "steps": []}

    try:
        if "ibge" in sources:
            report["steps"].append({"step": "ibge.estados", "result": ibge.refresh_estados()})
            report["steps"].append({"step": "ibge.estimate_years", "result": ibge.detect_estimate_years()})
            report["steps"].append(
                {"step": "ibge.population_uf", "result": ibge.fetch_population_uf(args.ibge_pop)}
            )
            if not args.skip_pib:
                report["steps"].append(
                    {"step": "ibge.pib_uf", "result": ibge.fetch_pib_uf(args.ibge_pib)}
                )
            report["steps"].append(
                {"step": "ibge.social_bundle", "result": ibge.fetch_social_bundle()}
            )
            if not args.skip_malha:
                report["steps"].append({"step": "ibge.malha_uf", "result": ibge.refresh_malha_uf()})

        if "territory" in sources:
            report["steps"].append({"step": "territory.refresh", "result": territory.refresh_all()})

        if "ipeadata" in sources:
            report["steps"].append({"step": "ipeadata.bundle", "result": ipeadata.fetch_bundle()})

        if "comex" in sources:
            report["steps"].append(
                {
                    "step": "comex.bundle",
                    "result": comex.fetch_bundle(year_from=args.comex_from),
                }
            )

        if "siconfi" in sources:
            report["steps"].append({"step": "siconfi.entes", "result": siconfi.snapshot_entes()})
            report["steps"].append({"step": "siconfi.rreo_probe", "result": siconfi.probe_rreo()})

        if "tesouro" in sources:
            report["steps"].append(
                {"step": "tesouro.transferencias", "result": tesouro.discover_transferencias()}
            )
    except Exception as exc:  # noqa: BLE001
        report["status"] = "failed"
        report["error"] = str(exc)
        report["finished_at"] = utc_now()
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1

    report["status"] = "ok"
    report["finished_at"] = utc_now()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

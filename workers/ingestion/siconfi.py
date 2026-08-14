"""SICONFI / Tesouro Nacional open API probes and snapshots."""

from __future__ import annotations

import json
from typing import Any

from common import fetch_bytes, fixtures_dir, snapshot_raw, utc_now, write_json

ENTES_URL = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/entes"
RREO_URL = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/rreo"


def snapshot_entes(limit_hint: int = 50) -> dict[str, Any]:
    """Download SICONFI entes catalog (paginated open API)."""
    raw = fetch_bytes(f"{ENTES_URL}?limit={limit_hint}", timeout=120)
    snapshot_raw(
        "siconfi",
        "entes_sample.json",
        raw,
        {"source_url": ENTES_URL, "connector": "siconfi.entes"},
    )
    payload = json.loads(raw.decode("utf-8"))
    items = payload.get("items", [])
    out = {
        "retrieved_at": utc_now(),
        "source_url": ENTES_URL,
        "docs": "https://apidatalake.tesouro.gov.br/docs/siconfi/",
        "status_label": "OBSERVADO",
        "count_returned": len(items),
        "has_more": payload.get("hasMore"),
        "sample": items[:10],
        "limitations": [
            "API pública paginada; não é tempo real tick-a-tick.",
            "Contabilidade pública tem defasagem e revisões; separar empenhado/liquidado/pago.",
        ],
    }
    path = fixtures_dir() / "siconfi" / "entes_sample.json"
    write_json(path, out)
    return {"wrote": str(path), "count_returned": len(items), "has_more": out["has_more"]}


def probe_rreo(an_exercicio: int = 2024, in_bim: int = 6, id_ente: int = 35) -> dict[str, Any]:
    """Fetch one RREO slice as connectivity/schema probe for Fase 2."""
    url = (
        f"{RREO_URL}?an_exercicio={an_exercicio}&in_bim={in_bim}"
        f"&co_tipo_demonstrativo=RREO&id_ente={id_ente}"
    )
    try:
        raw = fetch_bytes(url, timeout=120)
    except Exception as exc:  # noqa: BLE001 - probe should not crash runner
        return {"ok": False, "url": url, "error": str(exc)}
    snapshot_raw(
        "siconfi",
        f"rreo_{id_ente}_{an_exercicio}_b{in_bim}.json",
        raw,
        {"source_url": url, "connector": "siconfi.rreo.probe"},
    )
    payload = json.loads(raw.decode("utf-8"))
    path = fixtures_dir() / "siconfi" / "rreo_probe.json"
    write_json(
        path,
        {
            "retrieved_at": utc_now(),
            "source_url": url,
            "status_label": "OBSERVADO",
            "count_returned": len(payload.get("items", [])),
            "sample": payload.get("items", [])[:5],
        },
    )
    return {"ok": True, "wrote": str(path), "count_returned": len(payload.get("items", []))}

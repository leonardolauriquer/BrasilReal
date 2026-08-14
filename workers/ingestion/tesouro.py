"""Tesouro Transparente / CKAN discovery for constitutional transfers."""

from __future__ import annotations

import json
from typing import Any

from common import fetch_bytes, fixtures_dir, snapshot_raw, utc_now, write_json

CKAN_PACKAGE = (
    "https://www.tesourotransparente.gov.br/ckan/api/3/action/package_show"
    "?id=api-de-transferencias-constitucionais"
)


def discover_transferencias() -> dict[str, Any]:
    raw = fetch_bytes(CKAN_PACKAGE, timeout=60)
    snapshot_raw(
        "tesouro",
        "transferencias_package.json",
        raw,
        {"source_url": CKAN_PACKAGE, "connector": "tesouro.ckan.transferencias"},
    )
    payload = json.loads(raw.decode("utf-8"))
    result = payload.get("result", {})
    resources = [
        {
            "id": r.get("id"),
            "name": r.get("name"),
            "format": r.get("format"),
            "url": r.get("url"),
            "last_modified": r.get("last_modified") or r.get("metadata_modified"),
        }
        for r in result.get("resources", [])
    ]
    out = {
        "retrieved_at": utc_now(),
        "source_url": CKAN_PACKAGE,
        "title": result.get("title"),
        "notes": result.get("notes"),
        "status_label": "OBSERVADO",
        "resources": resources,
        "limitations": [
            "Transferências constitucionais são séries oficiais com defasagem contábil.",
            "Não interpretar automaticamente como 'quanto o estado paga à União'.",
        ],
    }
    path = fixtures_dir() / "tesouro" / "transferencias_package.json"
    write_json(path, out)
    return {"wrote": str(path), "resources": len(resources), "title": out.get("title")}

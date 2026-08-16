"""Build territorial fiche items with mandatory definition + source."""

from __future__ import annotations

from typing import Any


def _ok(item: dict[str, Any]) -> bool:
    src = item.get("source") or {}
    return bool(item.get("definition")) and bool(src.get("organization")) and bool(src.get("dataset"))


def make_item(
    spec: dict[str, Any],
    *,
    value: float | int | None = None,
    text: str | None = None,
    status_label: str | None = None,
    reference_period: str | None = None,
    extra_limitations: list[str] | None = None,
) -> dict[str, Any] | None:
    limitations = list(spec.get("limitations") or [])
    if extra_limitations:
        limitations.extend(extra_limitations)
    item = {
        "id": spec["id"],
        "label": spec["label"],
        "section": spec.get("section", "territorio"),
        "value": value,
        "text": text,
        "unit": spec.get("unit"),
        "status_label": status_label or spec["status_label"],
        "reference_period": reference_period or spec["reference_period"],
        "definition": spec["definition"],
        "source": dict(spec["source"]),
        "limitations": limitations,
    }
    if value is None and (text is None or text == ""):
        item["status_label"] = "SEM DADO"
        item["text"] = item.get("text") or "SEM DADO"
        item["limitations"] = limitations + [
            "Não há valor oficial carregado para esta unidade neste produto."
        ]
    if not _ok(item):
        return None
    return item


def enrich_metric(row: dict[str, Any], metric_specs: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    """Attach definition/source/limitations to an observation row; drop if incomplete."""
    ind = row.get("indicator")
    spec = metric_specs.get(str(ind), {})
    definition = row.get("definition") or spec.get("definition")
    source = row.get("source") or {}
    # Normalize source shape — never invent an organization
    if isinstance(source, dict) and "organization" not in source:
        source = {
            "organization": source.get("organization") or "",
            "dataset": source.get("dataset")
            or source.get("dataset_page")
            or source.get("api_url")
            or row.get("dataset_id")
            or "",
            "url": source.get("url") or source.get("dataset_page") or source.get("api_url"),
        }
    if spec.get("source"):
        # Prefer catalog URL when fixture source lacks dataset label
        catalog_src = spec["source"]
        source = {
            "organization": source.get("organization") or catalog_src.get("organization"),
            "dataset": catalog_src.get("dataset") or source.get("dataset"),
            "url": catalog_src.get("url") or source.get("url"),
            "retrieved_at": source.get("retrieved_at"),
        }
    limitations = list(row.get("limitations") or spec.get("limitations") or [])
    out = {
        **row,
        "definition": definition,
        "source": source,
        "limitations": limitations,
        "short_name": row.get("short_name") or row.get("indicator"),
        "label": row.get("short_name") or row.get("indicator"),
    }
    if not definition or not source.get("organization") or not source.get("dataset"):
        return None
    return out

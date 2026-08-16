"""Normalize heterogeneous fixture `source` blobs into tooltip shape."""

from __future__ import annotations

from typing import Any


def normalize_source(
    src: Any,
    *,
    fallback_dataset: str | None = None,
) -> dict[str, Any]:
    if not isinstance(src, dict):
        return {
            "organization": "",
            "dataset": fallback_dataset or "",
            "url": None,
        }

    org = src.get("organization") or ""
    url = (
        src.get("url")
        or src.get("serie_page")
        or src.get("dataset_page")
        or src.get("api_url")
    )
    # Prefer a stable id/name over a raw URL as `dataset` (UI provenance gate).
    dataset = (
        src.get("dataset")
        or fallback_dataset
        or src.get("sercodigo")
        or src.get("variable_name")
        or ""
    )
    # Last resort: short label from page URL path — never leave empty if org exists.
    if not dataset and isinstance(src.get("dataset_page"), str):
        dataset = "IBGE / página do dataset"

    return {
        "organization": org,
        "dataset": str(dataset),
        "url": url,
    }

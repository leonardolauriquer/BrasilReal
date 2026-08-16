"""Freshness: always prefer the latest official period; cache on miss.

IBGE layers refresh period lists + UF series via disk cache (TTL).
Fixture-only layers (Ipeadata/Comex) serve the newest shipped period —
full source re-pull stays in workers/ingestion (too heavy for request path).
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.paths import repo_root
from app.core.store import store
from app.services import ibge_live

CACHE_ROOT = repo_root() / "data" / "cache" / "freshness"
DEFAULT_TTL_SECONDS = 12 * 60 * 60  # 12h


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _meta_path(key: str) -> Path:
    safe = key.replace(":", "_").replace("/", "_")
    return CACHE_ROOT / f"{safe}.meta.json"


def _write_meta(key: str, payload: dict[str, Any]) -> None:
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    _meta_path(key).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_meta(key: str) -> dict[str, Any] | None:
    path = _meta_path(key)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def cache_age_seconds(key: str) -> float | None:
    meta = _read_meta(key)
    if not meta or "retrieved_epoch" not in meta:
        return None
    return max(0.0, time.time() - float(meta["retrieved_epoch"]))


def indicator_catalog_row(indicator_id: str) -> dict[str, Any]:
    return next((i for i in store.list_indicators() if i["id"] == indicator_id), {})


def _ibge_cache_file(key: str) -> Path:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]
    return repo_root() / "data" / "cache" / "ibge" / f"{digest}.json"


def _invalidate_ibge_key(key: str) -> None:
    path = _ibge_cache_file(key)
    if path.exists():
        path.unlink()


def resolve_periods(
    indicator_id: str,
    *,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    force: bool = False,
) -> dict[str, Any]:
    """Return sorted periods + latest, refreshing IBGE when cache is stale/missing."""
    fixture_periods = store.indicator_periods(indicator_id)
    live_capable = indicator_id in ibge_live.INDICATOR_AGGREGATES
    meta_key = f"periods:{indicator_id}"
    age = cache_age_seconds(meta_key)
    stale = age is None or age >= ttl_seconds

    periods: list[str] = []
    source = "fixture"
    error: str | None = None
    cache_hit = False

    if live_capable:
        try:
            if force or stale:
                _invalidate_ibge_key(f"periods:{indicator_id}")
                cache_hit = False
                epoch = time.time()
            else:
                cache_hit = True
                epoch = time.time() - float(age or 0)
            periods = ibge_live.list_periods(indicator_id)
            source = "live_ibge"
            _write_meta(
                meta_key,
                {
                    "key": meta_key,
                    "indicator": indicator_id,
                    "retrieved_at": _utc_now(),
                    "retrieved_epoch": epoch if cache_hit else time.time(),
                    "ttl_seconds": ttl_seconds,
                    "count": len(periods),
                    "latest": periods[-1] if periods else None,
                },
            )
        except Exception as exc:  # noqa: BLE001
            error = str(exc)
            periods = list(fixture_periods)
            source = "fixture_fallback"
    else:
        periods = list(fixture_periods)
        source = "fixture"
        _write_meta(
            meta_key,
            {
                "key": meta_key,
                "indicator": indicator_id,
                "retrieved_at": _utc_now(),
                "retrieved_epoch": time.time(),
                "ttl_seconds": ttl_seconds,
                "count": len(periods),
                "latest": periods[-1] if periods else None,
                "note": "Fixture-backed; re-ingest via workers/ingestion for source refresh.",
            },
        )

    if not periods and fixture_periods:
        periods = list(fixture_periods)
        source = "fixture_fallback"

    latest = periods[-1] if periods else None
    return {
        "indicator": indicator_id,
        "items": periods,
        "count": len(periods),
        "latest": latest,
        "source": source,
        "cache_hit": cache_hit,
        "ttl_seconds": ttl_seconds,
        "error": error,
    }


def build_live_rows(
    indicator_id: str,
    period: str,
    *,
    geography: str | None = None,
    force: bool = False,
) -> list[dict[str, Any]]:
    """Fetch UF series from IBGE (cached) and shape observation rows with catalog provenance."""
    if force:
        _invalidate_ibge_key(f"uf:{indicator_id}:{period}")
    catalog = indicator_catalog_row(indicator_id)
    rows = ibge_live.fetch_uf_series(indicator_id, period)
    geo_by_code = {g["ibge_code"]: g for g in store.list_geographies()}
    unit = catalog.get("unit") or ""
    status = catalog.get("status_label") or "ESTIMADO"
    higher = bool(catalog.get("higher_is_worse"))
    definition = catalog.get("definition")
    limitations = list(catalog.get("limitations") or [])
    src = catalog.get("source") or {}
    source = {
        "organization": (src.get("organization") if isinstance(src, dict) else None) or "IBGE",
        "dataset": (src.get("dataset") if isinstance(src, dict) else None)
        or f"Agregados sob demanda / {indicator_id} / {period}",
        "url": src.get("url") if isinstance(src, dict) else None,
        "method_notes": "Série sob demanda via API de Agregados (cache local em data/cache).",
    }
    if not definition or not source.get("organization") or not source.get("dataset"):
        # Never invent live rows without catalog provenance.
        return []

    out: list[dict[str, Any]] = []
    for row in rows:
        g = geo_by_code.get(row["ibge_code"], {})
        if geography and geography not in {row["ibge_code"], g.get("uf")}:
            continue
        out.append(
            {
                "indicator": indicator_id,
                "geography_ibge_code": row["ibge_code"],
                "uf": g.get("uf", ""),
                "name": g.get("name") or row["name"],
                "value": row["value"],
                "unit": unit,
                "reference_period": period,
                "release_date": None,
                "status_label": status,
                "evidence_grade": "A",
                "higher_is_worse": higher,
                "definition": definition,
                "limitations": limitations,
                "source": source,
                "dataset_id": f"ibge.{indicator_id}.{period}",
                "quality": "official_estimate",
            }
        )
    _write_meta(
        f"obs:{indicator_id}:{period}",
        {
            "retrieved_at": _utc_now(),
            "retrieved_epoch": time.time(),
            "indicator": indicator_id,
            "period": period,
            "count": len(out),
        },
    )
    return out


def observations_with_freshness(
    indicator: str | None,
    period: str | None,
    geography: str | None,
    *,
    prefer_latest: bool = True,
    force: bool = False,
) -> dict[str, Any]:
    """
    Resolve observations.

    - No period + prefer_latest → newest period (live IBGE list when possible).
    - Cache miss on IBGE → network → data/cache/ibge.
    - Fixture if live fails. Never invent values.
    """
    live_fallback = False
    live_error: str | None = None
    freshness: dict[str, Any] | None = None
    resolved_period = period

    if indicator and (prefer_latest and not resolved_period):
        freshness = resolve_periods(indicator, force=force)
        resolved_period = freshness.get("latest")

    items = store.observations(
        indicator=indicator,
        geography=geography,
        period=resolved_period,
    )

    if not indicator:
        return {
            "items": items,
            "resolved_period": resolved_period,
            "live_fallback": False,
            "live_error": None,
            "freshness": freshness,
        }

    live_ok = indicator in ibge_live.INDICATOR_AGGREGATES
    if live_ok:
        try:
            freshness = freshness or resolve_periods(indicator, force=force)
            latest = freshness.get("latest")
            fixture_periods = set(store.indicator_periods(indicator))

            if prefer_latest and period is None and latest:
                resolved_period = str(latest)
                items = store.observations(
                    indicator=indicator, geography=geography, period=resolved_period
                )

            if resolved_period and not items:
                items = build_live_rows(
                    indicator, str(resolved_period), geography=geography, force=force
                )
                live_fallback = True
            elif (
                prefer_latest
                and period is None
                and latest
                and str(latest) not in fixture_periods
                and items
            ):
                # Fixtures returned a different/older period somehow — force live latest
                items = build_live_rows(
                    indicator, str(latest), geography=geography, force=force
                )
                resolved_period = str(latest)
                live_fallback = True
        except Exception as exc:  # noqa: BLE001
            live_error = str(exc)
            if not items:
                items = store.observations(
                    indicator=indicator, geography=geography, period=None
                )

    return {
        "items": items,
        "resolved_period": resolved_period,
        "live_fallback": live_fallback,
        "live_error": live_error,
        "freshness": freshness,
    }

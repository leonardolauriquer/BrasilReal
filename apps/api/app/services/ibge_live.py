"""On-demand IBGE fetches with disk cache (municipal + periods)."""

from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path
from typing import Any

from app.core.store import repo_root

USER_AGENT = "BrasilReal/0.1 (+educational-simulator)"
CACHE = repo_root() / "data" / "cache" / "ibge"


def _get(url: str, timeout: int = 90) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        if raw[:2] == b"\x1f\x8b":
            import gzip

            raw = gzip.decompress(raw)
        return raw


def _cache_path(key: str) -> Path:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]
    return CACHE / f"{digest}.json"


def cached_json(key: str, url: str) -> Any:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = _cache_path(key)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    raw = _get(url)
    data = json.loads(raw.decode("utf-8"))
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


INDICATOR_AGGREGATES: dict[str, dict[str, Any]] = {
    "population": {"aggregate": 6579, "variable": 9324, "classificacao": None},
    "pib": {"aggregate": 5938, "variable": 37, "classificacao": None},
    "poverty_rate": {"aggregate": 5877, "variable": 9948, "classificacao": None},
    "literacy_rate": {
        "aggregate": 9543,
        "variable": 2513,
        "classificacao": "2[6794]|86[95251]|287[100362]",
    },
    "unemployment_rate": {"aggregate": 4099, "variable": 4099, "classificacao": None},
}


def list_periods(indicator: str) -> list[str]:
    meta = INDICATOR_AGGREGATES.get(indicator)
    if not meta:
        return []
    url = f"https://servicodados.ibge.gov.br/api/v3/agregados/{meta['aggregate']}/periodos"
    data = cached_json(f"periods:{indicator}", url)
    ids = [str(item["id"] if isinstance(item, dict) else item) for item in data]
    return sorted(ids)


def fetch_uf_series(indicator: str, period: str) -> list[dict[str, Any]]:
    meta = INDICATOR_AGGREGATES[indicator]
    url = (
        f"https://servicodados.ibge.gov.br/api/v3/agregados/{meta['aggregate']}"
        f"/periodos/{period}/variaveis/{meta['variable']}?localidades=N3[all]"
    )
    if meta.get("classificacao"):
        url += f"&classificacao={meta['classificacao']}"
    payload = cached_json(f"uf:{indicator}:{period}", url)
    series = payload[0]["resultados"][0]["series"]
    rows = []
    for item in series:
        raw = str(item["serie"][period]).replace(",", ".")
        if raw in {"", "...", "-", "X", "x"}:
            continue
        value = float(raw) if "." in raw or indicator != "population" else float(raw)
        if indicator == "population":
            value = float(str(item["serie"][period]).replace(".", "").replace(",", ""))
        if indicator == "pib":
            # mil reais -> BRL
            value = float(str(item["serie"][period]).replace(".", "").replace(",", "")) * 1000
        rows.append(
            {
                "ibge_code": str(item["localidade"]["id"]),
                "name": item["localidade"]["nome"],
                "value": value,
            }
        )
    return rows


def fetch_municipality_geo(uf_code: str) -> dict[str, Any]:
    url = (
        f"https://servicodados.ibge.gov.br/api/v3/malhas/estados/{uf_code}"
        f"?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=municipio"
    )
    return cached_json(f"malha:mun:{uf_code}", url)


def fetch_municipality_population(uf_code: str, period: str = "2025") -> list[dict[str, Any]]:
    url = (
        f"https://servicodados.ibge.gov.br/api/v3/agregados/6579/periodos/{period}"
        f"/variaveis/9324?localidades=N6[N3[{uf_code}]]"
    )
    payload = cached_json(f"pop:mun:{uf_code}:{period}", url)
    series = payload[0]["resultados"][0]["series"]
    rows = []
    for item in series:
        raw = str(item["serie"][period]).replace(".", "").replace(",", "")
        if raw in {"", "...", "-", "X", "x"}:
            continue
        rows.append(
            {
                "ibge_code": str(item["localidade"]["id"]),
                "name": item["localidade"]["nome"],
                "value": int(raw),
            }
        )
    return rows

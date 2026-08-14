"""Shared HTTP helpers for official open-data connectors."""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

USER_AGENT = "BrasilReal/0.1 (+educational-simulator; contact=local-dev)"
DEFAULT_TIMEOUT = 60


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def fixtures_dir() -> Path:
    return repo_root() / "data" / "fixtures"


def raw_dir() -> Path:
    path = repo_root() / "data" / "raw"
    path.mkdir(parents=True, exist_ok=True)
    return path


def fetch_bytes(
    url: str,
    *,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = 3,
    backoff_s: float = 1.5,
) -> bytes:
    import gzip

    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "*/*",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                # Some endpoints still return gzip bytes even after urllib handling.
                if raw[:2] == b"\x1f\x8b":
                    raw = gzip.decompress(raw)
                return raw
        except urllib.error.HTTPError as exc:
            last_err = exc
            if exc.code in {429, 500, 502, 503, 504} and attempt < retries - 1:
                time.sleep(backoff_s * (attempt + 1))
                continue
            raise
        except urllib.error.URLError as exc:
            last_err = exc
            if attempt < retries - 1:
                time.sleep(backoff_s * (attempt + 1))
                continue
            raise
    raise RuntimeError(f"fetch failed for {url}: {last_err}")


def fetch_json(url: str, **kwargs: Any) -> Any:
    raw = fetch_bytes(url, **kwargs)
    return json.loads(raw.decode("utf-8"))


def write_json(path: Path, payload: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def snapshot_raw(source: str, name: str, content: bytes, meta: dict[str, Any]) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    folder = raw_dir() / source / stamp
    folder.mkdir(parents=True, exist_ok=True)
    blob = folder / name
    blob.write_bytes(content)
    meta_path = folder / f"{name}.meta.json"
    meta = {
        **meta,
        "retrieved_at": utc_now(),
        "bytes": len(content),
        "checksum_sha256": hashlib.sha256(content).hexdigest(),
        "path": str(blob.relative_to(repo_root())),
    }
    write_json(meta_path, meta)
    return blob

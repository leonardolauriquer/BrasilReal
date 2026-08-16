from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.data_integrity import (
    DataIntegrityError,
    canonical_sha256,
    enforce_additive_totals,
    enforce_uf_coverage,
    inspect_write_payload,
    validate_disk_locks,
    validate_manifest,
)
from app.core.paths import fixtures_root
from app.schemas.observations import ObservationOut

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
from canary_api import run_canary  # noqa: E402
from check_contracts import main as check_contracts_main  # noqa: E402


def _row(**over):
    base = {
        "indicator": "population",
        "geography_ibge_code": "35",
        "uf": "SP",
        "name": "São Paulo",
        "value": 10,
        "unit": "habitantes",
        "reference_period": "2025-07-01",
        "status_label": "ESTIMADO",
        "definition": "População residente estimada pelo IBGE.",
        "source": {"organization": "IBGE", "dataset": "agregados-6579"},
        "dataset_id": "ibge.population.uf",
    }
    base.update(over)
    return base


def test_observation_schema_rejects_missing_definition():
    with pytest.raises(ValidationError):
        ObservationOut.model_validate(_row(definition=""))


def test_observation_schema_accepts_complete_row():
    out = ObservationOut.model_validate(_row())
    assert out.definition.startswith("População")
    assert out.source.organization == "IBGE"


def test_uf_coverage_wipes_incomplete_layer():
    rows = [_row(geography_ibge_code="35", uf="SP"), _row(geography_ibge_code="33", uf="RJ")]
    kept, dropped, ok = enforce_uf_coverage(rows, [], indicator="population", geography=None)
    assert kept == []
    assert ok is False
    assert dropped[0]["reason"].startswith("uf_coverage:")


def test_uf_coverage_allows_empty_or_single_geo():
    kept, dropped, ok = enforce_uf_coverage([], [], indicator="population", geography=None)
    assert kept == [] and ok is None and dropped == []
    one = [_row()]
    kept, dropped, ok = enforce_uf_coverage(one, [], indicator="population", geography="35")
    assert kept == one and ok is None


def test_additive_total_mismatch_wipes_layer():
    rows = [_row(value=10), _row(value=5, geography_ibge_code="33", uf="RJ")]
    kept, dropped, ok = enforce_additive_totals(
        rows, [], indicator="population", expected_total=999, field="brazil_total"
    )
    assert kept == []
    assert ok is False
    assert "brazil_total_mismatch" in dropped[0]["reason"]


def test_inspect_write_refuses_broken_population(tmp_path):
    payload = {"records": [], "brazil_total": 1, "source": {}}
    errors = inspect_write_payload(tmp_path / "population_uf_2099.json", payload)
    assert errors


def test_inspect_write_ignores_unrelated_json(tmp_path):
    assert inspect_write_payload(tmp_path / "notes.json", {"hello": True}) == []


def test_manifest_lock_matches_disk():
    root = fixtures_root()
    validate_disk_locks(root)
    assert validate_manifest(root) == []


def test_manifest_detects_tamper(tmp_path):
    src = fixtures_root() / "ibge" / "population_uf_2025.json"
    dest = tmp_path / "ibge"
    dest.mkdir()
    payload = json.loads(src.read_text(encoding="utf-8"))
    (dest / "population_uf_2025.json").write_text(json.dumps(payload), encoding="utf-8")
    copied = deepcopy(payload)
    copied["records"] = copied["records"][:26]
    copied["brazil_total"] = 1
    man = {
        "schema": "brasilreal.fixtures.manifest.v1",
        "files": {"ibge/population_uf_2025.json": {"sha256": canonical_sha256(copied)}},
        "layers": {},
    }
    (tmp_path / "MANIFEST.json").write_text(json.dumps(man), encoding="utf-8")
    errors = validate_manifest(tmp_path)
    assert any("sha256 mismatch" in e or "golden" in e or "missing" in e for e in errors)


def test_validate_disk_locks_raises_without_manifest(tmp_path):
    try:
        validate_disk_locks(tmp_path)
        assert False, "expected DataIntegrityError"
    except DataIntegrityError:
        pass


def test_contracts_aligned():
    assert check_contracts_main() == 0


def test_ingestion_write_json_refuses_bad_population(tmp_path):
    workers = ROOT / "workers" / "ingestion"
    if str(workers) not in sys.path:
        sys.path.insert(0, str(workers))
    from common import write_json  # noqa: E402

    dest = tmp_path / "population_uf_2099.json"
    with pytest.raises(RuntimeError, match="refusing to write"):
        write_json(dest, {"records": [], "brazil_total": 1, "source": {}})
    assert not dest.exists()


def test_canary_against_local_api(client):
    errors = run_canary(lambda path: client.get(path).json())
    assert errors == [], errors

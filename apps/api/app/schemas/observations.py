"""Pydantic observation envelope — unlabeled numbers cannot serialize."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator


class SourceOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    organization: str = Field(min_length=1)
    dataset: str = Field(min_length=1)
    url: str | None = None
    retrieved_at: str | None = None


class ObservationOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    indicator: str = Field(min_length=1)
    geography_ibge_code: str = Field(min_length=1)
    uf: str = Field(min_length=2, max_length=2)
    name: str = Field(min_length=1)
    value: float | int
    unit: str = Field(min_length=1)
    reference_period: str = Field(min_length=4)
    status_label: str = Field(min_length=1)
    definition: str = Field(min_length=8)
    source: SourceOut
    dataset_id: str = Field(min_length=1)
    release_date: str | None = None
    evidence_grade: str | None = None
    higher_is_worse: bool | None = None
    limitations: list[str] | None = None
    short_name: str | None = None
    label: str | None = None

    @field_validator("value")
    @classmethod
    def finite_value(cls, v: float | int) -> float | int:
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ValueError("value must be a finite number")
        if v != v or v in {float("inf"), float("-inf")}:
            raise ValueError("value must be finite")
        return v


class IntegrityMeta(BaseModel):
    model_config = ConfigDict(extra="allow")

    gated: StrictBool
    raw_count: int
    kept_count: int
    dropped_count: int
    dropped: list[dict[str, str]] = Field(default_factory=list)
    coverage_ok: bool | None = None
    population_reconcile_ok: bool | None = None
    pib_reconcile_ok: bool | None = None
    schema_rejected: int = 0


class ObservationsMeta(BaseModel):
    model_config = ConfigDict(extra="allow")

    integrity: IntegrityMeta
    requested_period: str | None = None
    resolved_period: str | None = None
    period_resolved: bool | None = None
    period_miss: bool = False
    live_fallback: bool = False
    live_error: Any = None
    freshness: Any = None
    population_brazil_total: int | None = None
    population_reference_date: str | None = None
    population_dataset_id: str | None = None
    population_checksum_sha256: str | None = None
    pib_brazil_total_brl: float | int | None = None
    pib_reference_period: str | None = None
    pib_dataset_id: str | None = None


class ObservationsResponse(BaseModel):
    count: int
    meta: ObservationsMeta
    items: list[ObservationOut]

"""Minimal TypedDict mirrors of packages/contracts/typescript/atlas.ts."""

from __future__ import annotations

from typing import NotRequired, TypedDict


class SourceInfo(TypedDict):
    organization: str
    dataset: str
    url: NotRequired[str]
    retrieved_at: NotRequired[str]


class Indicator(TypedDict):
    id: str
    name: str
    unit: str
    status_label: str
    short_name: NotRequired[str]
    kind: NotRequired[str]
    reference_period: NotRequired[str]
    higher_is_worse: NotRequired[bool]
    group: NotRequired[str]
    group_label: NotRequired[str]
    definition: NotRequired[str]
    source: NotRequired[SourceInfo]
    limitations: NotRequired[list[str]]


class Observation(TypedDict):
    indicator: str
    geography_ibge_code: str
    uf: str
    name: str
    value: float
    unit: str
    reference_period: str
    status_label: str
    source: SourceInfo
    dataset_id: str
    definition: str
    release_date: NotRequired[str | None]
    evidence_grade: NotRequired[str]
    higher_is_worse: NotRequired[bool]
    limitations: NotRequired[list[str]]
    short_name: NotRequired[str]
    label: NotRequired[str]

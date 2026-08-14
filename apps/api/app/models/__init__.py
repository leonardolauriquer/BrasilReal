"""SQLAlchemy models — schema mínimo do MVP (bitemporal-ready)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class SourceCatalog(Base):
    __tablename__ = "source_catalog"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    organization: Mapped[str] = mapped_column(String(200))
    dataset: Mapped[str] = mapped_column(String(200))
    url: Mapped[str] = mapped_column(Text)
    license_or_terms: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    frequency: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    access_method: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    owner: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)


class IngestionRun(Base):
    __tablename__ = "ingestion_run"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("source_catalog.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32))
    record_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    connector_version: Mapped[str] = mapped_column(String(64))
    content_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)


class SourceArtifact(Base):
    __tablename__ = "source_artifact"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("source_catalog.id"))
    canonical_url: Mapped[str] = mapped_column(Text)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    mime_type: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    checksum_sha256: Mapped[str] = mapped_column(String(64))
    storage_uri: Mapped[str] = mapped_column(Text)
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class Geography(Base):
    __tablename__ = "geography"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    ibge_code: Mapped[str] = mapped_column(String(16), index=True)
    level: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(200))
    uf: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    valid_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    valid_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)


class IndicatorDefinition(Base):
    __tablename__ = "indicator_definition"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    concept: Mapped[str] = mapped_column(String(200))
    unit: Mapped[str] = mapped_column(String(64))
    periodicity: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    method_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    limitations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Observation(Base):
    __tablename__ = "observation"
    __table_args__ = (
        UniqueConstraint(
            "geography_id",
            "indicator_id",
            "reference_period",
            "revision",
            name="uq_observation_revision",
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    geography_id: Mapped[str] = mapped_column(ForeignKey("geography.id"))
    indicator_id: Mapped[str] = mapped_column(ForeignKey("indicator_definition.id"))
    value: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    unit: Mapped[str] = mapped_column(String(64))
    reference_period: Mapped[str] = mapped_column(String(32))
    release_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revision: Mapped[int] = mapped_column(Integer, default=1)
    status_label: Mapped[str] = mapped_column(String(32))
    source_artifact_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("source_artifact.id"), nullable=True
    )


class LegalInstrument(Base):
    __tablename__ = "legal_instrument"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    urn_lexml: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    type: Mapped[str] = mapped_column(String(64))
    number: Mapped[str] = mapped_column(String(64))
    year: Mapped[int] = mapped_column(Integer)
    authority: Mapped[str] = mapped_column(String(120))
    title: Mapped[str] = mapped_column(Text)
    ementa: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    canonical_url: Mapped[str] = mapped_column(Text)
    computable_rules: Mapped[bool] = mapped_column(Boolean, default=False)


class Scenario(Base):
    __tablename__ = "scenario"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    author: Mapped[str] = mapped_column(String(120))
    baseline: Mapped[bool] = mapped_column(Boolean, default=False)
    cutoff_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(32))
    is_hypothetical: Mapped[bool] = mapped_column(Boolean, default=True)
    manifesto_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    patches: Mapped[list["ScenarioPatch"]] = relationship(back_populates="scenario")


class ScenarioPatch(Base):
    __tablename__ = "scenario_patch"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(ForeignKey("scenario.id"))
    path: Mapped[str] = mapped_column(String(120))
    value: Mapped[str] = mapped_column(Text)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    scenario: Mapped[Scenario] = relationship(back_populates="patches")


class SimulationRun(Base):
    __tablename__ = "simulation_run"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(ForeignKey("scenario.id"))
    seed: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32))
    model_id: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    result_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class AuditEvent(Base):
    __tablename__ = "audit_event"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    actor: Mapped[str] = mapped_column(String(120))
    action: Mapped[str] = mapped_column(String(120))
    target: Mapped[str] = mapped_column(String(200))
    before_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    after_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    correlation_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

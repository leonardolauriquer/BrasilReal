"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-14
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "source_catalog",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("organization", sa.String(length=200), nullable=False),
        sa.Column("dataset", sa.String(length=200), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("license_or_terms", sa.Text(), nullable=True),
        sa.Column("frequency", sa.String(length=64), nullable=True),
        sa.Column("access_method", sa.String(length=64), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("owner", sa.String(length=120), nullable=True),
    )
    op.create_table(
        "ingestion_run",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("source_id", sa.String(length=64), sa.ForeignKey("source_catalog.id")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("record_count", sa.Integer(), server_default="0"),
        sa.Column("error_count", sa.Integer(), server_default="0"),
        sa.Column("connector_version", sa.String(length=64), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=True),
    )
    op.create_table(
        "source_artifact",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("source_id", sa.String(length=64), sa.ForeignKey("source_catalog.id")),
        sa.Column("canonical_url", sa.Text(), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("mime_type", sa.String(length=120), nullable=True),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("storage_uri", sa.Text(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
    )
    op.create_table(
        "geography",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("ibge_code", sa.String(length=16), nullable=False, index=True),
        sa.Column("level", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("uf", sa.String(length=2), nullable=True),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_to", sa.Date(), nullable=True),
    )
    op.create_table(
        "indicator_definition",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("concept", sa.String(length=200), nullable=False),
        sa.Column("unit", sa.String(length=64), nullable=False),
        sa.Column("periodicity", sa.String(length=64), nullable=True),
        sa.Column("method_notes", sa.Text(), nullable=True),
        sa.Column("limitations", sa.Text(), nullable=True),
    )
    op.create_table(
        "observation",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("geography_id", sa.String(length=64), sa.ForeignKey("geography.id")),
        sa.Column("indicator_id", sa.String(length=64), sa.ForeignKey("indicator_definition.id")),
        sa.Column("value", sa.Numeric(20, 6), nullable=False),
        sa.Column("unit", sa.String(length=64), nullable=False),
        sa.Column("reference_period", sa.String(length=32), nullable=False),
        sa.Column("release_date", sa.Date(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revision", sa.Integer(), server_default="1"),
        sa.Column("status_label", sa.String(length=32), nullable=False),
        sa.Column("source_artifact_id", sa.String(length=64), sa.ForeignKey("source_artifact.id"), nullable=True),
        sa.UniqueConstraint(
            "geography_id",
            "indicator_id",
            "reference_period",
            "revision",
            name="uq_observation_revision",
        ),
    )
    op.create_table(
        "legal_instrument",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("urn_lexml", sa.String(length=255), nullable=True),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("number", sa.String(length=64), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("authority", sa.String(length=120), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("ementa", sa.Text(), nullable=True),
        sa.Column("canonical_url", sa.Text(), nullable=False),
        sa.Column("computable_rules", sa.Boolean(), server_default=sa.text("false")),
    )
    op.create_table(
        "scenario",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("author", sa.String(length=120), nullable=False),
        sa.Column("baseline", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("cutoff_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("is_hypothetical", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("manifesto_json", sa.Text(), nullable=True),
    )
    op.create_table(
        "scenario_patch",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("scenario_id", sa.String(length=64), sa.ForeignKey("scenario.id")),
        sa.Column("path", sa.String(length=120), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "simulation_run",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("scenario_id", sa.String(length=64), sa.ForeignKey("scenario.id")),
        sa.Column("seed", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("model_id", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("result_json", sa.Text(), nullable=True),
    )
    op.create_table(
        "audit_event",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("actor", sa.String(length=120), nullable=False),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("target", sa.String(length=200), nullable=False),
        sa.Column("before_json", sa.Text(), nullable=True),
        sa.Column("after_json", sa.Text(), nullable=True),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("correlation_id", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    for table in [
        "audit_event",
        "simulation_run",
        "scenario_patch",
        "scenario",
        "legal_instrument",
        "observation",
        "indicator_definition",
        "geography",
        "source_artifact",
        "ingestion_run",
        "source_catalog",
    ]:
        op.drop_table(table)

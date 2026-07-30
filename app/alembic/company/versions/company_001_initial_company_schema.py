"""Initial company schema

Revision ID: 001
Revises:
Create Date: 2026-07-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "company_001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = ("company",)
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS company")

    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("website", sa.String(), nullable=True),
        sa.Column("domain", sa.String(), nullable=True),
        sa.Column("industry", sa.String(), nullable=True),
        sa.Column("country", sa.String(), nullable=True),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("company_size", sa.String(), nullable=True),
        sa.Column("company_type", sa.String(), nullable=True),
        sa.Column("logo_url", sa.String(), nullable=True),
        sa.Column("founded_year", sa.String(), nullable=True),
        sa.Column("headquarters_full", sa.String(), nullable=True),
        sa.Column("countries_of_operation", sa.Text(), nullable=True),
        sa.Column("funding_stage", sa.String(), nullable=True),
        sa.Column("funding_amount", sa.String(), nullable=True),
        sa.Column("products", sa.Text(), nullable=True),
        sa.Column("tech_stack", sa.Text(), nullable=True),
        sa.Column("work_environment", sa.Text(), nullable=True),
        sa.Column("extra", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), server_default="[]"),
        sa.Column("links", sa.Text(), server_default="[]"),
        sa.Column("source", sa.String(), server_default="web"),
        sa.Column("workflow_log", sa.Text(), server_default="[]"),
        sa.Column("input_text", sa.Text(), nullable=True),
        sa.Column("input_type", sa.String(), server_default="url"),
        sa.Column("status", sa.String(), server_default="pending"),
        sa.Column("created_at", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.Text(), nullable=True),
        sa.Column("queue_order", sa.Integer(), server_default="0"),
        sa.Column("current_node", sa.String(), nullable=True),
        sa.Column("progress_pct", sa.Integer(), server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), server_default="0"),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("failure_step", sa.String(), nullable=True),
        sa.Column("failure_timestamp", sa.String(), nullable=True),
        sa.Column("session_id", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="company",
    )
    op.create_index("idx_companies_name", "companies", ["name"], schema="company")
    op.create_index("idx_companies_status", "companies", ["status"], schema="company")

    op.create_table(
        "company_intelligence",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("company.companies.id"), nullable=False),
        sa.Column("overview", sa.Text(), nullable=True),
        sa.Column("culture_analysis", sa.Text(), nullable=True),
        sa.Column("international_analysis", sa.Text(), nullable=True),
        sa.Column("career_analysis", sa.Text(), nullable=True),
        sa.Column("benefits_analysis", sa.Text(), nullable=True),
        sa.Column("visa_analysis", sa.Text(), nullable=True),
        sa.Column("technology_analysis", sa.Text(), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("scores", sa.Text(), nullable=True),
        sa.Column("raw_source_data", sa.Text(), nullable=True),
        sa.Column("generated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="company",
    )
    op.create_index(
        "idx_company_intelligence_company_id",
        "company_intelligence",
        ["company_id"],
        schema="company",
    )

    op.create_table(
        "company_links",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("company.companies.id"), nullable=False),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("extracted_content", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="company",
    )
    op.create_index(
        "idx_company_links_company_id",
        "company_links",
        ["company_id"],
        schema="company",
    )


def downgrade() -> None:
    op.drop_table("company_links", schema="company")
    op.drop_table("company_intelligence", schema="company")
    op.drop_table("companies", schema="company")
    op.execute("DROP SCHEMA IF EXISTS company")
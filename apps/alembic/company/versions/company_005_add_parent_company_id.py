"""Add parent_company_id to companies (main/related company relations).

A company with a parent_company_id is a near-duplicate ("alias") of its main
company. The main company is the single reference for display and further
processing; relating an alias re-points its jobs to the main.

Revision ID: company_005_add_parent_company_id
Revises: company_004_sync_sequences
Create Date: 2026-08-06
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "company_005_add_parent_company_id"
down_revision: Union[str, None] = "company_004_sync_sequences"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "companies",
        sa.Column("parent_company_id", sa.String(36), nullable=True),
        schema="company",
    )
    op.create_foreign_key(
        "fk_company_parent_company_id",
        "companies",
        "companies",
        ["parent_company_id"],
        ["id"],
        source_schema="company",
        referent_schema="company",
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_company_parent_company_id",
        "companies",
        ["parent_company_id"],
        schema="company",
    )


def downgrade() -> None:
    op.drop_index("ix_company_parent_company_id", table_name="companies", schema="company")
    op.drop_constraint("fk_company_parent_company_id", "companies", schema="company")
    op.drop_column("companies", "parent_company_id", schema="company")

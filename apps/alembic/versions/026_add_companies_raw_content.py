"""Add raw_content column to companies.

Mirror of jobs.raw_description: the company context preparation phase
persists the prepared combined_text here so the analysis phase has a durable
LLM input even though the in-memory workflow context is not persisted.

Revision ID: 026_add_companies_raw_content
Revises: 025_add_workflow_progress
Create Date: 2026-08-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '026_add_companies_raw_content'
down_revision: Union[str, None] = '025_add_workflow_progress'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "companies",
        sa.Column("raw_content", sa.Text, nullable=True),
        schema="company",
    )


def downgrade() -> None:
    op.drop_column("companies", "raw_content", schema="company")

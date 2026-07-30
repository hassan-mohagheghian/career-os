"""Add processing_executions table.

Revision ID: 023_add_processing_executions
Revises: 022_rename_preferences_to_rules
Create Date: 2026-07-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '023_add_processing_executions'
down_revision: Union[str, None] = '022_rename_preferences_to_rules'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS processing")
    op.create_table(
        "processing_executions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("execution_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="created"),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("target_id", sa.String(255), nullable=False),
        sa.Column("created_at", sa.Text, nullable=True),
        sa.Column("started_at", sa.Text, nullable=True),
        sa.Column("finished_at", sa.Text, nullable=True),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text, nullable=True),
        schema="processing",
    )


def downgrade() -> None:
    op.drop_table("processing_executions", schema="processing")

"""Initial processing schema and processing_executions table.

Branch root for the `processing` context (mirrors company_001). Creates the
`processing` schema and the `processing_executions` table. Idempotent so it is
safe to (re)apply on a database that already has the table.

Revision ID: 023_add_processing_executions
Revises:
Create Date: 2026-07-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = '023_add_processing_executions'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = ('processing',)
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS processing")
    bind = op.get_bind()
    insp = inspect(bind)
    if not insp.has_table("processing_executions", schema="processing"):
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
    bind = op.get_bind()
    insp = inspect(bind)
    if insp.has_table("processing_executions", schema="processing"):
        op.drop_table("processing_executions", schema="processing")

"""Add heartbeat_at column to processing_executions.

Worker heartbeat for reconcile stale detection: the runner updates this
timestamp periodically so reconcile_stuck_executions can distinguish
active workers from crashed ones.

Revision ID: processing_001_add_heartbeat_at
Revises: 023_add_processing_executions
Create Date: 2026-08-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = 'processing_001_add_heartbeat_at'
down_revision: Union[str, None] = '023_add_processing_executions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS processing")
    bind = op.get_bind()
    insp = inspect(bind)
    if not insp.has_column("processing_executions", "heartbeat_at", schema="processing"):
        op.add_column(
            "processing_executions",
            sa.Column("heartbeat_at", sa.Text, nullable=True),
            schema="processing",
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if insp.has_column("processing_executions", "heartbeat_at", schema="processing"):
        op.drop_column("processing_executions", "heartbeat_at", schema="processing")

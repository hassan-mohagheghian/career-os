"""Add workflow_progress column to processing_executions.

Revision ID: 025_add_workflow_progress
Revises: 024_add_uuid_v7_to_jobs
Create Date: 2026-08-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '025_add_workflow_progress'
down_revision: Union[str, None] = '024_add_uuid_v7_to_jobs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "processing_executions",
        sa.Column("workflow_progress", sa.Text, nullable=True),
        schema="processing",
    )


def downgrade() -> None:
    op.drop_column("processing_executions", "workflow_progress", schema="processing")

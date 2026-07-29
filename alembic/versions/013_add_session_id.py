"""Add missing session_id column to pending_companies.

The baseline migration created pending_jobs and pending_generations with a
session_id column but omitted it for pending_companies. The SQLAlchemy
model has the column, causing OperationalError when querying.

Revision ID: 013_add_session_id
Revises: 012_job_lifecycle
Create Date: 2026-07-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = '013_add_session_id'
down_revision: Union[str, None] = '012_job_lifecycle'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(table: str, column: str) -> bool:
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [c["name"] for c in inspector.get_columns(table)]
    return column in columns


def upgrade() -> None:
    if not column_exists('pending_companies', 'session_id'):
        with op.batch_alter_table('pending_companies') as batch_op:
            batch_op.add_column(sa.Column('session_id', sa.String(), nullable=True))
    else:
        pass


def downgrade() -> None:
    if column_exists('pending_companies', 'session_id'):
        with op.batch_alter_table('pending_companies') as batch_op:
            batch_op.drop_column('session_id')

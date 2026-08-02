"""Add tracking columns to pending_companies.

Adds previous_status, current_node, retry_count, failure_details
to pending_companies matching PendingJobModel's schema after the
012 job lifecycle refactor.

Revision ID: 015_add_company_tracking
Revises: 014_migrate_company_statuses
Create Date: 2026-07-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '015_add_company_tracking'
down_revision: Union[str, None] = '014_migrate_company_statuses'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('pending_companies') as batch_op:
        batch_op.add_column(sa.Column('previous_status', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('current_node', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('retry_count', sa.Integer(), server_default='0'))
        batch_op.add_column(sa.Column('failure_details', sa.Text(), nullable=True))

    # Set previous_status from current status for existing rows
    pending_companies = sa.table('pending_companies', sa.column('previous_status'), sa.column('status'))
    op.execute(
        sa.update(pending_companies).where(pending_companies.c.previous_status.is_(None))
        .values(previous_status=pending_companies.c.status)
    )


def downgrade() -> None:
    with op.batch_alter_table('pending_companies') as batch_op:
        batch_op.drop_column('failure_details')
        batch_op.drop_column('retry_count')
        batch_op.drop_column('current_node')
        batch_op.drop_column('previous_status')

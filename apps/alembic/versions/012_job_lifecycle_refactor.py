"""Job lifecycle refactor: new statuses and tracking columns.

Adds columns for the new explicit JobStatus state machine:
- previous_status, current_node, retry_count, failure_details, auto_process

Migrates existing status values:
- pending    → created
- queued     → queued (unchanged)
- processing → starting (orphans) / fetching (active)
- paused     → waiting
- done       → completed
- failed     → failed (unchanged)

Revision ID: 012_job_lifecycle
Revises: initial
Create Date: 2026-07-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '012_job_lifecycle'
down_revision: Union[str, None] = 'initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


OLD_TO_NEW_STATUS = {
    'pending': 'created',
    'queued': 'queued',
    'processing': 'fetching',
    'paused': 'waiting',
    'done': 'completed',
    'failed': 'failed',
}


def upgrade() -> None:
    pending_jobs = sa.table('pending_jobs', sa.column('status'))

    # ── Migrate existing status values first ───────────────────────
    for old_status, new_status in OLD_TO_NEW_STATUS.items():
        if old_status != new_status:
            op.execute(
                sa.update(pending_jobs).where(pending_jobs.c.status == old_status)
                .values(status=new_status)
            )

    # Orphaned 'processing' items that were stuck go to 'created'
    op.execute(
        sa.update(pending_jobs).where(pending_jobs.c.status == 'processing')
        .values(status='created')
    )

    # ── Add new columns to pending_jobs ────────────────────────────
    with op.batch_alter_table('pending_jobs') as batch_op:
        batch_op.add_column(sa.Column('previous_status', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('current_node', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('retry_count', sa.Integer(), server_default='0'))
        batch_op.add_column(sa.Column('failure_details', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('auto_process', sa.Integer(), server_default='1'))

    # ── Set previous_status from old status values ─────────────────
    pending_jobs_ext = sa.table('pending_jobs', sa.column('status'), sa.column('previous_status'))
    for old_status, new_status in OLD_TO_NEW_STATUS.items():
        if old_status != new_status:
            op.execute(
                sa.update(pending_jobs_ext).where(
                    sa.and_(pending_jobs_ext.c.status == new_status, pending_jobs_ext.c.previous_status.is_(None))
                ).values(previous_status=old_status)
            )

    op.execute(
        sa.update(pending_jobs_ext).where(
            sa.and_(pending_jobs_ext.c.status == 'created', pending_jobs_ext.c.previous_status.is_(None))
        ).values(previous_status='processing')
    )

    # ── Add index on status for faster queries ─────────────────────
    with op.batch_alter_table('pending_jobs') as batch_op:
        batch_op.create_index('idx_pending_jobs_status', ['status'])


def downgrade() -> None:
    # ── Drop index first ───────────────────────────────────────────
    with op.batch_alter_table('pending_jobs') as batch_op:
        batch_op.drop_index('idx_pending_jobs_status')

    # ── Revert status values ───────────────────────────────────────
    NEW_TO_OLD_STATUS = {v: k for k, v in OLD_TO_NEW_STATUS.items()}

    pending_jobs_downgrade = sa.table('pending_jobs', sa.column('status'))
    for new_status, old_status in NEW_TO_OLD_STATUS.items():
        if new_status != old_status:
            op.execute(
                sa.update(pending_jobs_downgrade).where(pending_jobs_downgrade.c.status == new_status)
                .values(status=old_status)
            )

    # Handle statuses that don't have a direct old mapping
    for extra_status in ('starting', 'analyzing', 'generating', 'finalizing', 'cancelled', 'waiting'):
        op.execute(
            sa.update(pending_jobs_downgrade).where(pending_jobs_downgrade.c.status == extra_status)
            .values(status='pending')
        )

    # ── Drop new columns ───────────────────────────────────────────
    with op.batch_alter_table('pending_jobs') as batch_op:
        batch_op.drop_column('auto_process')
        batch_op.drop_column('failure_details')
        batch_op.drop_column('retry_count')
        batch_op.drop_column('current_node')
        batch_op.drop_column('previous_status')

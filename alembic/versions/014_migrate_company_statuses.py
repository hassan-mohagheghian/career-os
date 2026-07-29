"""Migrate pending_companies status values to match new JobStatus enum.

The 012 migration only converted pending_jobs statuses. pending_companies
still has old values: pending, processing, paused, done.

Old → New mapping:
  pending    → created
  queued     → queued (unchanged)
  processing → starting  (orphans → starting)
  paused     → waiting
  done       → completed
  failed     → failed (unchanged)

Revision ID: 014_migrate_company_statuses
Revises: 013_add_session_id
Create Date: 2026-07-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '014_migrate_company_statuses'
down_revision: Union[str, None] = '013_add_session_id'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


OLD_TO_NEW_STATUS = {
    'pending': 'created',
    'queued': 'queued',
    'processing': 'starting',
    'paused': 'waiting',
    'done': 'completed',
    'failed': 'failed',
}


def upgrade() -> None:
    for old_status, new_status in OLD_TO_NEW_STATUS.items():
        if old_status != new_status:
            op.execute(
                sa.text(
                    "UPDATE pending_companies SET status = :new WHERE status = :old"
                ).bindparams(new=new_status, old=old_status)
            )


def downgrade() -> None:
    NEW_TO_OLD_STATUS = {v: k for k, v in OLD_TO_NEW_STATUS.items()}

    for new_status, old_status in NEW_TO_OLD_STATUS.items():
        if new_status != old_status:
            op.execute(
                sa.text(
                    "UPDATE pending_companies SET status = :old WHERE status = :new"
                ).bindparams(old=old_status, new=new_status)
            )

    # Handle statuses that don't have a direct old mapping
    for extra_status in ('analyzing', 'generating', 'finalizing', 'cancelled'):
        op.execute(
            sa.text(
                "UPDATE pending_companies SET status = 'pending' WHERE status = :extra"
            ).bindparams(extra=extra_status)
        )

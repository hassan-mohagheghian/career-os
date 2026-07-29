"""Add worker data columns to jobs and companies.

- Add links, source to jobs
- Add notes, links, source, workflow_log to companies

Revision ID: 017_add_worker_data_columns
Revises: 016_remove_processing_module
Create Date: 2026-07-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '017_add_worker_data_columns'
down_revision: Union[str, None] = '016_remove_processing_module'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('jobs') as batch_op:
        batch_op.add_column(sa.Column('links', sa.Text(), server_default='[]'))
        batch_op.add_column(sa.Column('source', sa.Text(), server_default='web'))

    with op.batch_alter_table('companies') as batch_op:
        batch_op.add_column(sa.Column('notes', sa.Text(), server_default='[]'))
        batch_op.add_column(sa.Column('links', sa.Text(), server_default='[]'))
        batch_op.add_column(sa.Column('source', sa.Text(), server_default='web'))
        batch_op.add_column(sa.Column('workflow_log', sa.Text(), server_default='[]'))


def downgrade() -> None:
    with op.batch_alter_table('jobs') as batch_op:
        batch_op.drop_column('source')
        batch_op.drop_column('links')

    with op.batch_alter_table('companies') as batch_op:
        batch_op.drop_column('workflow_log')
        batch_op.drop_column('source')
        batch_op.drop_column('links')
        batch_op.drop_column('notes')

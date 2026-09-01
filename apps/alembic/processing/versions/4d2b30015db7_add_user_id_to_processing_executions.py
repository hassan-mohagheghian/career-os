"""add user_id to processing_executions

Revision ID: 4d2b30015db7
Revises: 47a6df55e081
Create Date: 2026-09-01 23:09:17.007033

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '4d2b30015db7'
down_revision: Union[str, None] = '47a6df55e081'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS processing")
    op.add_column(
        'processing_executions',
        sa.Column('user_id', sa.String(36), nullable=False, server_default=''),
        schema='processing',
    )
    op.create_index(
        op.f('ix_processing_processing_executions_user_id'),
        'processing_executions',
        ['user_id'],
        unique=False,
        schema='processing',
    )


def downgrade() -> None:
    op.drop_index(
        op.f('ix_processing_processing_executions_user_id'),
        table_name='processing_executions',
        schema='processing',
    )
    op.drop_column('processing_executions', 'user_id', schema='processing')

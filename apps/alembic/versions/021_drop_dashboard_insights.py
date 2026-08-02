"""Drop dashboard_insights table (orphaned after restore).

Revision ID: 021_drop_dashboard_insights
Revises: 020_drop_tech_learning_table
Create Date: 2026-07-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '021_drop_dashboard_insights'
down_revision: Union[str, None] = '020_drop_tech_learning_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('dashboard_insights')


def downgrade() -> None:
    op.create_table(
        'dashboard_insights',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('type', sa.Text(), nullable=False),
        sa.Column('icon', sa.Text(), nullable=True),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', sa.Integer(), server_default='0'),
        sa.Column('updated_at', sa.Text(), nullable=True),
    )

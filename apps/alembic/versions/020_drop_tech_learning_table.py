"""Drop unused tech_learning table.

Revision ID: 020_drop_tech_learning_table
Revises: 019_drop_skill_topic_tables
Create Date: 2026-07-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '020_drop_tech_learning_table'
down_revision: Union[str, None] = '019_drop_skill_topic_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('tech_learning')


def downgrade() -> None:
    op.create_table(
        'tech_learning',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('pl', sa.String(), nullable=True),
        sa.Column('pc', sa.String(), nullable=True),
        sa.Column('sc', sa.String(), nullable=True),
        sa.Column('dc', sa.String(), nullable=True),
        sa.Column('usage', sa.Integer(), nullable=True),
        sa.Column('uc', sa.String(), nullable=True),
        sa.Column('jobs', sa.Text(), nullable=True),
        sa.Column('jd', sa.Text(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('action', sa.Text(), nullable=True),
    )

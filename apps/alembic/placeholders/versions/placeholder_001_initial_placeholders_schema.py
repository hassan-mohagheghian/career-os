"""add placeholders table

Revision ID: placeholder_001
Revises: application_005
Create Date: 2026-08-19 22:59:59.875263

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'placeholder_001'
down_revision: Union[str, None] = 'application_005'
branch_labels: Union[str, Sequence[str], None] = ('placeholders',)
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS placeholders")
    op.create_table('placeholders',
    sa.Column('key', sa.String(length=64), nullable=False),
    sa.Column('value', sa.Text(), nullable=False),
    sa.Column('updated_at', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('key', name=op.f('pk_placeholders')),
    schema='placeholders'
    )


def downgrade() -> None:
    op.drop_table('placeholders', schema='placeholders')

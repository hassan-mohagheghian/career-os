"""add pinned flag to companies

Revision ID: 5b6c673f3d38
Revises: 9d29b936826b
Create Date: 2026-08-06 20:08:13.131978

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b6c673f3d38'
down_revision: Union[str, None] = '9d29b936826b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('companies', sa.Column('pinned', sa.Integer(), nullable=False, server_default='0'), schema='company')


def downgrade() -> None:
    op.drop_column('companies', 'pinned', schema='company')

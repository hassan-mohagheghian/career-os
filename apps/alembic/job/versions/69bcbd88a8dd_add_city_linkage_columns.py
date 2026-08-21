"""add city linkage columns to jobs

Revision ID: 69bcbd88a8dd
Revises: city_001
Create Date: 2026-08-20 09:23:18.293825

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '69bcbd88a8dd'
down_revision: Union[str, None] = 'city_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('jobs', sa.Column('city_id', sa.String(length=36), nullable=True), schema='job')
    op.add_column('jobs', sa.Column('city', sa.String(), nullable=True), schema='job')
    op.add_column('jobs', sa.Column('country', sa.String(), nullable=True), schema='job')


def downgrade() -> None:
    op.drop_column('jobs', 'country', schema='job')
    op.drop_column('jobs', 'city', schema='job')
    op.drop_column('jobs', 'city_id', schema='job')

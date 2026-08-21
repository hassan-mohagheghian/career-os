"""add hidden and city aliases

Revision ID: c3cbd31cd041
Revises: da0d4ba7154d
Create Date: 2026-08-20 17:04:15.398245

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3cbd31cd041'
down_revision: Union[str, None] = 'da0d4ba7154d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Soft-hide flag so merged-away cities keep their lineage (Skills pattern).
    op.add_column(
        'cities',
        sa.Column('hidden', sa.Integer(), server_default='0', nullable=False),
        schema='city',
    )
    op.create_table(
        'city_aliases',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('city_id', sa.String(length=36), nullable=False),
        sa.Column('alias_name', sa.String(), nullable=False),
        sa.Column('normalized_name', sa.String(), server_default='', nullable=False),
        sa.Column('created_at', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ['city_id'], ['city.cities.id'], name=op.f('fk_city_aliases_city_id_cities')
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_city_aliases')),
        schema='city',
    )


def downgrade() -> None:
    op.drop_table('city_aliases', schema='city')
    op.drop_column('cities', 'hidden', schema='city')
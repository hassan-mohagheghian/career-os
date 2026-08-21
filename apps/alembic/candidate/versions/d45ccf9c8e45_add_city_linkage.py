"""add city linkage to candidate profiles

Revision ID: d45ccf9c8e45
Revises: 2cdcda32cae0
Create Date: 2026-08-20 09:24:06.126822

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd45ccf9c8e45'
down_revision: Union[str, None] = '2cdcda32cae0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('candidate_profiles', sa.Column('city', sa.String(), nullable=False, server_default=''), schema='candidate')
    op.add_column('candidate_profiles', sa.Column('country', sa.String(), nullable=False, server_default=''), schema='candidate')
    op.add_column('candidate_profiles', sa.Column('original_text', sa.String(), nullable=False, server_default=''), schema='candidate')
    op.add_column('candidate_profiles', sa.Column('address', sa.String(), nullable=False, server_default=''), schema='candidate')
    op.add_column('candidate_profiles', sa.Column('city_id', sa.String(length=36), nullable=True), schema='candidate')


def downgrade() -> None:
    op.drop_column('candidate_profiles', 'city_id', schema='candidate')
    op.drop_column('candidate_profiles', 'address', schema='candidate')
    op.drop_column('candidate_profiles', 'original_text', schema='candidate')
    op.drop_column('candidate_profiles', 'country', schema='candidate')
    op.drop_column('candidate_profiles', 'city', schema='candidate')

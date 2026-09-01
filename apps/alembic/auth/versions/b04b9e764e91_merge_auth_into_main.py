"""merge auth into main

Revision ID: b04b9e764e91
Revises: auth_001, job_008
Create Date: 2026-09-01 17:21:48.013653

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b04b9e764e91'
down_revision: Union[str, None] = ('auth_001', 'job_008')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

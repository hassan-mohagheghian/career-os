"""merge ai into main

Revision ID: 38f645e2256c
Revises: efaf28c67af2
Create Date: 2026-09-02 07:47:35.585669

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '38f645e2256c'
down_revision: Union[str, None] = 'efaf28c67af2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

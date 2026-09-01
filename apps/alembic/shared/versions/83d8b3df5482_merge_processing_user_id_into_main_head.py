"""merge processing user_id into main head

Revision ID: 83d8b3df5482
Revises: multi_001, 4d2b30015db7
Create Date: 2026-09-01 23:12:19.309272

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '83d8b3df5482'
down_revision: Union[str, None] = ('multi_001', '4d2b30015db7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

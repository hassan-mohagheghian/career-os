"""merge processing branch into main head

Revision ID: 47a6df55e081
Revises: processing_001_add_heartbeat_at, 0a497bf191e2
Create Date: 2026-08-28 13:10:39.327772

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '47a6df55e081'
down_revision: Union[str, None] = ('processing_001_add_heartbeat_at', '0a497bf191e2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

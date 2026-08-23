"""merge job_007 and skill_003

Revision ID: 0a497bf191e2
Revises: job_007, skill_003
Create Date: 2026-08-23 14:31:29.195149

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0a497bf191e2'
down_revision: Union[str, None] = ('job_007', 'skill_003')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

"""merge context heads

Revision ID: b54e0ddc0786
Revises: job_001, company_001, skill_001, shared_002
Create Date: 2026-08-02 12:12:34.643513

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b54e0ddc0786'
down_revision: Union[str, None] = ('job_001', 'company_001', 'skill_001', 'shared_002')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

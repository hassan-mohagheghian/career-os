"""merge job_companies and company head

Revision ID: cfb9c0c021da
Revises: 5b6c673f3d38, job_005_add_job_companies
Create Date: 2026-08-06 21:05:18.801638

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cfb9c0c021da'
down_revision: Union[str, None] = ('5b6c673f3d38', 'job_005_add_job_companies')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

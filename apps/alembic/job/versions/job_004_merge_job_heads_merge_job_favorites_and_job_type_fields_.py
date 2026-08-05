"""merge job favorites and job type fields heads

Revision ID: job_004_merge_job_heads
Revises: 026_consolidate_job_type_fields, job_003_add_job_favorite
Create Date: 2026-08-05 09:14:58.501107

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'job_004_merge_job_heads'
down_revision: Union[str, None] = ('026_consolidate_job_type_fields', 'job_003_add_job_favorite')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

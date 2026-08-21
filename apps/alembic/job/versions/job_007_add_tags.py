"""add tags column

User-defined tags stored as a JSON array of strings on the jobs table.
Enables categorization and multi-select filtering by custom labels.

Revision ID: job_007
Revises: job_006
Create Date: 2026-08-21 20:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "job_007"
down_revision: Union[str, None] = "job_006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("tags", sa.Text(), nullable=False, server_default="[]"), schema="job")


def downgrade() -> None:
    op.drop_column("jobs", "tags", schema="job")

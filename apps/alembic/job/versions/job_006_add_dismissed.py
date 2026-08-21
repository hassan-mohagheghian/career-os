"""add dismissed flag

Job-level dismiss flag lets the user ignore a recommended job (hidden from
the list by default, reviewable via a "Show dismissed" toggle).  Mirrors the
``pinned`` flag pattern.  Column lives in the ``job`` schema.

Revision ID: job_006
Revises: application_006
Create Date: 2026-08-21 18:45:56.591142
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "job_006"
down_revision: Union[str, None] = "application_006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("dismissed", sa.Integer(), nullable=False, server_default="0"), schema="job")


def downgrade() -> None:
    op.drop_column("jobs", "dismissed", schema="job")

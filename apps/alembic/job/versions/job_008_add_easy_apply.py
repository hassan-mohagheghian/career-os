"""add easy_apply column

Boolean flag indicating the job offers LinkedIn Easy Apply (apply directly
through LinkedIn without leaving the platform). Detected during content
extraction when the fetched page text contains "Easy Apply".

Revision ID: job_008
Revises: 47a6df55e081
Create Date: 2026-09-01 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "job_008"
down_revision: Union[str, None] = "47a6df55e081"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS job")
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {c["name"] for c in inspector.get_columns("jobs", schema="job")}
    if "easy_apply" not in columns:
        op.add_column("jobs", sa.Column("easy_apply", sa.Integer(), nullable=True), schema="job")


def downgrade() -> None:
    op.drop_column("jobs", "easy_apply", schema="job")

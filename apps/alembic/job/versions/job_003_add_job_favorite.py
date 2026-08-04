"""add favorite column to jobs

Revision ID: job_003_add_job_favorite
Revises: 42c200d12fd5
Create Date: 2026-08-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'job_003_add_job_favorite'
down_revision: Union[str, None] = '42c200d12fd5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(bind, table: str, schema: str, column: str) -> bool:
    inspector = sa.inspect(bind)
    if not inspector.has_table(table, schema=schema):
        return False
    columns = {c["name"] for c in inspector.get_columns(table, schema=schema)}
    return column in columns


def upgrade() -> None:
    bind = op.get_bind()
    if _column_exists(bind, "jobs", "job", "favorite"):
        return
    op.add_column(
        "jobs",
        sa.Column("favorite", sa.Integer(), nullable=False, server_default="0"),
        schema="job",
    )


def downgrade() -> None:
    bind = op.get_bind()
    if _column_exists(bind, "jobs", "job", "favorite"):
        op.drop_column("jobs", "favorite", schema="job")

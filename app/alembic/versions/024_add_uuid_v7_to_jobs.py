"""Add UUID v7 id column to jobs table.

Revision ID: 024_add_uuid_v7_to_jobs
Revises: 023_add_processing_executions
Create Date: 2026-07-31
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '024_add_uuid_v7_to_jobs'
down_revision: Union[str, None] = '023_add_processing_executions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _generate_uuid_v7() -> str:
    """Generate a UUIDv7 string."""
    import uuid
    return str(uuid.uuid7())


def upgrade() -> None:
    # Add the column as nullable initially
    op.add_column(
        "jobs",
        sa.Column("id", sa.String(36), nullable=True),
        schema="job",
    )

    # Backfill UUIDv7 for existing rows
    conn = op.get_bind()
    jobs_table = sa.table(
        "jobs",
        sa.Column("num", sa.Integer),
        sa.Column("id", sa.String(36)),
        schema="job",
    )
    rows = conn.execute(
        sa.select(jobs_table.c.num).where(jobs_table.c.id.is_(None))
    ).fetchall()

    for (num,) in rows:
        conn.execute(
            sa.update(jobs_table)
            .where(jobs_table.c.num == num)
            .values(id=_generate_uuid_v7())
        )

    # Now make it NOT NULL and add unique index
    op.alter_column(
        "jobs",
        "id",
        nullable=False,
        schema="job",
    )
    op.create_index(
        "ix_jobs_id",
        "jobs",
        ["id"],
        unique=True,
        schema="job",
    )


def downgrade() -> None:
    op.drop_index("ix_jobs_id", table_name="jobs", schema="job")
    op.drop_column("jobs", "id", schema="job")

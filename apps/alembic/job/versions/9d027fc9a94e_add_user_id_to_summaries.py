"""add user_id to summaries

Revision ID: 9d027fc9a94e
Revises: 38f645e2256c
Create Date: 2026-09-02 07:47:56.635638

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9d027fc9a94e"
down_revision: Union[str, None] = "38f645e2256c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("summaries", schema="job")}
    if "user_id" not in cols:
        op.add_column(
            "summaries",
            sa.Column("user_id", sa.String(36), nullable=False, server_default=""),
            schema="job",
        )
        op.create_index(
            "ix_job_summaries_user_id", "summaries", ["user_id"], unique=False, schema="job"
        )
        op.execute(
            "UPDATE job.summaries SET user_id = (SELECT id FROM auth.users WHERE username = 'hassan' LIMIT 1) WHERE user_id = ''"
        )


def downgrade() -> None:
    op.drop_index("ix_job_summaries_user_id", table_name="summaries", schema="job")
    op.drop_column("summaries", "user_id", schema="job")

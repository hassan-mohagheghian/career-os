"""add job analysis table

Revision ID: 42c200d12fd5
Revises: job_002_remove_job_num
Create Date: 2026-08-03 16:07:39.116804

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '42c200d12fd5'
down_revision: Union[str, None] = 'job_002_remove_job_num'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(bind, name: str, schema: str) -> bool:
    inspector = sa.inspect(bind)
    return inspector.has_table(name, schema=schema)


def upgrade() -> None:
    bind = op.get_bind()
    if _table_exists(bind, "job_analysis", "job"):
        # The table may already exist on databases where startup
        # Base.metadata.create_all() ran ahead of migrations.
        return

    op.create_table(
        "job_analysis",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("payload", sa.Text(), nullable=True),
        sa.Column("fit_score", sa.Integer(), nullable=True),
        sa.Column("success_score", sa.Integer(), nullable=True),
        sa.Column("overall_score", sa.Integer(), nullable=True),
        sa.Column("recommendation", sa.String(), nullable=True),
        sa.Column("apply_reason", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("prompt_version", sa.String(), nullable=True),
        sa.Column("schema_version", sa.String(), nullable=True),
        sa.Column("generated_at", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_job_analysis")),
        sa.UniqueConstraint("job_id", name="uq_job_analysis_job_id"),
        schema="job",
    )


def downgrade() -> None:
    op.drop_table("job_analysis", schema="job")

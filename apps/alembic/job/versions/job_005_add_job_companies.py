"""add job_companies table

Revision ID: job_005_add_job_companies
Revises: job_004_merge_job_heads
Create Date: 2026-08-06 21:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'job_005_add_job_companies'
down_revision: Union[str, None] = 'job_004_merge_job_heads'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(bind, name: str, schema: str) -> bool:
    inspector = sa.inspect(bind)
    return inspector.has_table(name, schema=schema)


def upgrade() -> None:
    bind = op.get_bind()
    if _table_exists(bind, "job_companies", "job"):
        # The table may already exist on databases where startup
        # Base.metadata.create_all() ran ahead of migrations.
        return

    op.create_table(
        "job_companies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("company_type", sa.String(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["job.jobs.id"],
            name=op.f("fk_job_companies_job_id_jobs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_job_companies")),
        schema="job",
    )
    op.create_index(
        op.f("ix_job_job_companies_job_id"),
        "job_companies",
        ["job_id"],
        unique=False,
        schema="job",
    )
    op.create_index(
        op.f("ix_job_job_companies_company_id"),
        "job_companies",
        ["company_id"],
        unique=False,
        schema="job",
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_job_job_companies_company_id"), table_name="job_companies", schema="job")
    op.drop_index(op.f("ix_job_job_companies_job_id"), table_name="job_companies", schema="job")
    op.drop_table("job_companies", schema="job")

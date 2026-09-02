"""add user_id to job_analysis

Revision ID: e2860ac259cf
Revises: 9d027fc9a94e
Create Date: 2026-09-02 08:12:48.388692

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e2860ac259cf"
down_revision: Union[str, None] = "9d027fc9a94e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("job_analysis", schema="job")}
    if "user_id" not in cols:
        op.add_column(
            "job_analysis",
            sa.Column("user_id", sa.String(36), nullable=False, server_default=""),
            schema="job",
        )
        op.create_index(
            "ix_job_job_analysis_user_id", "job_analysis", ["user_id"], unique=False, schema="job"
        )
        op.execute(
            "UPDATE job.job_analysis SET user_id = (SELECT id FROM auth.users WHERE username = 'hassan' LIMIT 1) WHERE user_id = ''"
        )
    existing = inspector.get_unique_constraints("job_analysis", schema="job")
    old_constraint = [c for c in existing if c["column_names"] == ["job_id"]]
    if old_constraint:
        op.drop_constraint(old_constraint[0]["name"], "job_analysis", schema="job", type_="unique")
    new_constraint = [c for c in existing if c["column_names"] == ["job_id", "user_id"]]
    if not new_constraint:
        op.create_unique_constraint(
            "uq_job_analysis_job_user", "job_analysis", ["job_id", "user_id"], schema="job"
        )


def downgrade() -> None:
    op.drop_constraint("uq_job_analysis_job_user", "job_analysis", schema="job", type_="unique")
    op.create_unique_constraint(
        op.f("uq_job_analysis_job_id"), "job_analysis", ["job_id"], schema="job",
        postgresql_nulls_not_distinct=False,
    )
    op.drop_index("ix_job_job_analysis_user_id", table_name="job_analysis", schema="job")
    op.drop_column("job_analysis", "user_id", schema="job")

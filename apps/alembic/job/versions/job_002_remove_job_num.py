"""Remove legacy numeric num / job_num columns, re-keying to job UUID id.

Revision ID: job_002_remove_job_num
Revises: b54e0ddc0786
Create Date: 2026-08-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "job_002_remove_job_num"
down_revision: Union[str, None] = "b54e0ddc0786"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _num_to_id_map(bind) -> dict:
    jobs = sa.table("jobs", sa.Column("num", sa.Integer()), sa.Column("id", sa.String(36)), schema="job")
    rows = bind.execute(sa.select(jobs.c.num, jobs.c.id)).fetchall()
    return {num: id_ for num, id_ in rows if num is not None and id_ is not None}


def upgrade() -> None:
    bind = op.get_bind()
    num_to_id = _num_to_id_map(bind)

    summaries = sa.table(
        "summaries",
        sa.Column("num", sa.Integer()),
        sa.Column("job_id", sa.String(36)),
        schema="job",
    )
    resumes = sa.table(
        "resumes",
        sa.Column("id", sa.String()),
        sa.Column("job_num", sa.Integer()),
        sa.Column("job_id", sa.String(36)),
        schema="job",
    )

    # 1. Add job_id columns and backfill from jobs.num -> jobs.id.
    op.add_column("summaries", sa.Column("job_id", sa.String(36), nullable=True), schema="job")
    op.add_column("resumes", sa.Column("job_id", sa.String(36), nullable=True), schema="job")

    for num, job_id in num_to_id.items():
        bind.execute(sa.update(summaries).where(summaries.c.num == num).values(job_id=job_id))
        bind.execute(sa.update(resumes).where(resumes.c.job_num == num).values(job_id=job_id))

    # 2. Summaries: replace num (PK) with an autoincrement integer id PK.
    op.drop_constraint("pk_summaries", "summaries", type_="primary", schema="job")
    op.drop_column("summaries", "num", schema="job")
    op.add_column(
        "summaries",
        sa.Column("id", sa.Integer(), sa.Identity()),
        schema="job",
    )
    op.create_primary_key("pk_summaries", "summaries", ["id"], schema="job")

    # 3. Jobs: promote id to primary key and drop num.
    op.drop_constraint("pk_jobs", "jobs", type_="primary", schema="job")
    op.drop_column("jobs", "num", schema="job")
    op.create_primary_key("pk_jobs", "jobs", ["id"], schema="job")

    # 4. Resumes: drop legacy job_num lookup.
    op.drop_column("resumes", "job_num", schema="job")


def downgrade() -> None:
    bind = op.get_bind()

    op.add_column("jobs", sa.Column("num", sa.Integer(), nullable=True), schema="job")

    # Re-key id -> num via row order as a best-effort downgrade.
    jobs = sa.table("jobs", sa.Column("id", sa.String(36)), sa.Column("num", sa.Integer()), schema="job")
    rows = bind.execute(sa.select(jobs.c.id)).fetchall()
    ordered = {str(id_).strip(): i for i, (id_,) in enumerate(rows, start=1)}
    for id_, num in ordered.items():
        bind.execute(sa.update(jobs).where(jobs.c.id == id_).values(num=num))

    op.add_column("resumes", sa.Column("job_num", sa.Integer(), nullable=True), schema="job")
    resumes = sa.table(
        "resumes",
        sa.Column("id", sa.String()),
        sa.Column("job_id", sa.String(36)),
        sa.Column("job_num", sa.Integer()),
        schema="job",
    )
    resumes_rows = bind.execute(sa.select(resumes.c.id, resumes.c.job_id)).fetchall()
    for id_, job_id in resumes_rows:
        if job_id in ordered:
            bind.execute(sa.update(resumes).where(resumes.c.id == id_).values(job_num=ordered[job_id]))

    # Rebuild summaries with num PK, carry job_id back via id order.
    op.drop_column("summaries", "id", schema="job")
    op.add_column("summaries", sa.Column("num", sa.Integer(), nullable=True), schema="job")
    summaries = sa.table(
        "summaries",
        sa.Column("id", sa.Integer(), sa.Identity()),
        sa.Column("num", sa.Integer()),
        sa.Column("job_id", sa.String(36)),
        schema="job",
    )
    summary_rows = bind.execute(sa.select(summaries.c.id, summaries.c.job_id)).fetchall()
    for i, (sid, job_id) in enumerate(summary_rows, start=1):
        bind.execute(sa.update(summaries).where(summaries.c.id == sid).values(num=i))
    op.drop_column("summaries", "job_id", schema="job")

    op.drop_column("resumes", "job_id", schema="job")
    op.create_primary_key("pk_summaries", "summaries", ["num"], schema="job")
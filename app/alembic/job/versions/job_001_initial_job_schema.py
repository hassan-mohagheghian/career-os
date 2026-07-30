"""Initial job schema

Revision ID: job_001
Revises:
Create Date: 2026-07-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "job_001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = ("job",)
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS job")

    op.create_table(
        "jobs",
        sa.Column("num", sa.Integer(), nullable=False),
        sa.Column("company", sa.String(), nullable=True),
        sa.Column("role", sa.String(), nullable=True),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("match", sa.String(), nullable=True),
        sa.Column("score", sa.String(), nullable=True),
        sa.Column("success", sa.String(), nullable=True),
        sa.Column("salary", sa.String(), nullable=True),
        sa.Column("stack", sa.String(), nullable=True),
        sa.Column("visa", sa.String(), nullable=True),
        sa.Column("applicants", sa.String(), nullable=True),
        sa.Column("posted", sa.String(), nullable=True),
        sa.Column("industry", sa.String(), nullable=True),
        sa.Column("domain", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("action", sa.String(), nullable=True),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("work_type", sa.String(), server_default="On-site"),
        sa.Column("workflow_log", sa.Text(), server_default="[]"),
        sa.Column("locations", sa.Text(), server_default="[]"),
        sa.Column("deleted", sa.Integer(), server_default="0"),
        sa.Column("employment_type", sa.String(), server_default="Full-time"),
        sa.Column("work_types", sa.Text(), server_default="[]"),
        sa.Column("raw_description", sa.Text(), nullable=True),
        sa.Column("structured_description", sa.Text(), nullable=True),
        sa.Column("adv_at", sa.String(), nullable=True),
        sa.Column("see_at", sa.String(), nullable=True),
        sa.Column("apply_reason", sa.Text(), nullable=True),
        sa.Column("fit_score", sa.Integer(), nullable=True),
        sa.Column("success_score", sa.Integer(), nullable=True),
        sa.Column("overall_score", sa.Integer(), nullable=True),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.Text(), nullable=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("apply_time", sa.String(), nullable=True),
        sa.Column("response_time", sa.String(), nullable=True),
        sa.Column("response_status", sa.String(), nullable=True),
        sa.Column("rescoring", sa.Integer(), server_default="0"),
        sa.Column("links", sa.Text(), server_default="[]"),
        sa.Column("source", sa.String(), server_default="web"),
        sa.Column("status", sa.String(), server_default="imported"),
        sa.Column("queue_order", sa.Integer(), server_default="0"),
        sa.Column("current_node", sa.String(), nullable=True),
        sa.Column("progress_pct", sa.Integer(), server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), server_default="0"),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("failure_step", sa.String(), nullable=True),
        sa.Column("failure_timestamp", sa.String(), nullable=True),
        sa.Column("session_id", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("num"),
        schema="job",
    )
    op.create_index("idx_jobs_url", "jobs", ["url"], schema="job")
    op.create_index("idx_jobs_created_at", "jobs", ["created_at"], schema="job")
    op.create_index("idx_jobs_posted_at", "jobs", ["posted"], schema="job")
    op.create_index("idx_jobs_status", "jobs", ["status"], schema="job")

    op.create_table(
        "summaries",
        sa.Column("num", sa.Integer(), nullable=False),
        sa.Column("company", sa.String(), nullable=True),
        sa.Column("match", sa.String(), nullable=True),
        sa.Column("score", sa.String(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("stack", sa.String(), nullable=True),
        sa.Column("resumeFit", sa.String(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("url", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("num"),
        schema="job",
    )

    op.create_table(
        "resumes",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("company", sa.String(), nullable=True),
        sa.Column("role", sa.String(), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1"),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=True),
        sa.Column("job_num", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="job",
    )

    op.create_table(
        "generation_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("type", sa.String(), nullable=True),
        sa.Column("job_num", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("company", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="job",
    )


def downgrade() -> None:
    op.drop_table("generation_history", schema="job")
    op.drop_table("resumes", schema="job")
    op.drop_table("summaries", schema="job")
    op.drop_table("jobs", schema="job")
    op.execute("DROP SCHEMA IF EXISTS job")
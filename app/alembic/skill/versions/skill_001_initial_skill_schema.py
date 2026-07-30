"""Initial skill schema

Revision ID: 001
Revises:
Create Date: 2026-07-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "skill_001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = ("skill",)
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS skill")

    op.create_table(
        "skills",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("level", sa.Integer(), server_default="1"),
        sa.Column("ml", sa.String(), nullable=True),
        sa.Column("mc", sa.String(), nullable=True),
        sa.Column("roles", sa.String(), server_default=""),
        sa.Column("path", sa.String(), server_default=""),
        sa.Column("source", sa.String(), server_default="service"),
        sa.Column("hidden", sa.Integer(), server_default="0"),
        sa.Column("merged_into", sa.String(), server_default=""),
        sa.Column("category", sa.String(), server_default=""),
        sa.Column("confidence", sa.Float(), server_default="0"),
        sa.Column("market_relevance", sa.Float(), server_default="0"),
        sa.Column("evidence", sa.Text(), server_default="[]"),
        sa.Column("source_type", sa.String(), server_default="service"),
        sa.Column("tags", sa.Text(), server_default="[]"),
        sa.Column("created_at", sa.Text(), nullable=True),
        sa.UniqueConstraint("name"),
        sa.PrimaryKeyConstraint("id"),
        schema="skill",
    )

    op.create_table(
        "skill_aliases",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("skill_id", sa.Integer(), sa.ForeignKey("skill.skills.id"), nullable=False),
        sa.Column("alias_name", sa.String(), nullable=False),
        sa.Column("normalized_name", sa.String(), server_default=""),
        sa.Column("created_at", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="skill",
    )

    op.create_table(
        "skill_relationships",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("skill_name", sa.String(), nullable=False),
        sa.Column("related_name", sa.String(), nullable=False),
        sa.Column("relation_type", sa.String(), nullable=False),
        sa.Column("confidence", sa.Float(), server_default="0"),
        sa.UniqueConstraint("skill_name", "related_name", "relation_type"),
        sa.PrimaryKeyConstraint("id"),
        schema="skill",
    )

    op.create_table(
        "skill_roadmaps",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("skill_name", sa.String(), nullable=False),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("skill.skill_roadmaps.id"), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), server_default=""),
        sa.Column("level", sa.Integer(), server_default="0"),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
        sa.Column("version", sa.Integer(), server_default="1"),
        sa.Column("numbering", sa.String(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="skill",
    )

    op.create_table(
        "skill_roadmap_progress",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("roadmap_id", sa.Integer(), sa.ForeignKey("skill.skill_roadmaps.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_name", sa.String(), nullable=False),
        sa.Column("completed", sa.Integer(), server_default="0"),
        sa.Column("updated_at", sa.Text(), nullable=True),
        sa.UniqueConstraint("roadmap_id"),
        sa.PrimaryKeyConstraint("id"),
        schema="skill",
    )

    op.create_table(
        "skill_roadmap_jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("skill_name", sa.String(), nullable=False),
        sa.Column("job_type", sa.String(), server_default="generate"),
        sa.Column("status", sa.String(), server_default="queued"),
        sa.Column("step", sa.Integer(), server_default="0"),
        sa.Column("total_steps", sa.Integer(), server_default="4"),
        sa.Column("message", sa.Text(), server_default=""),
        sa.Column("version", sa.Integer(), nullable=True),
        sa.Column("count", sa.Integer(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("session_id", sa.String(), nullable=True),
        sa.Column("provider_name", sa.String(), nullable=True),
        sa.Column("pid", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="skill",
    )


def downgrade() -> None:
    op.drop_table("skill_roadmap_jobs", schema="skill")
    op.drop_table("skill_roadmap_progress", schema="skill")
    op.drop_table("skill_roadmaps", schema="skill")
    op.drop_table("skill_relationships", schema="skill")
    op.drop_table("skill_aliases", schema="skill")
    op.drop_table("skills", schema="skill")
    op.execute("DROP SCHEMA IF EXISTS skill")
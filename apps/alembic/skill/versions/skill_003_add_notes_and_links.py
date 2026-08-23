"""add skill notes and links

Free-text activity notes and titled resource links on a skill, enabling
users to track learning progress and save documentation. Tables live in
the ``skill`` schema; FKs point within the same context only (rule 15).

Revision ID: skill_003
Revises: 20fc9eceffce
Create Date: 2026-08-22 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "skill_003"
down_revision: Union[str, None] = "20fc9eceffce"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "skill_notes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["skill_id"],
            ["skill.skills.id"],
            name=op.f("fk_skill_notes_skill_id_skills"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_skill_notes")),
        schema="skill",
    )
    op.create_index(
        op.f("ix_skill_skill_notes_skill_id"),
        "skill_notes",
        ["skill_id"],
        unique=False,
        schema="skill",
    )

    op.create_table(
        "skill_links",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["skill_id"],
            ["skill.skills.id"],
            name=op.f("fk_skill_links_skill_id_skills"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_skill_links")),
        schema="skill",
    )
    op.create_index(
        op.f("ix_skill_skill_links_skill_id"),
        "skill_links",
        ["skill_id"],
        unique=False,
        schema="skill",
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_skill_skill_links_skill_id"),
        table_name="skill_links",
        schema="skill",
    )
    op.drop_table("skill_links", schema="skill")

    op.drop_index(
        op.f("ix_skill_skill_notes_skill_id"),
        table_name="skill_notes",
        schema="skill",
    )
    op.drop_table("skill_notes", schema="skill")

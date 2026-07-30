"""Initial shared schema

Revision ID: 001
Revises:
Create Date: 2026-07-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "shared_001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = ("shared",)
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS shared")

    op.create_table(
        "rules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("rule_type", sa.String(), server_default="job"),
        sa.Column("scope", sa.String(), server_default="JOB"),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.Integer(), server_default="0"),
        sa.Column("score_weight", sa.Integer(), server_default="0"),
        sa.Column("enabled", sa.Integer(), server_default="1"),
        sa.Column("updated_at", sa.Text(), nullable=True),
        sa.UniqueConstraint("category", "key"),
        sa.PrimaryKeyConstraint("id"),
        schema="shared",
    )

    op.create_table(
        "cities",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("icon", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("info", sa.Text(), nullable=True),
        sa.Column("jobs", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="shared",
    )

    op.create_table(
        "metadata",
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("key"),
        schema="shared",
    )


def downgrade() -> None:
    op.drop_table("metadata", schema="shared")
    op.drop_table("cities", schema="shared")
    op.drop_table("rules", schema="shared")
    op.execute("DROP SCHEMA IF EXISTS shared")
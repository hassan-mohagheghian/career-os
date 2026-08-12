"""drop application preparation

Revision ID: application_002
Revises: roadmap_001
Create Date: 2026-08-12 12:41:43.562803

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "application_002"
down_revision: Union[str, None] = "roadmap_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(
        op.f("ix_application_application_preparations_application_id"),
        table_name="application_preparations",
        schema="application",
    )
    op.drop_table("application_preparations", schema="application")


def downgrade() -> None:
    op.create_table(
        "application_preparations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("application_id", sa.String(length=36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["application.applications.id"],
            name=op.f("fk_application_preparations_application_id_applications"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_application_preparations")),
        schema="application",
    )
    op.create_index(
        op.f("ix_application_application_preparations_application_id"),
        "application_preparations",
        ["application_id"],
        unique=False,
        schema="application",
    )
"""add application notes

Free-text activity notes on an application (user's own words + creation
time), listed newest first in the Application Workspace Notes section. Table
lives in the ``application`` schema; FK points within the same context only
(rule 15).

Revision ID: application_006
Revises: c3cbd31cd041
Create Date: 2026-08-21 18:04:42.347629
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "application_006"
down_revision: Union[str, None] = "c3cbd31cd041"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "application_notes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("application_id", sa.String(length=36), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["application.applications.id"],
            name=op.f("fk_application_notes_application_id_applications"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_application_notes")),
        schema="application",
    )
    op.create_index(
        op.f("ix_application_application_notes_application_id"),
        "application_notes",
        ["application_id"],
        unique=False,
        schema="application",
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_application_application_notes_application_id"),
        table_name="application_notes",
        schema="application",
    )
    op.drop_table("application_notes", schema="application")

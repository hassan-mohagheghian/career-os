"""add application status timeline

Records one row per application status transition (``changed_at``) so the
application tracker can render a lifecycle timeline. Table lives in the
``application`` schema; FK points within the same context only (rule 15).

Revision ID: application_004
Revises: 6806b605992a
Create Date: 2026-08-19 21:03:38.062072
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "application_004"
down_revision: Union[str, None] = "6806b605992a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "application_status_timeline",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("application_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("changed_at", sa.String(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["application.applications.id"],
            name=op.f("fk_application_status_timeline_application_id_applications"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_application_status_timeline")),
        schema="application",
    )
    op.create_index(
        op.f("ix_application_application_status_timeline_application_id"),
        "application_status_timeline",
        ["application_id"],
        unique=False,
        schema="application",
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_application_application_status_timeline_application_id"),
        table_name="application_status_timeline",
        schema="application",
    )
    op.drop_table("application_status_timeline", schema="application")
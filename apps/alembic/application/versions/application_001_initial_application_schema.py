"""initial application schema

Revision ID: application_001
Revises: 20fc9eceffce
Create Date: 2026-08-11 13:32:01.263819

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "application_001"
down_revision: Union[str, None] = "20fc9eceffce"
branch_labels: Union[str, Sequence[str], None] = ("application",)
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS application")

    op.create_table(
        "applications",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("applied_at", sa.String(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_applications")),
        schema="application",
    )
    op.create_index(
        op.f("ix_application_applications_job_id"),
        "applications",
        ["job_id"],
        unique=False,
        schema="application",
    )

    op.create_table(
        "application_follow_ups",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("application_id", sa.String(length=36), nullable=False),
        sa.Column("scheduled_at", sa.String(), nullable=True),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("completed_at", sa.String(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["application.applications.id"],
            name=op.f("fk_application_follow_ups_application_id_applications"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_application_follow_ups")),
        schema="application",
    )
    op.create_index(
        op.f("ix_application_application_follow_ups_application_id"),
        "application_follow_ups",
        ["application_id"],
        unique=False,
        schema="application",
    )

    op.create_table(
        "application_documents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("application_id", sa.String(length=36), nullable=False),
        sa.Column("document_type", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["application.applications.id"],
            name=op.f("fk_application_documents_application_id_applications"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_application_documents")),
        schema="application",
    )
    op.create_index(
        op.f("ix_application_application_documents_application_id"),
        "application_documents",
        ["application_id"],
        unique=False,
        schema="application",
    )

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


def downgrade() -> None:
    op.drop_index(
        op.f("ix_application_application_preparations_application_id"),
        table_name="application_preparations",
        schema="application",
    )
    op.drop_table("application_preparations", schema="application")

    op.drop_index(
        op.f("ix_application_application_documents_application_id"),
        table_name="application_documents",
        schema="application",
    )
    op.drop_table("application_documents", schema="application")

    op.drop_index(
        op.f("ix_application_application_follow_ups_application_id"),
        table_name="application_follow_ups",
        schema="application",
    )
    op.drop_table("application_follow_ups", schema="application")

    op.drop_index(
        op.f("ix_application_applications_job_id"),
        table_name="applications",
        schema="application",
    )
    op.drop_table("applications", schema="application")

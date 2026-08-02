"""Add llm_configurations table

Revision ID: shared_002
Revises: shared_001
Create Date: 2026-07-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "shared_002"
down_revision: Union[str, None] = "shared_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS ai")

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "llm_configurations" in inspector.get_table_names(schema="ai"):
        return

    op.create_table(
        "llm_configurations",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("model", sa.String(255), nullable=False),
        sa.Column("model_version", sa.String(100), nullable=True),
        sa.Column("enabled", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        schema="ai",
    )


def downgrade() -> None:
    op.drop_table("llm_configurations", schema="ai")
    op.execute("DROP SCHEMA IF EXISTS ai")

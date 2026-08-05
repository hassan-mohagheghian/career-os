"""Remove score_weight from rules

Revision ID: shared_003_remove_score_weight
Revises: job_004_merge_job_heads
Create Date: 2026-08-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "shared_003_remove_score_weight"
down_revision: Union[str, None] = "job_004_merge_job_heads"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("rules", "score_weight", schema="shared")


def downgrade() -> None:
    op.add_column("rules", sa.Column("score_weight", sa.Integer(), server_default="0"), schema="shared")

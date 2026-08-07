"""drop legacy resumes table

Revision ID: 25dc1b9ebc0e
Revises: candidate_002
Create Date: 2026-08-07 12:05:02.925811

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '25dc1b9ebc0e'
down_revision: Union[str, None] = 'candidate_002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The legacy `job.resumes` table backed the removed resume / LinkedIn /
    # tailored-document generation stack. Candidate source documents were
    # backfilled into `candidate.candidate_sources` (candidate_001) before this
    # drop, so no live data is lost here.
    op.drop_table("resumes", schema="job")


def downgrade() -> None:
    # Recreate the legacy resumes table with its final column layout (after the
    # job_num → job_id migration in job_002_remove_job_num.py).
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
        sa.Column("job_id", sa.String(length=36), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="job",
    )

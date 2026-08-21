"""drop legacy shared cities table

Revision ID: da0d4ba7154d
Revises: d45ccf9c8e45
Create Date: 2026-08-20 09:24:39.441538

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'da0d4ba7154d'
down_revision: Union[str, None] = 'd45ccf9c8e45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('cities', schema='shared')


def downgrade() -> None:
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

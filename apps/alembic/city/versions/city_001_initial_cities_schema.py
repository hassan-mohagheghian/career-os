"""initial cities schema

Revision ID: city_001
Revises: placeholder_001
Create Date: 2026-08-20 09:19:39.123562

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'city_001'
down_revision: Union[str, None] = 'placeholder_001'
branch_labels: Union[str, Sequence[str], None] = ('city',)
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS city")
    op.create_table(
        "cities",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("city", sa.String(), nullable=False),
        sa.Column("country", sa.String(), nullable=False),
        sa.Column("original_text", sa.Text(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cities")),
        sa.UniqueConstraint("city", "country", name=op.f("uq_cities_city_country")),
        schema="city",
    )


def downgrade() -> None:
    op.drop_table("cities", schema="city")

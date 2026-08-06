"""Sync company table autoincrement sequences past existing row ids.

Existing rows in company_intelligence / company_links were inserted with
explicit ids (seeded before the shared ProcessingExecution pipeline), so the
SERIAL sequences were never advanced. A new insert relying on autoincrement
then collides with an existing pk (e.g. UniqueViolation on company_intelligence
id=2). Re-align each sequence to max(id)+1 so inserts never collide.

Revision ID: company_004_sync_sequences
Revises: company_003_add_companies_raw_content
Create Date: 2026-08-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "company_004_sync_sequences"
down_revision: Union[str, None] = "company_003_add_companies_raw_content"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    for table in ("company_intelligence", "company_links"):
        bind.execute(
            sa.text(
                f"SELECT setval(pg_get_serial_sequence('company.{table}', 'id'), "
                f"COALESCE((SELECT MAX(id) FROM company.{table}), 0) + 1, false)"
            )
        )


def downgrade() -> None:
    pass

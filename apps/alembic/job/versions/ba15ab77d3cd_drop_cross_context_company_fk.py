"""drop cross-context company FK from job_companies

Revision ID: ba15ab77d3cd
Revises: 25dc1b9ebc0e
Create Date: 2026-08-07 14:50:29.850217

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba15ab77d3cd'
down_revision: Union[str, None] = '25dc1b9ebc0e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _fk_exists(bind, table: str, schema: str, constraint: str) -> bool:
    inspector = sa.inspect(bind)
    return any(
        c["name"] == constraint
        for c in inspector.get_foreign_keys(table, schema=schema)
    )


def upgrade() -> None:
    # Drop the cross-context FK created by job_005 (AGENTS.md rule 15 — no FKs
    # across bounded contexts; company_id is a logical reference only). Fresh
    # databases no longer get the constraint, so guard against it being absent.
    bind = op.get_bind()
    if _fk_exists(bind, "job_companies", "job", "fk_job_companies_company_id_companies"):
        op.drop_constraint(
            op.f("fk_job_companies_company_id_companies"),
            "job_companies",
            schema="job",
            type_="foreignkey",
        )


def downgrade() -> None:
    op.create_foreign_key(
        op.f("fk_job_companies_company_id_companies"),
        "job_companies",
        "companies",
        ["company_id"],
        ["id"],
        source_schema="job",
        referent_schema="company",
        ondelete="CASCADE",
    )

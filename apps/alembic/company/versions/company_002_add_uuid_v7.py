"""Re-key companies to UUID v7 ids.

Migrates company.companies.id from Integer to String(36) UUID v7, and updates
the referencing columns company_intelligence.company_id, company_links.company_id
and job.jobs.company_id in place, mirroring job_002_remove_job_num.

Revision ID: company_002_add_uuid_v7
Revises: shared_003_remove_score_weight
Create Date: 2026-08-05
"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "company_002_add_uuid_v7"
down_revision: Union[str, None] = "shared_003_remove_score_weight"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # 1. Drop FK constraints on the child tables so columns can be re-keyed.
    op.drop_constraint(
        "fk_company_intelligence_company_id_companies",
        "company_intelligence",
        type_="foreignkey",
        schema="company",
    )
    op.drop_constraint(
        "fk_company_links_company_id_companies",
        "company_links",
        type_="foreignkey",
        schema="company",
    )

    # 2. Companies: add uuid column, backfill, then promote it to the PK.
    op.add_column(
        "companies",
        sa.Column("id_uuid", sa.String(36), nullable=True),
        schema="company",
    )
    companies = sa.table(
        "companies",
        sa.Column("id", sa.Integer()),
        sa.Column("id_uuid", sa.String(36)),
        schema="company",
    )
    id_map = {}
    rows = bind.execute(sa.select(companies.c.id)).fetchall()
    for (old_id,) in rows:
        new_id = str(uuid.uuid7())
        id_map[old_id] = new_id
        bind.execute(
            sa.update(companies).where(companies.c.id == old_id).values(id_uuid=new_id)
        )

    # 3. company_intelligence / company_links: add uuid company_id and backfill.
    op.add_column(
        "company_intelligence",
        sa.Column("company_id_uuid", sa.String(36), nullable=True),
        schema="company",
    )
    op.add_column(
        "company_links",
        sa.Column("company_id_uuid", sa.String(36), nullable=True),
        schema="company",
    )
    for table in ("company_intelligence", "company_links"):
        child = sa.table(
            table,
            sa.Column("company_id", sa.Integer()),
            sa.Column("company_id_uuid", sa.String(36)),
            schema="company",
        )
        for old_id, new_id in id_map.items():
            bind.execute(
                sa.update(child)
                .where(child.c.company_id == old_id)
                .values(company_id_uuid=new_id)
            )

    # 4. job.jobs.company_id: add uuid column and backfill.
    op.add_column(
        "jobs",
        sa.Column("company_id_uuid", sa.String(36), nullable=True),
        schema="job",
    )
    jobs = sa.table(
        "jobs",
        sa.Column("company_id", sa.Integer()),
        sa.Column("company_id_uuid", sa.String(36)),
        schema="job",
    )
    for old_id, new_id in id_map.items():
        bind.execute(
            sa.update(jobs)
            .where(jobs.c.company_id == old_id)
            .values(company_id_uuid=new_id)
        )

    # 5. Drop the old integer id columns (companies.id is the PK).
    op.drop_constraint("pk_companies", "companies", type_="primary", schema="company")
    op.drop_column("companies", "id", schema="company")
    op.drop_column("company_intelligence", "company_id", schema="company")
    op.drop_column("company_links", "company_id", schema="company")
    op.drop_column("jobs", "company_id", schema="job")

    # 6. Rename the uuid columns into place.
    op.alter_column("companies", "id_uuid", new_column_name="id", schema="company")
    op.alter_column(
        "company_intelligence", "company_id_uuid", new_column_name="company_id", schema="company"
    )
    op.alter_column(
        "company_links", "company_id_uuid", new_column_name="company_id", schema="company"
    )
    op.alter_column("jobs", "company_id_uuid", new_column_name="company_id", schema="job")

    # 7. Re-apply NOT NULL and constraints.
    op.alter_column("companies", "id", nullable=False, schema="company")
    op.alter_column("company_intelligence", "company_id", nullable=False, schema="company")
    op.alter_column("company_links", "company_id", nullable=False, schema="company")

    op.create_primary_key("pk_companies", "companies", ["id"], schema="company")
    op.create_foreign_key(
        "fk_company_intelligence_company_id_companies",
        "company_intelligence",
        "companies",
        ["company_id"],
        ["id"],
        source_schema="company",
        referent_schema="company",
    )
    op.create_foreign_key(
        "fk_company_links_company_id_companies",
        "company_links",
        "companies",
        ["company_id"],
        ["id"],
        source_schema="company",
        referent_schema="company",
    )


def downgrade() -> None:
    bind = op.get_bind()

    # Restore integer ids by row order (downgrade is best-effort data-wise).
    op.drop_constraint(
        "fk_company_intelligence_company_id_companies",
        "company_intelligence",
        type_="foreignkey",
        schema="company",
    )
    op.drop_constraint(
        "fk_company_links_company_id_companies",
        "company_links",
        type_="foreignkey",
        schema="company",
    )

    companies = sa.table(
        "companies",
        sa.Column("id", sa.String(36)),
        sa.Column("id_num", sa.Integer()),
        schema="company",
    )
    rows = bind.execute(sa.select(companies.c.id)).fetchall()
    ordered = {str(id_).strip(): i for i, (id_,) in enumerate(rows, start=1)}

    op.add_column("companies", sa.Column("id_num", sa.Integer(), nullable=True), schema="company")
    for id_, num in ordered.items():
        bind.execute(sa.update(companies).where(companies.c.id == id_).values(id_num=num))

    op.add_column(
        "company_intelligence", sa.Column("company_id_num", sa.Integer(), nullable=True), schema="company"
    )
    op.add_column(
        "company_links", sa.Column("company_id_num", sa.Integer(), nullable=True), schema="company"
    )
    op.add_column("jobs", sa.Column("company_id_num", sa.Integer(), nullable=True), schema="job")

    for table in ("company_intelligence", "company_links"):
        child = sa.table(
            table,
            sa.Column("company_id", sa.String(36)),
            sa.Column("company_id_num", sa.Integer()),
            schema="company",
        )
        for id_, num in ordered.items():
            bind.execute(
                sa.update(child).where(child.c.company_id == id_).values(company_id_num=num)
            )
    jobs = sa.table(
        "jobs",
        sa.Column("company_id", sa.String(36)),
        sa.Column("company_id_num", sa.Integer()),
        schema="job",
    )
    for id_, num in ordered.items():
        bind.execute(sa.update(jobs).where(jobs.c.company_id == id_).values(company_id_num=num))

    op.drop_constraint("pk_companies", "companies", type_="primary", schema="company")
    op.drop_column("companies", "id", schema="company")
    op.drop_column("company_intelligence", "company_id", schema="company")
    op.drop_column("company_links", "company_id", schema="company")
    op.drop_column("jobs", "company_id", schema="job")

    op.alter_column("companies", "id_num", new_column_name="id", schema="company")
    op.alter_column(
        "company_intelligence", "company_id_num", new_column_name="company_id", schema="company"
    )
    op.alter_column(
        "company_links", "company_id_num", new_column_name="company_id", schema="company"
    )
    op.alter_column("jobs", "company_id_num", new_column_name="company_id", schema="job")

    op.alter_column("companies", "id", nullable=False, schema="company")
    op.create_primary_key("pk_companies", "companies", ["id"], schema="company")

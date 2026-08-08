"""add slug to skills/categories and create skill breakdowns

Revision ID: 20fc9eceffce
Revises: skill_002
Create Date: 2026-08-08 10:51:00.372164

Adds a unique `slug` (canonical name key) to `skill.skills` and
`skill.skill_categories`, backfills it from existing names and merges
collisions (rows whose names slugify to the same key — e.g. "NoSQL" vs
"nosql" — are consolidated onto the lowest-id row: mentions/category links
re-point, the duplicate name becomes an alias, the duplicate row is hidden).
Also creates `skill.skill_breakdowns` for the break-down feature.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20fc9eceffce'
down_revision: Union[str, None] = 'skill_002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _slugify(name: str) -> str:
    """Lowercase, trim, collapse separators to '-', keep + . # -."""
    import re
    cleaned = re.sub(r"[^\w+#.\-]+", "-", (name or "").strip().lower(), flags=re.UNICODE)
    return re.sub(r"-+", "-", cleaned).strip("-")


def _merge_skill_slugs(connection) -> None:
    """Consolidate skill rows whose names share a slug.

    For each slug group (ordered by id) the lowest-id row is canonical: it
    keeps the clean slug; every later duplicate gets its mentions and category
    links re-pointed to the canonical row (deduped), its name registered as an
    alias of the canonical row, its own slug suffixed to stay unique, and its
    `hidden` flag set so it no longer surfaces in the catalog.
    """
    rows = connection.execute(
        sa.text(
            "SELECT id, name, slug FROM skill.skills "
            "WHERE slug IS NOT NULL ORDER BY id"
        )
    ).fetchall()

    groups: dict[str, list[tuple[int, str]]] = {}
    for row in rows:
        groups.setdefault(row[2], []).append((row[0], row[1]))

    for slug, members in groups.items():
        if len(members) == 1:
            continue
        canonical_id, canonical_name = members[0]
        for dup_id, dup_name in members[1:]:
            # Re-point mentions onto the canonical row, skipping existing keys
            # so the unique (skill_id, source_type, source_id) constraint holds.
            connection.execute(
                sa.text(
                    "INSERT INTO skill.skill_mentions (skill_id, source_type, source_id, status, evidence, created_at) "
                    "SELECT :canonical_id, m.source_type, m.source_id, m.status, m.evidence, m.created_at "
                    "FROM skill.skill_mentions m "
                    "WHERE m.skill_id = :dup_id "
                    "ON CONFLICT (skill_id, source_type, source_id) DO NOTHING"
                ),
                {"canonical_id": canonical_id, "dup_id": dup_id},
            )
            connection.execute(
                sa.text("DELETE FROM skill.skill_mentions WHERE skill_id = :dup_id"),
                {"dup_id": dup_id},
            )

            # Re-point category links, deduped.
            connection.execute(
                sa.text(
                    "INSERT INTO skill.skill_category_links (skill_id, category_id, created_at) "
                    "SELECT :canonical_id, cl.category_id, cl.created_at "
                    "FROM skill.skill_category_links cl "
                    "WHERE cl.skill_id = :dup_id "
                    "ON CONFLICT (skill_id, category_id) DO NOTHING"
                ),
                {"canonical_id": canonical_id, "dup_id": dup_id},
            )
            connection.execute(
                sa.text("DELETE FROM skill.skill_category_links WHERE skill_id = :dup_id"),
                {"dup_id": dup_id},
            )

            # Register the duplicate name as an alias of the canonical row.
            connection.execute(
                sa.text(
                    "INSERT INTO skill.skill_aliases (skill_id, alias_name, normalized_name, created_at) "
                    "VALUES (:canonical_id, :alias_name, :normalized_name, now()) "
                    "ON CONFLICT DO NOTHING"
                ),
                {"canonical_id": canonical_id, "alias_name": dup_name, "normalized_name": dup_name.lower()},
            )

            # Keep the duplicate row (lineage) but hide it and give it a unique slug.
            connection.execute(
                sa.text("UPDATE skill.skills SET hidden = 1, slug = :dup_slug WHERE id = :dup_id"),
                {"dup_slug": f"{slug}-{dup_id}", "dup_id": dup_id},
            )


def _merge_category_slugs(connection) -> None:
    """Consolidate category rows whose names share a slug onto the lowest id."""
    rows = connection.execute(
        sa.text(
            "SELECT id, name, slug FROM skill.skill_categories "
            "WHERE slug IS NOT NULL ORDER BY id"
        )
    ).fetchall()

    groups: dict[str, list[tuple[int, str]]] = {}
    for row in rows:
        groups.setdefault(row[2], []).append((row[0], row[1]))

    for slug, members in groups.items():
        if len(members) == 1:
            continue
        canonical_id = members[0][0]
        canonical_name = members[0][1]
        for dup_id, dup_name in members[1:]:
            connection.execute(
                sa.text(
                    "INSERT INTO skill.skill_category_links (skill_id, category_id, created_at) "
                    "SELECT cl.skill_id, :canonical_id, cl.created_at "
                    "FROM skill.skill_category_links cl WHERE cl.category_id = :dup_id "
                    "ON CONFLICT (skill_id, category_id) DO NOTHING"
                ),
                {"canonical_id": canonical_id, "dup_id": dup_id},
            )
            connection.execute(
                sa.text("DELETE FROM skill.skill_category_links WHERE category_id = :dup_id"),
                {"dup_id": dup_id},
            )
            # Keep the category row's name mapping clean; the duplicate row is dropped.
            connection.execute(
                sa.text("UPDATE skill.skills SET category = :canonical_name WHERE category = :dup_name"),
                {"canonical_name": canonical_name, "dup_name": dup_name},
            )
            connection.execute(
                sa.text("DELETE FROM skill.skill_categories WHERE id = :dup_id"),
                {"dup_id": dup_id},
            )


def upgrade() -> None:
    bind = op.get_bind()

    op.add_column('skill_categories', sa.Column('slug', sa.String(), nullable=True), schema='skill')
    op.add_column('skills', sa.Column('slug', sa.String(), nullable=True), schema='skill')

    # Backfill slugs from existing names.
    skill_rows = bind.execute(sa.text("SELECT id, name FROM skill.skills")).fetchall()
    for skill_id, name in skill_rows:
        slug = _slugify(name) or f"skill-{skill_id}"
        bind.execute(
            sa.text("UPDATE skill.skills SET slug = :slug WHERE id = :id"),
            {"slug": slug, "id": skill_id},
        )

    cat_rows = bind.execute(sa.text("SELECT id, name FROM skill.skill_categories")).fetchall()
    for cat_id, name in cat_rows:
        slug = _slugify(name) or f"category-{cat_id}"
        bind.execute(
            sa.text("UPDATE skill.skill_categories SET slug = :slug WHERE id = :id"),
            {"slug": slug, "id": cat_id},
        )

    # Merge collisions (idempotent against a partially-migrated dev DB).
    _merge_skill_slugs(bind)
    _merge_category_slugs(bind)

    op.alter_column('skills', 'slug', existing_type=sa.String(), nullable=False, schema='skill')
    op.alter_column('skill_categories', 'slug', existing_type=sa.String(), nullable=False, schema='skill')

    op.create_index(op.f('ix_skill_skills_slug'), 'skills', ['slug'], unique=True, schema='skill')
    op.create_index(op.f('ix_skill_skill_categories_slug'), 'skill_categories', ['slug'], unique=True, schema='skill')

    op.create_table(
        'skill_breakdowns',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('origin_skill_id', sa.Integer(), nullable=False),
        sa.Column('child_skill_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['child_skill_id'], ['skill.skills.id'], name='fk_skill_breakdowns_child_skill_id_skills'),
        sa.ForeignKeyConstraint(['origin_skill_id'], ['skill.skills.id'], name='fk_skill_breakdowns_origin_skill_id_skills'),
        sa.PrimaryKeyConstraint('id', name='pk_skill_breakdowns'),
        sa.UniqueConstraint('origin_skill_id', 'child_skill_id', name='uq_skill_breakdowns_origin_skill_id'),
        schema='skill',
    )


def downgrade() -> None:
    op.drop_table('skill_breakdowns', schema='skill')
    op.drop_index(op.f('ix_skill_skill_categories_slug'), table_name='skill_categories', schema='skill')
    op.drop_index(op.f('ix_skill_skills_slug'), table_name='skills', schema='skill')
    op.drop_column('skill_categories', 'slug', schema='skill')
    op.drop_column('skills', 'slug', schema='skill')

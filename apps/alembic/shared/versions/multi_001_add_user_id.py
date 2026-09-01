"""Multi-tenancy 001 - Add user_id to all aggregate roots

Revision ID: multi_001
Revises: b04b9e764e91
Create Date: 2026-09-01
"""

from alembic import op
import sqlalchemy as sa

revision = 'multi_001'
down_revision = 'b04b9e764e91'
branch_labels = None
depends_on = None


def _add_user_id(table: str, schema: str) -> None:
    """Add user_id column to a table if it doesn't already exist."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c['name'] for c in inspector.get_columns(table, schema=schema)]
    if 'user_id' not in columns:
        op.add_column(
            table,
            sa.Column('user_id', sa.String(36), nullable=False, server_default='migrate'),
            schema=schema,
        )
        op.create_index(f'ix_{schema}_{table}_user_id', table, ['user_id'], schema=schema)


DEFAULT_USER_ID = '00000000-0000-0000-0000-000000000001'


def upgrade() -> None:
    # Ensure default user exists in auth.users
    op.execute("""
        INSERT INTO auth.users (id, username, display_name, password_hash, created_at, updated_at)
        SELECT '00000000-0000-0000-0000-000000000001', 'hassan', 'Hassan', 'seed', NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM auth.users WHERE username = 'hassan')
    """)

    # Aggregate roots that need user_id
    tables = [
        ('jobs', 'job'),
        ('companies', 'company'),
        ('skills', 'skill'),
        ('candidates', 'candidate'),
        ('applications', 'application'),
        ('roadmaps', 'roadmap'),
        ('placeholders', 'placeholders'),
        ('llm_configurations', 'ai'),
        ('rules', 'shared'),
        ('cities', 'city'),
    ]

    for table, schema in tables:
        _add_user_id(table, schema)

    # Backfill existing data to the default hassan user
    for table, schema in tables:
        op.execute(f"""
            UPDATE {schema}.{table} SET user_id = (
                SELECT id FROM auth.users WHERE username = 'hassan' LIMIT 1
            ) WHERE user_id = 'migrate'
        """)

    # Remove server default after backfill
    for table, schema in tables:
        op.alter_column(
            table,
            'user_id',
            server_default=None,
            schema=schema,
        )


def downgrade() -> None:
    tables = [
        ('jobs', 'job'),
        ('companies', 'company'),
        ('skills', 'skill'),
        ('candidates', 'candidate'),
        ('applications', 'application'),
        ('roadmaps', 'roadmap'),
        ('placeholders', 'placeholders'),
        ('llm_configurations', 'ai'),
        ('rules', 'shared'),
        ('cities', 'city'),
    ]

    for table, schema in tables:
        op.drop_index(f'ix_{schema}_{table}_user_id', schema=schema)
        op.drop_column(table, 'user_id', schema=schema)

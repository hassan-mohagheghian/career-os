"""Auth 001 - Create initial auth schema and users table

Revision ID: auth_001
Revises: 
Create Date: 2026-09-01
"""

from alembic import op
import sqlalchemy as sa

revision = 'auth_001'
down_revision = None
branch_labels = ('auth',)
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS auth")
    
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('username', sa.String(64), unique=True, nullable=False, index=True),
        sa.Column('display_name', sa.String(128), nullable=False),
        sa.Column('password_hash', sa.String(128), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema='auth'
    )


def downgrade() -> None:
    op.drop_table('users', schema='auth')
    op.execute("DROP SCHEMA IF EXISTS auth")

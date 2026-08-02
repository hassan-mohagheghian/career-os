"""Rename preferences table to rules.

Revision ID: 022_rename_preferences_to_rules
Revises: 021_drop_dashboard_insights
Create Date: 2026-07-29
"""
from typing import Sequence, Union

from alembic import op


revision: str = '022_rename_preferences_to_rules'
down_revision: Union[str, None] = '021_drop_dashboard_insights'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table('preferences', 'rules')


def downgrade() -> None:
    op.rename_table('rules', 'preferences')

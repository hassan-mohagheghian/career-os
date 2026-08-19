"""rename recommended status to seen

``recommended`` was the previous initial application status. It is replaced by
``seen`` (the mandatory, non-deletable first timeline node). This is a data
migration: it rewrites existing rows and backfills a ``seen`` node for any
application that has no timeline entries yet.

Revision ID: application_005
Revises: application_004
Create Date: 2026-08-19 22:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "application_005"
down_revision: Union[str, None] = "application_004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE application.applications SET status = 'seen' "
        "WHERE status = 'recommended'"
    )
    op.execute(
        "UPDATE application.application_status_timeline SET status = 'seen' "
        "WHERE status = 'recommended'"
    )
    op.execute(
        """
        INSERT INTO application.application_status_timeline
            (id, application_id, status, changed_at, created_at, updated_at)
        SELECT gen_random_uuid()::text, a.id, 'seen', a.created_at, a.created_at, a.created_at
        FROM application.applications a
        WHERE NOT EXISTS (
            SELECT 1 FROM application.application_status_timeline t
            WHERE t.application_id = a.id
        )
        """
    )


def downgrade() -> None:
    op.execute(
        "UPDATE application.application_status_timeline SET status = 'recommended' "
        "WHERE status = 'seen'"
    )
    op.execute(
        "UPDATE application.applications SET status = 'recommended' "
        "WHERE status = 'seen'"
    )
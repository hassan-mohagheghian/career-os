"""Clean up legacy application_preparation executions.

Prompt 146 removed the `application_preparation` execution type (feature deleted).
Databases that ran executions before that removal still carry orphaned rows in
`processing.processing_executions` with `execution_type='application_preparation'`,
which is no longer a valid :class:`ExecutionType`. This data migration hard-deletes
those dead rows (rule 8) so every repository read path stops failing.

Revision ID: application_003
Revises: application_002
Create Date: 2026-08-12 14:35:13.255463
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "application_003"
down_revision: Union[str, None] = "application_002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "DELETE FROM processing.processing_executions "
        "WHERE execution_type = 'application_preparation'"
    )


def downgrade() -> None:
    # Deleted executions belong to a removed feature and cannot be reconstructed;
    # the deletion is intentionally irreversible.
    pass
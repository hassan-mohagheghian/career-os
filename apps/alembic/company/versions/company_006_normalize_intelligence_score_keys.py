"""Normalize company_intelligence.scores to canonical keys.

Score keys were unified to the canonical form (fit / success / overall) and
the legacy aliases (company_fit_score / company_success_score /
company_overall_score) removed. This data migration rewrites existing rows so
the read path (list/detail/sort) can rely on canonical keys only.

Revision ID: company_006_normalize_intelligence_score_keys
Revises: company_005_add_parent_company_id
Create Date: 2026-08-06
"""
import json
from typing import Sequence, Union

from alembic import op


revision: str = "company_006_normalize_intelligence_score_keys"
down_revision: Union[str, None] = "company_005_add_parent_company_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_LEGACY_KEYS = ("company_fit_score", "company_success_score", "company_overall_score")


def _normalize(scores_raw: str) -> str:
    try:
        data = json.loads(scores_raw)
    except (json.JSONDecodeError, TypeError):
        return scores_raw
    if not isinstance(data, dict):
        return scores_raw

    for legacy, canonical in (
        ("company_fit_score", "fit"),
        ("company_success_score", "success"),
        ("company_overall_score", "overall"),
    ):
        if legacy in data and canonical not in data:
            data[canonical] = data[legacy]
    for key in _LEGACY_KEYS:
        data.pop(key, None)

    return json.dumps(data, ensure_ascii=False)


def upgrade() -> None:
    conn = op.get_bind()
    table = '"company"."company_intelligence"'
    rows = conn.exec_driver_sql(
        f'SELECT id, scores FROM {table} WHERE scores IS NOT NULL'
    ).fetchall()
    for row_id, scores_raw in rows:
        normalized = _normalize(scores_raw)
        if normalized != scores_raw:
            conn.exec_driver_sql(
                f'UPDATE {table} SET scores = %s WHERE id = %s',
                (normalized, row_id),
            )


def downgrade() -> None:
    # Re-introducing legacy aliases from canonical keys is lossy and not worth
    # doing; the normalization is reversible by re-processing instead.
    pass

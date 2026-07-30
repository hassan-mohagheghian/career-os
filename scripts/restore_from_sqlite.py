"""Restore data from SQLite backup to PostgreSQL.

Usage: python scripts/restore_from_sqlite.py
"""

import sys
import os
import sqlite3
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'server'))

from sqlalchemy import create_engine, inspect, text
from shared.infrastructure.config.app_config import DATABASE_URL


SQLITE_PATH = os.path.join(os.path.dirname(__file__), '..', 'app', 'server', 'db', 'jobs.db')


SCHEMA_MAP = {
    'alembic_version': 'public',
    'cities': 'shared',
    'companies': 'company',
    'company_intelligence': 'company',
    'company_links': 'company',
    'generation_history': 'job',
    'jobs': 'job',
    'metadata': 'shared',
    'resumes': 'job',
    'rules': 'shared',
    'skill_aliases': 'skill',
    'skill_relationships': 'skill',
    'skill_roadmap_jobs': 'skill',
    'skill_roadmap_progress': 'skill',
    'skill_roadmaps': 'skill',
    'skills': 'skill',
    'summaries': 'job',
}


DEFAULTS = {
    'companies': {'notes': '[]', 'links': '[]', 'workflow_log': '[]', 'input_text': '', 'tech_stack': '{}', 'work_environment': '{}', 'extra': '{}', 'products': '[]', 'countries_of_operation': '[]', 'founded_year': '', 'funding_amount': '', 'session_id': '', 'queue_order': 0, 'progress_pct': 0, 'retry_count': 0},
    'company_links': {'extracted_content': '', 'title': '', 'description': ''},
    'jobs': {'notes': '[]', 'links': '[]', 'workflow_log': '[]', 'locations': '[]', 'work_types': '[]', 'session_id': '', 'queue_order': 0, 'progress_pct': 0, 'retry_count': 0},
    'skills': {'evidence': '[]', 'source': 'service', 'source_type': 'service', 'tags': '[]'},
}


def _normalize(val):
    if isinstance(val, datetime):
        return val.isoformat()
    if isinstance(val, float) and val != val:
        return None
    return val


def _defaults_for(table_name, col):
    return DEFAULTS.get(table_name, {}).get(col)


def restore():
    print(f"Reading from SQLite: {SQLITE_PATH}")
    sqlite = sqlite3.connect(SQLITE_PATH)
    sqlite.row_factory = sqlite3.Row

    pg_engine = create_engine(DATABASE_URL)
    inspector = inspect(pg_engine)

    with pg_engine.connect() as conn:
        conn.execute(text("SET session_replication_role = 'replica'"))

        for table_name in sorted(SCHEMA_MAP):
            schema = SCHEMA_MAP[table_name]

            if table_name not in inspector.get_table_names(schema=schema):
                print(f"  Skipping {schema}.{table_name} (not found in PG)")
                continue

            pg_cols = [c['name'] for c in inspector.get_columns(table_name, schema=schema)]
            pg_not_null = {c['name'] for c in inspector.get_columns(table_name, schema=schema) if not c.get('nullable', True)}

            rows = sqlite.execute(f'SELECT * FROM "{table_name}"').fetchall()
            if not rows:
                print(f"  {schema}.{table_name}: 0 rows, skipping")
                continue

            conn.execute(text(f'TRUNCATE TABLE "{schema}"."{table_name}" CASCADE'))

            common_cols = [c for c in pg_cols if c in rows[0].keys()]

            placeholders = ", ".join([f":{c}" for c in common_cols])
            cols_sql = ", ".join([f'"{c}"' for c in common_cols])
            insert_sql = f'INSERT INTO "{schema}"."{table_name}" ({cols_sql}) VALUES ({placeholders})'

            count = 0
            for row in rows:
                vals = {}
                for c in common_cols:
                    val = _normalize(row[c])
                    if val is None and c in pg_not_null:
                        val = _defaults_for(table_name, c)
                    vals[c] = val
                conn.execute(text(insert_sql), vals)
                count += 1
                if count % 50 == 0:
                    print(f"    {schema}.{table_name}: {count}/{len(rows)}", flush=True)

            print(f"  {schema}.{table_name}: {count} rows restored", flush=True)

        conn.execute(text("SET session_replication_role = 'origin'"))
        conn.commit()

    sqlite.close()
    pg_engine.dispose()
    print("\nRestore complete.")


if __name__ == "__main__":
    restore()

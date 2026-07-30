"""Migrate data from SQLite (app/server/db/jobs.db) to PostgreSQL.

Handles column type mismatches, different schemas, and data inconsistencies.
"""

import sqlite3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

SQLITE_PATH = "app/server/db/jobs.db"
DATABASE_URL = "postgresql+psycopg://jobsearch:jobsearch@localhost:5432/jobsearch"

TABLE_MAP = {
    "jobs": ("job", "jobs"),
    "companies": ("company", "companies"),
    "company_intelligence": ("company", "company_intelligence"),
    "company_links": ("company", "company_links"),
    "skills": ("skill", "skills"),
    "skill_aliases": ("skill", "skill_aliases"),
    "skill_relationships": ("skill", "skill_relationships"),
    "skill_roadmaps": ("skill", "skill_roadmaps"),
    "skill_roadmap_progress": ("skill", "skill_roadmap_progress"),
    "skill_roadmap_jobs": ("skill", "skill_roadmap_jobs"),
    "rules": ("shared", "rules"),
    "cities": ("shared", "cities"),
    "metadata": ("shared", "metadata"),
    "summaries": ("job", "summaries"),
    "resumes": ("job", "resumes"),
    "generation_history": ("job", "generation_history"),
}

DROP_COLS = {
    "jobs": {"posted_at", "raw_file_path", "structured_file_path",
             "company_url", "linkedin_url", "previous_status"},
    "companies": {"links", "skills"},
}

NOT_NULL_DEFAULTS = {
    "jobs": {
        "work_type": "On-site",
        "workflow_log": "[]",
        "locations": "[]",
        "deleted": 0,
        "employment_type": "Full-time",
        "work_types": "[]",
        "rescoring": 0,
        "links": "[]",
        "status": "pending",
        "queue_order": 0,
        "progress_pct": 0,
        "retry_count": 0,
    },
    "companies": {
        "notes": "",
        "source": "web",
        "workflow_log": "[]",
        "status": "pending",
        "queue_order": 0,
        "progress_pct": 0,
        "retry_count": 0,
    },
    "skills": {
        "name": "",
        "level": 1,
        "roles": "",
        "path": "",
        "source": "",
        "hidden": 0,
        "merged_into": "",
        "category": "",
        "confidence": 0.0,
        "market_relevance": 0.0,
        "evidence": "[]",
        "source_type": "",
        "tags": "[]",
    },
    "skill_aliases": {
        "skill_id": 0,
        "alias_name": "",
        "normalized_name": "",
    },
    "skill_relationships": {
        "skill_name": "",
        "related_name": "",
        "relation_type": "",
        "confidence": 0.0,
    },
    "skill_roadmaps": {
        "skill_name": "",
        "title": "",
        "description": "",
        "level": 0,
        "sort_order": 0,
        "version": 1,
    },
    "skill_roadmap_progress": {
        "roadmap_id": 0,
        "skill_name": "",
        "completed": 0,
    },
    "skill_roadmap_jobs": {
        "skill_name": "",
        "job_type": "",
        "status": "",
        "step": 0,
        "total_steps": 0,
        "message": "",
    },
    "rules": {
        "category": "",
        "key": "",
        "value": "",
        "rule_type": "job",
        "scope": "JOB",
        "priority": 0,
        "score_weight": 0,
        "enabled": 1,
    },
    "cities": {},
    "company_intelligence": {},
    "company_links": {},
    "summaries": {},
    "resumes": {
        "version": 1,
    },
    "generation_history": {},
}

COLUMN_RENAME = {
    "summaries": {"resumeFit": "resumefit"},
}


def get_sqlite_data(cursor, table_name):
    cursor.execute(f"SELECT * FROM {table_name}")
    columns = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    return columns, rows


def get_pg_columns(conn, schema, table):
    result = conn.execute(
        text("""SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = :schema AND table_name = :table
                ORDER BY ordinal_position"""),
        {"schema": schema, "table": table},
    )
    return [row[0] for row in result]


def safe_int(val):
    if val is None:
        return None
    if isinstance(val, int):
        return val
    if isinstance(val, float):
        return int(val)
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def cast_value(val, col_name, table_name):
    if col_name in INT_COLS.get(table_name, set()):
        return safe_int(val)
    if isinstance(val, str) and val == "":
        return None
    return val


INT_COLS = {
    "jobs": {"num", "deleted", "rescoring", "fit_score",
             "success_score", "overall_score", "company_id",
             "queue_order", "progress_pct", "retry_count"},
    "companies": {"id", "queue_order", "progress_pct", "retry_count"},
    "skills": {"id", "level", "hidden", "confidence", "market_relevance"},
    "rules": {"id", "priority", "score_weight", "enabled"},
    "skill_roadmaps": {"id", "level", "sort_order", "version"},
    "skill_roadmap_progress": {"id", "roadmap_id", "completed"},
    "skill_roadmap_jobs": {"id", "step", "total_steps", "version", "count", "pid"},
    "summaries": {"num"},
    "resumes": {"version", "job_num"},
    "cities": {"id"},
    "company_intelligence": {"id", "company_id"},
    "company_links": {"id", "company_id"},
    "skill_aliases": {"id", "skill_id"},
    "skill_relationships": {"id"},
    "generation_history": {"id", "job_num"},
    "metadata": {},
}


def migrate_table(sqlite_cursor, pg_session, sqlite_table, pg_schema, pg_table):
    sqlite_cols, rows = get_sqlite_data(sqlite_cursor, sqlite_table)
    if not rows:
        print(f"  {sqlite_table}: 0 rows (empty)")
        return

    pg_cols = get_pg_columns(pg_session.connection(), pg_schema, pg_table)
    pg_cols_set = set(pg_cols)

    drop_set = DROP_COLS.get(sqlite_table, set())
    rename_map = COLUMN_RENAME.get(sqlite_table, {})
    defaults = NOT_NULL_DEFAULTS.get(sqlite_table, {})

    # Build mapping from original SQLite index -> (orig_col_name, pg_col_name)
    # Only for columns that exist in both SQLite and PostgreSQL
    index_to_pg = {}
    for i, col in enumerate(sqlite_cols):
        if col in drop_set:
            continue
        mapped = rename_map.get(col, col)
        if mapped not in pg_cols_set:
            continue
        index_to_pg[i] = (col, mapped)

    common_cols = [mapped for _, (_, mapped) in sorted(index_to_pg.items())]
    if not common_cols:
        print(f"  SKIP {sqlite_table}: no common columns")
        return

    pg_conn = pg_session.connection()
    placeholders = ", ".join([f":{c}" for c in common_cols])
    pg_cols_str = ", ".join(common_cols)
    insert_sql = text(
        f"INSERT INTO {pg_schema}.{pg_table} ({pg_cols_str}) VALUES ({placeholders})"
        " ON CONFLICT DO NOTHING"
    )

    inserted = 0
    skipped = 0

    for row in rows:
        record = {}
        for orig_idx, (orig_name, mapped_name) in index_to_pg.items():
            val = row[orig_idx]
            val = cast_value(val, mapped_name, sqlite_table)
            record[mapped_name] = val

        for col, default_val in defaults.items():
            if col in record and record[col] is None:
                record[col] = default_val

        try:
            pg_conn.execute(insert_sql, record)
            inserted += 1
        except Exception:
            skipped += 1

    pg_session.commit()
    status = f"{inserted} rows inserted"
    if skipped:
        status += f", {skipped} skipped (errors)"
    print(f"  {sqlite_table}: {status}")


def main():
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_cursor = sqlite_conn.cursor()

    pg_engine = create_engine(DATABASE_URL, echo=False)

    # Truncate all tables first
    with Session(pg_engine) as pg_session:
        pg_session.execute(text("SET session_replication_role = replica;"))
        for sqlite_table, (pg_schema, pg_table) in TABLE_MAP.items():
            pg_session.execute(text(f"TRUNCATE TABLE {pg_schema}.{pg_table} CASCADE;"))
        pg_session.commit()

    with Session(pg_engine) as pg_session:
        for sqlite_table, (pg_schema, pg_table) in TABLE_MAP.items():
            print(f"Migrating {sqlite_table} -> {pg_schema}.{pg_table} ...")
            migrate_table(sqlite_cursor, pg_session, sqlite_table, pg_schema, pg_table)

    # Re-enable triggers
    with Session(pg_engine) as pg_session:
        pg_session.execute(text("SET session_replication_role = default;"))
        pg_session.commit()

    # Reset sequences
    with Session(pg_engine) as pg_session:
        pg_session.execute(text("SELECT setval('job.jobs_num_seq', COALESCE((SELECT MAX(num) FROM job.jobs), 0));"))
        pg_session.execute(text("SELECT setval('company.companies_id_seq', COALESCE((SELECT MAX(id) FROM company.companies), 0));"))
        pg_session.execute(text("SELECT setval('skill.skills_id_seq', COALESCE((SELECT MAX(id) FROM skill.skills), 0));"))
        pg_session.commit()

    sqlite_conn.close()
    print("\nMigration complete!")


if __name__ == "__main__":
    main()

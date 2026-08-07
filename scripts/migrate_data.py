"""Migrate data from SQLite to PostgreSQL.

Usage:
    DATABASE_URL=postgresql+psycopg://user:pass@host/db python scripts/migrate_data.py

Reads from apps/backend/db/jobs.db and writes to the target PostgreSQL.
Only migrates columns that exist in the target schema.
Skips rows that fail type conversion.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

SQLITE_PATH = os.path.join(os.path.dirname(__file__), '..', 'app', 'server', 'db', 'jobs.db')
PG_URL_RAW = os.environ.get('DATABASE_URL')
if not PG_URL_RAW:
    sys.exit("DATABASE_URL is required")

PG_URL = PG_URL_RAW.replace('postgresql+psycopg://', 'postgresql://', 1)

import sqlite3
import psycopg
from psycopg import sql as pgsql

TABLE_MAP = {
    "jobs": ("job.jobs", "num"),
    "companies": ("company.companies", "id"),
    "company_intelligence": ("company.company_intelligence", "id"),
    "company_links": ("company.company_links", "id"),
    "skills": ("skill.skills", "id"),
    "skill_aliases": ("skill.skill_aliases", "id"),
    "skill_relationships": ("skill.skill_relationships", "id"),
    "summaries": ("job.summaries", "num"),
    "resumes": ("job.resumes", "id"),
    "rules": ("shared.rules", "id"),
    "cities": ("shared.cities", "id"),
    "generation_history": ("job.generation_history", "id"),
    "metadata": ("shared.metadata", None),
}


def get_pg_columns(pg_conn, pg_table):
    schema, table = pg_table.split(".")
    cur = pg_conn.execute(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema = %s AND table_name = %s ORDER BY ordinal_position",
        (schema, table)
    )
    return {r[0]: r[1] for r in cur.fetchall()}


def get_sqlite_columns(conn, table_name):
    info = conn.execute(f'PRAGMA table_info("{table_name}")').fetchall()
    return [c[1] for c in info]


def main():
    if not os.path.exists(SQLITE_PATH):
        sys.exit(f"SQLite database not found: {SQLITE_PATH}")

    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row

    pg_conn = psycopg.connect(PG_URL)
    pg_conn.autocommit = False

    cursor = sqlite_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence' ORDER BY name"
    )
    tables = [r[0] for r in cursor.fetchall()]

    total_rows = 0
    total_errors = 0
    for src_table in tables:
        if src_table not in TABLE_MAP:
            print(f"  Skipping {src_table} (no mapping)")
            continue

        dst_table, pk_col = TABLE_MAP[src_table]

        pg_col_info = get_pg_columns(pg_conn, dst_table)
        if not pg_col_info:
            print(f"  Skipping {src_table} -> {dst_table}: target table not found")
            continue

        sqlite_cols = get_sqlite_columns(sqlite_conn, src_table)
        common_cols = [c for c in sqlite_cols if c in pg_col_info]
        missing = [c for c in sqlite_cols if c not in pg_col_info]
        if missing:
            print(f"  {src_table} -> {dst_table}: skipping columns {missing}")

        rows = sqlite_conn.execute(f'SELECT * FROM "{src_table}"').fetchall()
        if not rows:
            print(f"  {src_table} -> {dst_table}: 0 rows (empty)")
            continue

        col_list = pgsql.SQL(", ").join(pgsql.Identifier(c) for c in common_cols)
        ph = pgsql.SQL(", ").join(pgsql.Placeholder() for _ in common_cols)
        insert_sql = pgsql.SQL("INSERT INTO {} ({}) VALUES ({}) ON CONFLICT DO NOTHING").format(
            pgsql.Identifier(*dst_table.split(".")), col_list, ph
        )

        pg_cursor = pg_conn.cursor()
        batch = []
        skipped = 0
        for row in rows:
            try:
                values = tuple(row[c] for c in common_cols)
                batch.append(values)
            except Exception:
                skipped += 1
                continue
            if len(batch) >= 500:
                try:
                    pg_cursor.executemany(insert_sql, batch)
                    pg_conn.commit()
                except Exception as e:
                    for vals in batch:
                        try:
                            pg_cursor.execute(insert_sql, vals)
                            pg_conn.commit()
                        except Exception:
                            total_errors += 1
                            pg_conn.rollback()
                batch.clear()

        if batch:
            try:
                pg_cursor.executemany(insert_sql, batch)
                pg_conn.commit()
            except Exception:
                for vals in batch:
                    try:
                        pg_cursor.execute(insert_sql, vals)
                        pg_conn.commit()
                    except Exception:
                        total_errors += 1
                        pg_conn.rollback()

        good = len(rows) - skipped - total_errors
        print(f"  {src_table} -> {dst_table}: {len(rows)} rows ({good} ok, {total_errors} errors, {skipped} skipped)")
        total_rows += good

    sqlite_conn.close()
    pg_conn.close()
    print(f"\nDone. {total_rows} total rows migrated ({total_errors} errors).")


if __name__ == "__main__":
    main()
"""Consolidated database access layer with retry logic and helpers."""

import json
import sqlite3
import time

from config import DB_PATH


def get_db():
    """Get database connection with WAL mode and retry for locked databases."""
    for attempt in range(5):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5)
            conn.row_factory = sqlite3.Row
            conn.execute('PRAGMA journal_mode=WAL')
            return conn
        except sqlite3.OperationalError as e:
            if 'locked' in str(e) and attempt < 4:
                time.sleep(0.5 * (attempt + 1))
            else:
                raise


def row_to_dict(row):
    """Convert a sqlite3.Row to a dictionary."""
    return dict(row) if row else None


def rows_to_list(rows):
    """Convert a list of sqlite3.Row objects to a list of dictionaries."""
    return [dict(r) for r in rows]

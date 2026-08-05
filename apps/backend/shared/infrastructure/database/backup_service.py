"""Database backup service — PostgreSQL backup + retention pruning.

Backups are produced with ``pg_dump`` running inside the PostgreSQL Docker
container (``docker exec``), because ``pg_dump`` is not installed on the host.
The dump is written directly to the host's backup directory via stdout.

Retention policy: keep only the N most recent backups (default 3) and delete
the rest, so the dev backup scheduler never fills the disk.
"""

from __future__ import annotations

import glob
import os
import subprocess
from datetime import datetime

from shared.infrastructure.config.app_config import (
    DATABASE_URL,
    DB_BACKUP_CONTAINER,
    DB_BACKUP_DIR,
    DB_BACKUP_KEEP_COUNT,
)
from shared.infrastructure.process.logging_config import get_logger
from sqlalchemy.engine import make_url

log = get_logger("db.backup")

BACKUP_PREFIX = "jobsearch"
BACKUP_EXT = ".dump"
BACKUP_GLOB = f"{BACKUP_PREFIX}_*.{BACKUP_EXT.lstrip('.')}"


def _db_credentials() -> tuple[str, str]:
    url = make_url(DATABASE_URL)
    return url.username or "postgres", url.database or "postgres"


def _backup_filename(now: datetime) -> str:
    return f"{BACKUP_PREFIX}_{now.strftime('%Y%m%d_%H%M%S')}{BACKUP_EXT}"


def _dump_command(database: str, username: str) -> list[str]:
    return [
        "docker",
        "exec",
        DB_BACKUP_CONTAINER,
        "pg_dump",
        "-U",
        username,
        "-d",
        database,
        "--format=custom",
        "--no-owner",
    ]


def create_db_backup() -> str:
    """Create a new PostgreSQL dump and return the backup file path."""
    os.makedirs(DB_BACKUP_DIR, exist_ok=True)
    username, database = _db_credentials()
    backup_path = os.path.join(DB_BACKUP_DIR, _backup_filename(datetime.now()))

    with open(backup_path, "wb") as fh:
        proc = subprocess.run(
            _dump_command(database, username),
            stdout=fh,
            stderr=subprocess.PIPE,
            check=False,
        )

    if proc.returncode != 0:
        stderr = proc.stderr.decode(errors="replace").strip()
        os.remove(backup_path)
        raise RuntimeError(
            f"pg_dump failed (exit {proc.returncode}) for {database}: {stderr}"
        )

    log.info("backup.created", path=backup_path)
    return backup_path


def list_backups() -> list[str]:
    """List existing backup files, oldest first."""
    return sorted(glob.glob(os.path.join(DB_BACKUP_DIR, BACKUP_GLOB)))


def prune_old_backups(keep: int = DB_BACKUP_KEEP_COUNT) -> list[str]:
    """Delete backups beyond the N most recent and return the removed paths."""
    backups = list_backups()
    if keep < 0:
        keep = 0
    stale = backups[:-keep] if keep > 0 else backups
    removed: list[str] = []
    for path in stale:
        try:
            os.remove(path)
            removed.append(path)
            log.info("backup.pruned", path=path)
        except OSError as e:  # pragma: no cover - fs error
            log.error("backup.prune_failed", path=path, error=str(e))
    return removed


def run_db_backup() -> dict:
    """Create a backup and enforce retention. Returns a summary dict."""
    backup_path = create_db_backup()
    removed = prune_old_backups(DB_BACKUP_KEEP_COUNT)
    return {
        "created": backup_path,
        "removed": removed,
        "retained": len(list_backups()),
    }

"""
SQLite repository implementations — persistence layer.

DDD: Repositories are the only place that touches the database directly.
Domain models flow in, raw SQL stays here.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from datetime import datetime
from typing import Optional, List, Dict

from .interfaces import IPendingRepository, IJobRepository
from .models import ItemStatus, WorkflowLogEntry


def _open_db(db_path: str) -> sqlite3.Connection:
    """Open a DB connection with WAL mode and retry on lock."""
    for attempt in range(5):
        try:
            conn = sqlite3.connect(db_path, timeout=5)
            conn.row_factory = sqlite3.Row
            conn.execute('PRAGMA journal_mode=WAL')
            return conn
        except sqlite3.OperationalError as e:
            if 'locked' in str(e) and attempt < 4:
                time.sleep(0.5 * (attempt + 1))
            else:
                raise


# ── Pending Jobs Repository ───────────────────────────────────────

class PendingJobRepository(IPendingRepository):
    """Repository for pending_jobs table."""

    def __init__(self, db_path: str):
        self._db_path = db_path

    def _db(self) -> sqlite3.Connection:
        return _open_db(self._db_path)

    def get(self, pid: int) -> Optional[dict]:
        conn = self._db()
        try:
            row = conn.execute('SELECT * FROM pending_jobs WHERE id=?', (pid,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def update_status(self, pid: int, status: ItemStatus, **fields) -> None:
        conn = self._db()
        try:
            sets = ['status=?', 'updated_at=?']
            vals = [status.value, datetime.now().isoformat()]
            for k, v in fields.items():
                sets.append(f'{k}=?')
                vals.append(v)
            vals.append(pid)
            conn.execute(f'UPDATE pending_jobs SET {",".join(sets)} WHERE id=?', vals)
            conn.commit()
        finally:
            conn.close()

    def update_step(self, pid: int, step: str, val: int, **fields) -> None:
        conn = self._db()
        try:
            sets = [f'{step}=?', 'updated_at=?']
            vals = [val, datetime.now().isoformat()]
            for k, v in fields.items():
                sets.append(f'{k}=?')
                vals.append(v)
            vals.append(pid)
            conn.execute(f'UPDATE pending_jobs SET {",".join(sets)} WHERE id=?', vals)
            conn.commit()
        finally:
            conn.close()

    def append_log(self, pid: int, entry: WorkflowLogEntry) -> None:
        conn = self._db()
        try:
            row = conn.execute('SELECT workflow_log FROM pending_jobs WHERE id=?', (pid,)).fetchone()
            logs = json.loads(row['workflow_log'] or '[]') if row else []
            logs.append(entry.to_dict())
            conn.execute('UPDATE pending_jobs SET workflow_log=? WHERE id=?', (json.dumps(logs), pid))
            conn.commit()
        finally:
            conn.close()

    def get_logs(self, pid: int) -> List[WorkflowLogEntry]:
        conn = self._db()
        try:
            row = conn.execute('SELECT workflow_log FROM pending_jobs WHERE id=?', (pid,)).fetchone()
            if not row:
                return []
            logs = json.loads(row['workflow_log'] or '[]')
            return [WorkflowLogEntry.from_dict(e) for e in logs]
        finally:
            conn.close()

    def claim_next(self) -> Optional[dict]:
        """Atomically claim the next queued job. Returns None if nothing available."""
        conn = self._db()
        try:
            row = conn.execute(
                'SELECT id FROM pending_jobs WHERE status=? ORDER BY queue_order ASC, created_at ASC LIMIT 1',
                ('queued',)
            ).fetchone()
            if not row:
                return None
            pid = dict(row)['id']
            updated = conn.execute(
                'UPDATE pending_jobs SET status=?, updated_at=? WHERE id=? AND status=?',
                (ItemStatus.PROCESSING.value, datetime.now().isoformat(), pid, ItemStatus.QUEUED.value)
            ).rowcount
            conn.commit()
            if updated == 0:
                return None
            full = conn.execute('SELECT * FROM pending_jobs WHERE id=?', (pid,)).fetchone()
            return dict(full) if full else None
        finally:
            conn.close()

    def count_by_status(self) -> Dict[ItemStatus, int]:
        conn = self._db()
        try:
            counts = {}
            for status in ItemStatus:
                row = conn.execute(
                    'SELECT COUNT(*) as cnt FROM pending_jobs WHERE status=?',
                    (status.value,)
                ).fetchone()
                counts[status] = row['cnt']
            return counts
        finally:
            conn.close()

    def reset_orphans(self) -> int:
        """Reset orphaned 'processing' items to 'queued'. Returns count."""
        conn = self._db()
        try:
            row = conn.execute(
                'SELECT COUNT(*) as cnt FROM pending_jobs WHERE status=?',
                (ItemStatus.PROCESSING.value,)
            ).fetchone()
            count = row['cnt']
            if count > 0:
                conn.execute(
                    'UPDATE pending_jobs SET status=?, error=NULL, updated_at=? WHERE status=?',
                    (ItemStatus.QUEUED.value, datetime.now().isoformat(), ItemStatus.PROCESSING.value)
                )
                conn.commit()
            return count
        finally:
            conn.close()


# ── Pending Companies Repository ──────────────────────────────────

class PendingCompanyRepository(IPendingRepository):
    """Repository for pending_companies table."""

    def __init__(self, db_path: str):
        self._db_path = db_path

    def _db(self) -> sqlite3.Connection:
        return _open_db(self._db_path)

    def get(self, pid: int) -> Optional[dict]:
        conn = self._db()
        try:
            row = conn.execute('SELECT * FROM pending_companies WHERE id=?', (pid,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def update_status(self, pid: int, status: ItemStatus, **fields) -> None:
        conn = self._db()
        try:
            sets = ['status=?', 'updated_at=?']
            vals = [status.value, datetime.now().isoformat()]
            for k, v in fields.items():
                sets.append(f'{k}=?')
                vals.append(v)
            vals.append(pid)
            conn.execute(f'UPDATE pending_companies SET {",".join(sets)} WHERE id=?', vals)
            conn.commit()
        finally:
            conn.close()

    def update_step(self, pid: int, step: str, val: int, **fields) -> None:
        conn = self._db()
        try:
            sets = [f'{step}=?', 'updated_at=?']
            vals = [val, datetime.now().isoformat()]
            for k, v in fields.items():
                sets.append(f'{k}=?')
                vals.append(v)
            vals.append(pid)
            conn.execute(f'UPDATE pending_companies SET {",".join(sets)} WHERE id=?', vals)
            conn.commit()
        finally:
            conn.close()

    def append_log(self, pid: int, entry: WorkflowLogEntry) -> None:
        conn = self._db()
        try:
            row = conn.execute('SELECT workflow_log FROM pending_companies WHERE id=?', (pid,)).fetchone()
            logs = json.loads(row['workflow_log'] or '[]') if row else []
            logs.append(entry.to_dict())
            conn.execute('UPDATE pending_companies SET workflow_log=? WHERE id=?', (json.dumps(logs), pid))
            conn.commit()
        finally:
            conn.close()

    def get_logs(self, pid: int) -> List[WorkflowLogEntry]:
        conn = self._db()
        try:
            row = conn.execute('SELECT workflow_log FROM pending_companies WHERE id=?', (pid,)).fetchone()
            if not row:
                return []
            logs = json.loads(row['workflow_log'] or '[]')
            return [WorkflowLogEntry.from_dict(e) for e in logs]
        finally:
            conn.close()

    def claim_next(self) -> Optional[dict]:
        conn = self._db()
        try:
            row = conn.execute(
                "SELECT id FROM pending_companies WHERE status='queued' ORDER BY created_at ASC LIMIT 1"
            ).fetchone()
            if not row:
                return None
            pid = dict(row)['id']
            updated = conn.execute(
                'UPDATE pending_companies SET status=?, updated_at=? WHERE id=? AND status=?',
                (ItemStatus.PROCESSING.value, datetime.now().isoformat(), pid, ItemStatus.QUEUED.value)
            ).rowcount
            conn.commit()
            if updated == 0:
                return None
            full = conn.execute('SELECT * FROM pending_companies WHERE id=?', (pid,)).fetchone()
            result = dict(full) if full else None
            if result:
                result['table'] = 'pending_companies'
            return result
        finally:
            conn.close()

    def count_by_status(self) -> Dict[ItemStatus, int]:
        conn = self._db()
        try:
            counts = {}
            for status in ItemStatus:
                row = conn.execute(
                    'SELECT COUNT(*) as cnt FROM pending_companies WHERE status=?',
                    (status.value,)
                ).fetchone()
                counts[status] = row['cnt']
            return counts
        finally:
            conn.close()

    def reset_orphans(self) -> int:
        conn = self._db()
        try:
            row = conn.execute(
                'SELECT COUNT(*) as cnt FROM pending_companies WHERE status=?',
                (ItemStatus.PROCESSING.value,)
            ).fetchone()
            count = row['cnt']
            if count > 0:
                conn.execute(
                    'UPDATE pending_companies SET status=?, error=NULL, updated_at=? WHERE status=?',
                    (ItemStatus.QUEUED.value, datetime.now().isoformat(), ItemStatus.PROCESSING.value)
                )
                conn.commit()
            return count
        finally:
            conn.close()


# ── Job Results Repository ────────────────────────────────────────

class JobRepository(IJobRepository):
    """Repository for jobs, summaries, and resumes tables."""

    def __init__(self, db_path: str):
        self._db_path = db_path

    def _db(self) -> sqlite3.Connection:
        return _open_db(self._db_path)

    def get_next_num(self) -> int:
        conn = self._db()
        try:
            row = conn.execute('SELECT MAX(num) FROM jobs').fetchone()
            return (row[0] or 0) + 1
        finally:
            conn.close()

    def get_by_url(self, url: str) -> Optional[dict]:
        conn = self._db()
        try:
            row = conn.execute('SELECT num, company, url, score, match FROM jobs WHERE url=? AND deleted=0', (url,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def insert(self, job_data: dict) -> int:
        conn = self._db()
        try:
            now = datetime.now().isoformat()
            conn.execute(
                '''INSERT OR REPLACE INTO jobs
                   (num, company, role, location, match, score, salary, stack, visa,
                    applicants, posted, industry, domain, notes, action, url,
                    work_type, workflow_log, created_at, posted_at, locations, deleted,
                    employment_type, work_types, raw_description, structured_description,
                    raw_file_path, structured_file_path, rescoring, success,
                    adv_at, see_at, apply_reason, company_url, linkedin_url,
                    apply_time, response_time, response_status,
                    fit_score, success_score, overall_score, company_id)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (job_data['num'], job_data.get('company'), job_data.get('role'),
                 job_data.get('location'), job_data.get('match'), job_data.get('score'),
                 job_data.get('salary'), job_data.get('stack'), job_data.get('visa'),
                 job_data.get('applicants'), job_data.get('posted'),
                 job_data.get('industry'), job_data.get('domain'),
                 job_data.get('notes'), job_data.get('action'), job_data.get('url'),
                 job_data.get('work_type', 'On-site'), job_data.get('workflow_log', '[]'),
                 job_data.get('created_at', now), job_data.get('posted_at'),
                 json.dumps(job_data.get('locations', []), ensure_ascii=False),
                 job_data.get('deleted', 0),
                 job_data.get('employment_type', 'Full-time'),
                 json.dumps(job_data.get('work_types', []), ensure_ascii=False),
                 job_data.get('raw_description'), job_data.get('structured_description'),
                 job_data.get('raw_file_path'), job_data.get('structured_file_path'),
                 job_data.get('rescoring', 0), job_data.get('success'),
                 job_data.get('adv_at'), job_data.get('see_at'),
                 job_data.get('apply_reason'), job_data.get('company_url'),
                 job_data.get('linkedin_url'), job_data.get('apply_time'),
                 job_data.get('response_time'), job_data.get('response_status'),
                 job_data.get('fit_score'), job_data.get('success_score'),
                 job_data.get('overall_score'), job_data.get('company_id'))
            )
            conn.commit()
            return job_data['num']
        finally:
            conn.close()

    def insert_summary(self, d: dict) -> None:
        conn = self._db()
        try:
            conn.execute(
                'INSERT OR REPLACE INTO summaries VALUES (?,?,?,?,?,?,?,?,?)',
                (d['num'], d.get('company'), d.get('match'), d.get('score'),
                 d.get('summary'), d.get('stack'), d.get('resumeFit'),
                 d.get('note'), d.get('url'))
            )
            conn.commit()
        finally:
            conn.close()

    def insert_resume(self, d: dict) -> None:
        conn = self._db()
        try:
            conn.execute(
                'INSERT OR REPLACE INTO resumes (id, title, company, role, content, version, raw_text, created_at, job_num) VALUES (?,?,?,?,?,?,?,?,?)',
                (d['id'], d.get('title'), d.get('company'), d.get('role'),
                 d.get('content'), d.get('version', 1), d.get('raw_text'),
                 d.get('created_at'), d.get('job_num'))
            )
            conn.commit()
        finally:
            conn.close()

    def save_workflow_log(self, num: int, log_json: str) -> None:
        conn = self._db()
        try:
            conn.execute('UPDATE jobs SET workflow_log=? WHERE num=?', (log_json, num))
            conn.commit()
        finally:
            conn.close()

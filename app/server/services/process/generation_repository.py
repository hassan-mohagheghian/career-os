"""
Unified Generation History Repository — reads from ALL source tables.

DDD: Repository pattern for the generation history projection.
SOLID: Single responsibility — only reads and normalizes generation history.
"""

from __future__ import annotations

import sqlite3
import time
from typing import Optional, List, Dict

from .generation_models import GenerationHistoryItem


def _open_db(db_path: str) -> sqlite3.Connection:
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


class GenerationHistoryRepository:
    """Reads generation history from all 5 source tables and normalizes.

    DDD: Read-only repository for the generation history projection.
    SRP: Only handles reading and normalizing generation history.
    OCP: New source tables added via new _query_* methods.

    Accepts either a db_path (str) or an existing connection.
    """

    def __init__(self, db_or_path):
        if isinstance(db_or_path, str):
            self._db_path = db_or_path
            self._conn = None
        else:
            self._db_path = None
            self._conn = db_or_path

    def _db(self) -> sqlite3.Connection:
        if self._conn is not None:
            return self._conn
        return _open_db(self._db_path)

    def _owns_conn(self) -> bool:
        """Whether we own the connection and should close it."""
        return self._db_path is not None

    def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        source_filter: Optional[str] = None,
    ) -> Dict[str, any]:
        all_items: List[GenerationHistoryItem] = []

        if source_filter is None or source_filter == 'job-processing':
            all_items.extend(self._query_pending_jobs())
        if source_filter is None or source_filter == 'company-processing':
            all_items.extend(self._query_pending_companies())
        if source_filter is None or source_filter == 'generation':
            all_items.extend(self._query_pending_generations())
        if source_filter is None or source_filter == 'roadmap':
            all_items.extend(self._query_roadmap_jobs())
        if source_filter is None or source_filter == 'insights':
            all_items.extend(self._query_insight_runs())

        def sort_key(item: GenerationHistoryItem) -> str:
            return item.started_at or item.completed_at or ''

        all_items.sort(key=sort_key, reverse=True)

        total = len(all_items)
        paginated = all_items[offset:offset + limit]

        return {'items': paginated, 'total': total}

    def _query_pending_jobs(self) -> List[GenerationHistoryItem]:
        items = []
        try:
            conn = self._db()
            try:
                rows = conn.execute(
                    "SELECT id, company, status, error, session_id, "
                    "created_at, updated_at "
                    "FROM pending_jobs ORDER BY created_at DESC LIMIT 200"
                ).fetchall()
                for row in rows:
                    r = dict(row)
                    items.append(GenerationHistoryItem(
                        id=r['id'],
                        source='job-processing',
                        title=r.get('company') or 'Job',
                        status=r.get('status', 'unknown'),
                        started_at=r.get('created_at'),
                        completed_at=r.get('updated_at') if r.get('status') in ('done', 'failed') else None,
                        error=r.get('error'),
                        session_id=r.get('session_id'),
                    ))
            finally:
                if self._owns_conn():
                    conn.close()
        except Exception:
            pass
        return items

    def _query_pending_companies(self) -> List[GenerationHistoryItem]:
        items = []
        try:
            conn = self._db()
            try:
                rows = conn.execute(
                    "SELECT id, company_name, status, error, session_id, "
                    "created_at, updated_at "
                    "FROM pending_companies ORDER BY created_at DESC LIMIT 200"
                ).fetchall()
                for row in rows:
                    r = dict(row)
                    items.append(GenerationHistoryItem(
                        id=r['id'],
                        source='company-processing',
                        title=r.get('company_name') or 'Company',
                        status=r.get('status', 'unknown'),
                        started_at=r.get('created_at'),
                        completed_at=r.get('updated_at') if r.get('status') in ('done', 'failed') else None,
                        error=r.get('error'),
                        session_id=r.get('session_id'),
                    ))
            finally:
                if self._owns_conn():
                    conn.close()
        except Exception:
            pass
        return items

    def _query_pending_generations(self) -> List[GenerationHistoryItem]:
        items = []
        try:
            conn = self._db()
            try:
                rows = conn.execute(
                    "SELECT id, type, status, error, session_id, "
                    "created_at, updated_at "
                    "FROM pending_generations ORDER BY created_at DESC LIMIT 200"
                ).fetchall()
                for row in rows:
                    r = dict(row)
                    gen_type = r.get('type', 'unknown')
                    title_map = {
                        'resume': 'Resume',
                        'cover': 'Cover Letter',
                        'cover_letter': 'Cover Letter',
                    }
                    items.append(GenerationHistoryItem(
                        id=r['id'],
                        source='generation',
                        title=title_map.get(gen_type, gen_type.title()),
                        status=r.get('status', 'unknown'),
                        started_at=r.get('created_at'),
                        completed_at=r.get('updated_at') if r.get('status') in ('done', 'failed') else None,
                        error=r.get('error'),
                        session_id=r.get('session_id'),
                    ))
            finally:
                if self._owns_conn():
                    conn.close()
        except Exception:
            pass
        return items

    def _query_roadmap_jobs(self) -> List[GenerationHistoryItem]:
        items = []
        try:
            conn = self._db()
            try:
                cols = {r[1] for r in conn.execute("PRAGMA table_info(skill_roadmap_jobs)").fetchall()}
                has_provider = 'provider_name' in cols

                if has_provider:
                    rows = conn.execute(
                        "SELECT id, skill_name, job_type, status, error, session_id, "
                        "provider_name, started_at, completed_at "
                        "FROM skill_roadmap_jobs ORDER BY created_at DESC LIMIT 200"
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT id, skill_name, job_type, status, error, session_id, "
                        "started_at, completed_at "
                        "FROM skill_roadmap_jobs ORDER BY created_at DESC LIMIT 200"
                    ).fetchall()
                for row in rows:
                    r = dict(row)
                    skill = r.get('skill_name', '?')
                    job_type = r.get('job_type', 'generate')
                    items.append(GenerationHistoryItem(
                        id=r['id'],
                        source='roadmap',
                        title=f"{skill} ({job_type})",
                        status=r.get('status', 'unknown'),
                        started_at=r.get('started_at'),
                        completed_at=r.get('completed_at'),
                        error=r.get('error'),
                        session_id=r.get('session_id'),
                        provider=r.get('provider_name'),
                    ))
            finally:
                if self._owns_conn():
                    conn.close()
        except Exception:
            pass
        return items

    def _query_insight_runs(self) -> List[GenerationHistoryItem]:
        items = []
        try:
            conn = self._db()
            try:
                rows = conn.execute(
                    "SELECT id, insight_type, status, error_message, session_id, "
                    "started_at, completed_at "
                    "FROM career_insight_runs ORDER BY started_at DESC LIMIT 200"
                ).fetchall()
                for row in rows:
                    r = dict(row)
                    insight_type = r.get('insight_type', 'unknown')
                    title_map = {
                        'overview': 'Overview',
                        'opportunities': 'Opportunities',
                        'companies': 'Companies',
                        'skills': 'Skills',
                        'skills_intel': 'Skills Intel',
                        'market': 'Market',
                        'networking': 'Networking',
                        'all': 'All Insights',
                    }
                    items.append(GenerationHistoryItem(
                        id=r['id'],
                        source='insights',
                        title=title_map.get(insight_type, insight_type.title()),
                        status=r.get('status', 'unknown'),
                        started_at=r.get('started_at'),
                        completed_at=r.get('completed_at'),
                        error=r.get('error_message'),
                        session_id=r.get('session_id'),
                    ))
            finally:
                if self._owns_conn():
                    conn.close()
        except Exception:
            pass
        return items

    # ── Context-filtered queries for local history ────────────────────

    def get_for_job(self, job_num: int, limit: int = 50) -> Dict[str, any]:
        """Get generation history for a specific job (resume + cover + processing)."""
        all_items: List[GenerationHistoryItem] = []
        all_items.extend(self._query_pending_generations_for_job(job_num))
        all_items.extend(self._query_pending_jobs_for_job(job_num))
        all_items.sort(key=lambda i: i.started_at or i.completed_at or '', reverse=True)
        return {'items': all_items[:limit], 'total': len(all_items)}

    def get_for_company(self, company_id: int, limit: int = 50) -> Dict[str, any]:
        """Get generation history for a specific company."""
        all_items: List[GenerationHistoryItem] = []
        all_items.extend(self._query_pending_companies_for_company(company_id))
        all_items.sort(key=lambda i: i.started_at or i.completed_at or '', reverse=True)
        return {'items': all_items[:limit], 'total': len(all_items)}

    def get_for_skill(self, skill_name: str, limit: int = 50) -> Dict[str, any]:
        """Get generation history for a specific skill."""
        all_items: List[GenerationHistoryItem] = []
        all_items.extend(self._query_roadmap_jobs_for_skill(skill_name))
        all_items.sort(key=lambda i: i.started_at or i.completed_at or '', reverse=True)
        return {'items': all_items[:limit], 'total': len(all_items)}

    def get_for_insight(self, insight_type: str, limit: int = 50) -> Dict[str, any]:
        """Get generation history for a specific insight section."""
        all_items: List[GenerationHistoryItem] = []
        all_items.extend(self._query_insight_runs_for_type(insight_type))
        all_items.sort(key=lambda i: i.started_at or i.completed_at or '', reverse=True)
        return {'items': all_items[:limit], 'total': len(all_items)}

    def get_active_count(
        self,
        context: str,
        job_num: Optional[int] = None,
        company_id: Optional[int] = None,
        skill_name: Optional[str] = None,
        insight_type: Optional[str] = None,
    ) -> int:
        """Count currently running/queued items for a context."""
        count = 0
        try:
            conn = self._db()
            try:
                if context == 'job' and job_num is not None:
                    row = conn.execute(
                        "SELECT COUNT(*) FROM pending_generations "
                        "WHERE job_num=? AND status IN ('queued', 'processing')",
                        (job_num,),
                    ).fetchone()
                    count += row[0] if row else 0
                    row2 = conn.execute(
                        "SELECT COUNT(*) FROM pending_jobs "
                        "WHERE job_num=? AND status IN ('queued', 'processing')",
                        (job_num,),
                    ).fetchone()
                    count += row2[0] if row2 else 0
                elif context == 'company' and company_id is not None:
                    row = conn.execute(
                        "SELECT COUNT(*) FROM pending_companies "
                        "WHERE company_id=? AND status IN ('queued', 'processing')",
                        (company_id,),
                    ).fetchone()
                    count = row[0] if row else 0
                elif context == 'skill' and skill_name is not None:
                    row = conn.execute(
                        "SELECT COUNT(*) FROM skill_roadmap_jobs "
                        "WHERE LOWER(skill_name)=LOWER(?) AND status IN ('queued', 'running')",
                        (skill_name,),
                    ).fetchone()
                    count = row[0] if row else 0
                elif context == 'insight' and insight_type is not None:
                    row = conn.execute(
                        "SELECT COUNT(*) FROM career_insight_runs "
                        "WHERE insight_type=? AND status='processing'",
                        (insight_type,),
                    ).fetchone()
                    count = row[0] if row else 0
            finally:
                if self._owns_conn():
                    conn.close()
        except Exception:
            pass
        return count

    def _query_pending_generations_for_job(self, job_num: int) -> List[GenerationHistoryItem]:
        items = []
        try:
            conn = self._db()
            try:
                rows = conn.execute(
                    "SELECT id, type, status, error, session_id, "
                    "created_at, updated_at "
                    "FROM pending_generations WHERE job_num=? ORDER BY created_at DESC",
                    (job_num,),
                ).fetchall()
                for row in rows:
                    r = dict(row)
                    gen_type = r.get('type', 'unknown')
                    title_map = {
                        'resume': 'Resume',
                        'cover': 'Cover Letter',
                        'cover_letter': 'Cover Letter',
                    }
                    items.append(GenerationHistoryItem(
                        id=r['id'],
                        source='generation',
                        title=title_map.get(gen_type, gen_type.title()),
                        status=r.get('status', 'unknown'),
                        started_at=r.get('created_at'),
                        completed_at=r.get('updated_at') if r.get('status') in ('done', 'failed') else None,
                        error=r.get('error'),
                        session_id=r.get('session_id'),
                    ))
            finally:
                if self._owns_conn():
                    conn.close()
        except Exception:
            pass
        return items

    def _query_pending_jobs_for_job(self, job_num: int) -> List[GenerationHistoryItem]:
        items = []
        try:
            conn = self._db()
            try:
                rows = conn.execute(
                    "SELECT id, company, status, error, session_id, "
                    "created_at, updated_at "
                    "FROM pending_jobs WHERE job_num=? ORDER BY created_at DESC",
                    (job_num,),
                ).fetchall()
                for row in rows:
                    r = dict(row)
                    items.append(GenerationHistoryItem(
                        id=r['id'],
                        source='job-processing',
                        title=r.get('company') or 'Job Processing',
                        status=r.get('status', 'unknown'),
                        started_at=r.get('created_at'),
                        completed_at=r.get('updated_at') if r.get('status') in ('done', 'failed') else None,
                        error=r.get('error'),
                        session_id=r.get('session_id'),
                    ))
            finally:
                if self._owns_conn():
                    conn.close()
        except Exception:
            pass
        return items

    def _query_pending_companies_for_company(self, company_id: int) -> List[GenerationHistoryItem]:
        items = []
        try:
            conn = self._db()
            try:
                rows = conn.execute(
                    "SELECT id, company_name, status, error, session_id, "
                    "created_at, updated_at "
                    "FROM pending_companies WHERE company_id=? ORDER BY created_at DESC",
                    (company_id,),
                ).fetchall()
                for row in rows:
                    r = dict(row)
                    items.append(GenerationHistoryItem(
                        id=r['id'],
                        source='company-processing',
                        title=r.get('company_name') or 'Company Processing',
                        status=r.get('status', 'unknown'),
                        started_at=r.get('created_at'),
                        completed_at=r.get('updated_at') if r.get('status') in ('done', 'failed') else None,
                        error=r.get('error'),
                        session_id=r.get('session_id'),
                    ))
            finally:
                if self._owns_conn():
                    conn.close()
        except Exception:
            pass
        return items

    def _query_roadmap_jobs_for_skill(self, skill_name: str) -> List[GenerationHistoryItem]:
        items = []
        try:
            conn = self._db()
            try:
                cols = {r[1] for r in conn.execute("PRAGMA table_info(skill_roadmap_jobs)").fetchall()}
                has_provider = 'provider_name' in cols
                if has_provider:
                    rows = conn.execute(
                        "SELECT id, skill_name, job_type, status, error, session_id, "
                        "provider_name, started_at, completed_at "
                        "FROM skill_roadmap_jobs WHERE LOWER(skill_name)=LOWER(?) "
                        "ORDER BY created_at DESC",
                        (skill_name,),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT id, skill_name, job_type, status, error, session_id, "
                        "started_at, completed_at "
                        "FROM skill_roadmap_jobs WHERE LOWER(skill_name)=LOWER(?) "
                        "ORDER BY created_at DESC",
                        (skill_name,),
                    ).fetchall()
                for row in rows:
                    r = dict(row)
                    job_type = r.get('job_type', 'generate')
                    items.append(GenerationHistoryItem(
                        id=r['id'],
                        source='roadmap',
                        title=f"{skill_name} ({job_type})",
                        status=r.get('status', 'unknown'),
                        started_at=r.get('started_at'),
                        completed_at=r.get('completed_at'),
                        error=r.get('error'),
                        session_id=r.get('session_id'),
                        provider=r.get('provider_name'),
                    ))
            finally:
                if self._owns_conn():
                    conn.close()
        except Exception:
            pass
        return items

    def _query_insight_runs_for_type(self, insight_type: str) -> List[GenerationHistoryItem]:
        items = []
        try:
            conn = self._db()
            try:
                rows = conn.execute(
                    "SELECT id, insight_type, status, error_message, session_id, "
                    "started_at, completed_at "
                    "FROM career_insight_runs WHERE insight_type=? ORDER BY started_at DESC",
                    (insight_type,),
                ).fetchall()
                for row in rows:
                    r = dict(row)
                    title_map = {
                        'overview': 'Overview',
                        'opportunities': 'Opportunities',
                        'companies': 'Companies',
                        'skills': 'Skills',
                        'skills_intel': 'Skills Intel',
                        'market': 'Market',
                        'networking': 'Networking',
                        'all': 'All Insights',
                    }
                    items.append(GenerationHistoryItem(
                        id=r['id'],
                        source='insights',
                        title=title_map.get(insight_type, insight_type.title()),
                        status=r.get('status', 'unknown'),
                        started_at=r.get('started_at'),
                        completed_at=r.get('completed_at'),
                        error=r.get('error_message'),
                        session_id=r.get('session_id'),
                    ))
            finally:
                if self._owns_conn():
                    conn.close()
        except Exception:
            pass
        return items

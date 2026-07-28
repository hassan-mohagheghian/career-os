"""
SQLAlchemy repository implementations — persistence layer.

DDD: Repositories are the only place that touches the database directly.
Domain models flow in, SQLAlchemy ORM handles the rest.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional, List, Dict

from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from .interfaces import IPendingRepository, IJobRepository
from .models import ItemStatus, WorkflowLogEntry

from pending.infrastructure.models.pending_model import PendingJobModel, PendingCompanyModel
from jobs.infrastructure.models.job_model import JobModel
from shared.infrastructure.database.models.misc_models import SummaryModel, ResumeModel


# ── Pending Jobs Repository ───────────────────────────────────────

class PendingJobRepository(IPendingRepository):
    """Repository for pending_jobs table via SQLAlchemy."""

    def __init__(self, session: Session):
        self._session = session

    def get(self, pid: int) -> Optional[dict]:
        row = self._session.query(PendingJobModel).filter(PendingJobModel.id == pid).first()
        if not row:
            return None
        return self._to_dict(row)

    def update_status(self, pid: int, status: ItemStatus, **fields) -> None:
        m = self._session.query(PendingJobModel).filter(PendingJobModel.id == pid).first()
        if not m:
            return
        m.status = status.value
        m.updated_at = datetime.now().isoformat()
        for k, v in fields.items():
            if hasattr(m, k):
                setattr(m, k, v)
        self._session.commit()

    def update_step(self, pid: int, step: str, val: int, **fields) -> None:
        m = self._session.query(PendingJobModel).filter(PendingJobModel.id == pid).first()
        if not m:
            return
        setattr(m, step, val)
        m.updated_at = datetime.now().isoformat()
        for k, v in fields.items():
            if hasattr(m, k):
                setattr(m, k, v)
        self._session.commit()

    def append_log(self, pid: int, entry: WorkflowLogEntry) -> None:
        m = self._session.query(PendingJobModel).filter(PendingJobModel.id == pid).first()
        if not m:
            return
        logs = json.loads(m.workflow_log or '[]')
        logs.append(entry.to_dict())
        m.workflow_log = json.dumps(logs)
        self._session.commit()

    def get_logs(self, pid: int) -> List[WorkflowLogEntry]:
        m = self._session.query(PendingJobModel).filter(PendingJobModel.id == pid).first()
        if not m:
            return []
        logs = json.loads(m.workflow_log or '[]')
        return [WorkflowLogEntry.from_dict(e) for e in logs]

    def claim_next(self) -> Optional[dict]:
        m = self._session.query(PendingJobModel).filter(
            PendingJobModel.status == ItemStatus.QUEUED.value
        ).order_by(PendingJobModel.queue_order.asc(), PendingJobModel.created_at.asc()).first()
        if not m:
            return None
        m.status = ItemStatus.PROCESSING.value
        m.updated_at = datetime.now().isoformat()
        self._session.commit()
        self._session.refresh(m)
        return self._to_dict(m)

    def count_by_status(self) -> Dict[ItemStatus, int]:
        counts = {}
        for status in ItemStatus:
            cnt = self._session.query(PendingJobModel).filter(
                PendingJobModel.status == status.value
            ).count()
            counts[status] = cnt
        return counts

    def reset_orphans(self) -> int:
        count = self._session.query(PendingJobModel).filter(
            PendingJobModel.status == ItemStatus.PROCESSING.value
        ).count()
        if count > 0:
            self._session.query(PendingJobModel).filter(
                PendingJobModel.status == ItemStatus.PROCESSING.value
            ).update({
                'status': ItemStatus.QUEUED.value,
                'error': None,
                'updated_at': datetime.now().isoformat(),
            })
            self._session.commit()
        return count

    @staticmethod
    def _to_dict(m: PendingJobModel) -> dict:
        return {
            'id': m.id, 'url': m.url, 'source': m.source, 'status': m.status,
            'version': m.version, 'notes': m.notes, 'links': m.links,
            'job_num': m.job_num, 'company': m.company,
            'step_fetch': m.step_fetch, 'step_resume': m.step_resume,
            'step_extract_raw': m.step_extract_raw, 'step_extract_struct': m.step_extract_struct,
            'step_cover': m.step_cover, 'step_analyze': m.step_analyze,
            'step_db': m.step_db, 'step_done': m.step_done,
            'workflow_log': m.workflow_log, 'error': m.error,
            'queue_order': m.queue_order, 'session_id': m.session_id,
            'created_at': m.created_at, 'updated_at': m.updated_at,
        }


# ── Pending Companies Repository ──────────────────────────────────

class PendingCompanyRepository(IPendingRepository):
    """Repository for pending_companies table via SQLAlchemy."""

    def __init__(self, session: Session):
        self._session = session

    def get(self, pid: int) -> Optional[dict]:
        row = self._session.query(PendingCompanyModel).filter(PendingCompanyModel.id == pid).first()
        if not row:
            return None
        return self._to_dict(row)

    def update_status(self, pid: int, status: ItemStatus, **fields) -> None:
        m = self._session.query(PendingCompanyModel).filter(PendingCompanyModel.id == pid).first()
        if not m:
            return
        m.status = status.value
        m.updated_at = datetime.now().isoformat()
        for k, v in fields.items():
            if hasattr(m, k):
                setattr(m, k, v)
        self._session.commit()

    def update_step(self, pid: int, step: str, val: int, **fields) -> None:
        m = self._session.query(PendingCompanyModel).filter(PendingCompanyModel.id == pid).first()
        if not m:
            return
        setattr(m, step, val)
        m.updated_at = datetime.now().isoformat()
        for k, v in fields.items():
            if hasattr(m, k):
                setattr(m, k, v)
        self._session.commit()

    def append_log(self, pid: int, entry: WorkflowLogEntry) -> None:
        m = self._session.query(PendingCompanyModel).filter(PendingCompanyModel.id == pid).first()
        if not m:
            return
        logs = json.loads(m.workflow_log or '[]')
        logs.append(entry.to_dict())
        m.workflow_log = json.dumps(logs)
        self._session.commit()

    def get_logs(self, pid: int) -> List[WorkflowLogEntry]:
        m = self._session.query(PendingCompanyModel).filter(PendingCompanyModel.id == pid).first()
        if not m:
            return []
        logs = json.loads(m.workflow_log or '[]')
        return [WorkflowLogEntry.from_dict(e) for e in logs]

    def claim_next(self) -> Optional[dict]:
        m = self._session.query(PendingCompanyModel).filter(
            PendingCompanyModel.status == ItemStatus.QUEUED.value
        ).order_by(PendingCompanyModel.created_at.asc()).first()
        if not m:
            return None
        m.status = ItemStatus.PROCESSING.value
        m.updated_at = datetime.now().isoformat()
        self._session.commit()
        self._session.refresh(m)
        result = self._to_dict(m)
        result['table'] = 'pending_companies'
        return result

    def count_by_status(self) -> Dict[ItemStatus, int]:
        counts = {}
        for status in ItemStatus:
            cnt = self._session.query(PendingCompanyModel).filter(
                PendingCompanyModel.status == status.value
            ).count()
            counts[status] = cnt
        return counts

    def reset_orphans(self) -> int:
        count = self._session.query(PendingCompanyModel).filter(
            PendingCompanyModel.status == ItemStatus.PROCESSING.value
        ).count()
        if count > 0:
            self._session.query(PendingCompanyModel).filter(
                PendingCompanyModel.status == ItemStatus.PROCESSING.value
            ).update({
                'status': ItemStatus.QUEUED.value,
                'error': None,
                'updated_at': datetime.now().isoformat(),
            })
            self._session.commit()
        return count

    @staticmethod
    def _to_dict(m: PendingCompanyModel) -> dict:
        return {
            'id': m.id, 'input_text': m.input_text, 'source': m.source,
            'status': m.status, 'version': m.version,
            'notes': m.notes, 'links': m.links, 'input_type': m.input_type,
            'step_fetch': m.step_fetch, 'step_extract': m.step_extract,
            'step_analyze': m.step_analyze, 'step_save': m.step_save,
            'step_done': m.step_done, 'company_id': m.company_id,
            'company_name': m.company_name, 'error': m.error,
            'workflow_log': m.workflow_log, 'session_id': m.session_id,
            'created_at': m.created_at, 'updated_at': m.updated_at,
        }


# ── Job Results Repository ────────────────────────────────────────

class JobRepository(IJobRepository):
    """Repository for jobs, summaries, and resumes tables via SQLAlchemy."""

    def __init__(self, session: Session):
        self._session = session

    def get_next_num(self) -> int:
        max_num = self._session.query(func.max(JobModel.num)).scalar()
        return (max_num or 0) + 1

    def get_by_url(self, url: str) -> Optional[dict]:
        m = self._session.query(JobModel).filter(
            JobModel.url == url, JobModel.deleted == 0
        ).first()
        if not m:
            return None
        return {
            'num': m.num, 'company': m.company, 'url': m.url,
            'score': m.score, 'match': m.match,
        }

    def insert(self, job_data: dict) -> int:
        now = datetime.now().isoformat()
        existing = self._session.query(JobModel).filter(JobModel.num == job_data['num']).first()
        if existing:
            for k, v in job_data.items():
                if hasattr(existing, k):
                    setattr(existing, k, v)
        else:
            m = JobModel(
                num=job_data['num'],
                company=job_data.get('company'),
                role=job_data.get('role'),
                location=job_data.get('location'),
                match=job_data.get('match'),
                score=job_data.get('score'),
                salary=job_data.get('salary'),
                stack=job_data.get('stack'),
                visa=job_data.get('visa'),
                applicants=job_data.get('applicants'),
                posted=job_data.get('posted'),
                industry=job_data.get('industry'),
                domain=job_data.get('domain'),
                notes=job_data.get('notes'),
                action=job_data.get('action'),
                url=job_data.get('url'),
                work_type=job_data.get('work_type', 'On-site'),
                workflow_log=job_data.get('workflow_log', '[]'),
                created_at=job_data.get('created_at', now),
                posted_at=job_data.get('posted_at'),
                locations=json.dumps(job_data.get('locations', []), ensure_ascii=False),
                deleted=job_data.get('deleted', 0),
                employment_type=job_data.get('employment_type', 'Full-time'),
                work_types=json.dumps(job_data.get('work_types', []), ensure_ascii=False),
                raw_description=job_data.get('raw_description'),
                structured_description=job_data.get('structured_description'),
                raw_file_path=job_data.get('raw_file_path'),
                structured_file_path=job_data.get('structured_file_path'),
                rescoring=job_data.get('rescoring', 0),
                success=job_data.get('success'),
                adv_at=job_data.get('adv_at'),
                see_at=job_data.get('see_at'),
                apply_reason=job_data.get('apply_reason'),
                company_url=job_data.get('company_url'),
                linkedin_url=job_data.get('linkedin_url'),
                apply_time=job_data.get('apply_time'),
                response_time=job_data.get('response_time'),
                response_status=job_data.get('response_status'),
                fit_score=job_data.get('fit_score'),
                success_score=job_data.get('success_score'),
                overall_score=job_data.get('overall_score'),
                company_id=job_data.get('company_id'),
            )
            self._session.add(m)
        self._session.commit()
        return job_data['num']

    def insert_summary(self, d: dict) -> None:
        existing = self._session.query(SummaryModel).filter(SummaryModel.num == d['num']).first()
        if existing:
            existing.company = d.get('company')
            existing.match = d.get('match')
            existing.score = d.get('score')
            existing.summary = d.get('summary')
            existing.stack = d.get('stack')
            existing.resume_fit = d.get('resumeFit')
            existing.note = d.get('note')
            existing.url = d.get('url')
        else:
            m = SummaryModel(
                num=d['num'], company=d.get('company'), match=d.get('match'),
                score=d.get('score'), summary=d.get('summary'), stack=d.get('stack'),
                resume_fit=d.get('resumeFit'), note=d.get('note'), url=d.get('url'),
            )
            self._session.add(m)
        self._session.commit()

    def insert_resume(self, d: dict) -> None:
        existing = self._session.query(ResumeModel).filter(ResumeModel.id == d['id']).first()
        if existing:
            existing.title = d.get('title')
            existing.company = d.get('company')
            existing.role = d.get('role')
            existing.content = d.get('content')
            existing.version = d.get('version', 1)
            existing.raw_text = d.get('raw_text')
            existing.created_at = d.get('created_at')
            existing.job_num = d.get('job_num')
        else:
            m = ResumeModel(
                id=d['id'], title=d.get('title'), company=d.get('company'),
                role=d.get('role'), content=d.get('content'),
                version=d.get('version', 1), raw_text=d.get('raw_text'),
                created_at=d.get('created_at'), job_num=d.get('job_num'),
            )
            self._session.add(m)
        self._session.commit()

    def save_workflow_log(self, num: int, log_json: str) -> None:
        m = self._session.query(JobModel).filter(JobModel.num == num).first()
        if m:
            m.workflow_log = log_json
            self._session.commit()

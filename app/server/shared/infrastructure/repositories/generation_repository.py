"""
Unified Generation History Repository — reads from ALL source tables.

DDD: Repository pattern for the generation history projection.
SOLID: Single responsibility — only reads and normalizes generation history.
"""

from __future__ import annotations

from typing import Optional, List, Dict

from shared.domain.models.generation_models import GenerationHistoryItem
from dependencies import get_session_sync
from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository
from processing.infrastructure.repositories.sa_pending_repository import SQLAlchemyPendingRepository
from processing.infrastructure.repositories.sa_pending_generation_repository import SQLAlchemyPendingGenerationRepository
from skills.infrastructure.repositories.sa_skill_roadmap_job_repository import SQLAlchemySkillRoadmapJobRepository
from career.infrastructure.repositories.sa_career_insight_run_repository import SQLAlchemyCareerInsightRunRepository


class GenerationHistoryRepository:
    """Reads generation history from all 5 source tables and normalizes.

    DDD: Read-only repository for the generation history projection.
    SRP: Only handles reading and normalizing generation history.
    OCP: New source tables added via new _query_* methods.
    """

    def __init__(self, db_or_path=None):
        # Accept legacy signature but ignore it — we use SA sessions
        pass

    def _session(self):
        return get_session_sync()

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
            session = self._session()
            try:
                repo = SQLAlchemyPendingRepository(session)
                rows = repo.get_all_for_stream("pending_jobs")[:200]
                for r in rows:
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
                session.close()
        except Exception:
            pass
        return items

    def _query_pending_companies(self) -> List[GenerationHistoryItem]:
        items = []
        try:
            session = self._session()
            try:
                repo = SQLAlchemyPendingRepository(session)
                rows = repo.get_all_for_stream("pending_companies")[:200]
                for r in rows:
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
                session.close()
        except Exception:
            pass
        return items

    def _query_pending_generations(self) -> List[GenerationHistoryItem]:
        items = []
        try:
            session = self._session()
            try:
                repo = SQLAlchemyPendingGenerationRepository(session)
                rows = repo.get_all(limit=200)
                for r in rows:
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
                session.close()
        except Exception:
            pass
        return items

    def _query_roadmap_jobs(self) -> List[GenerationHistoryItem]:
        items = []
        try:
            session = self._session()
            try:
                repo = SQLAlchemySkillRoadmapJobRepository(session)
                rows = repo.get_all(limit=200)
                for r in rows:
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
                session.close()
        except Exception:
            pass
        return items

    def _query_insight_runs(self) -> List[GenerationHistoryItem]:
        items = []
        try:
            session = self._session()
            try:
                repo = SQLAlchemyCareerInsightRunRepository(session)
                rows = repo.get_runs(limit=200)
                for r in rows:
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
                session.close()
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
            session = self._session()
            try:
                if context == 'job' and job_num is not None:
                    repo_gen = SQLAlchemyPendingGenerationRepository(session)
                    count += repo_gen.get_active_count(job_num)
                    repo_pending = SQLAlchemyPendingRepository(session)
                    # Count pending jobs with job_num in processing/queued status
                    from processing.infrastructure.models.pending_model import PendingJobModel
                    count += session.query(PendingJobModel).filter(
                        PendingJobModel.job_num == job_num,
                        PendingJobModel.status.in_(["processing", "queued"]),
                    ).count()
                elif context == 'company' and company_id is not None:
                    from processing.infrastructure.models.pending_model import PendingCompanyModel
                    count = session.query(PendingCompanyModel).filter(
                        PendingCompanyModel.company_id == company_id,
                        PendingCompanyModel.status.in_(["processing", "queued"]),
                    ).count()
                elif context == 'skill' and skill_name is not None:
                    from shared.infrastructure.database.models.misc_models import SkillRoadmapJobModel
                    count = session.query(SkillRoadmapJobModel).filter(
                        SkillRoadmapJobModel.skill_name.ilike(skill_name),
                        SkillRoadmapJobModel.status.in_(["queued", "running"]),
                    ).count()
                elif context == 'insight' and insight_type is not None:
                    from career.infrastructure.models.insight_model import CareerInsightRunModel
                    count = session.query(CareerInsightRunModel).filter(
                        CareerInsightRunModel.insight_type == insight_type,
                        CareerInsightRunModel.status == "processing",
                    ).count()
            finally:
                session.close()
        except Exception:
            pass
        return count

    def _query_pending_generations_for_job(self, job_num: int) -> List[GenerationHistoryItem]:
        items = []
        try:
            session = self._session()
            try:
                repo = SQLAlchemyPendingGenerationRepository(session)
                rows = repo.get_history_for_job(job_num)
                for r in rows:
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
                session.close()
        except Exception:
            pass
        return items

    def _query_pending_jobs_for_job(self, job_num: int) -> List[GenerationHistoryItem]:
        items = []
        try:
            session = self._session()
            try:
                from processing.infrastructure.models.pending_model import PendingJobModel
                rows = session.query(PendingJobModel).filter(
                    PendingJobModel.job_num == job_num,
                ).order_by(PendingJobModel.created_at.desc()).all()
                from shared.infrastructure.database.mappers import pending_job_model_to_dict
                for r in rows:
                    d = pending_job_model_to_dict(r)
                    items.append(GenerationHistoryItem(
                        id=d['id'],
                        source='job-processing',
                        title=d.get('company') or 'Job Processing',
                        status=d.get('status', 'unknown'),
                        started_at=d.get('created_at'),
                        completed_at=d.get('updated_at') if d.get('status') in ('done', 'failed') else None,
                        error=d.get('error'),
                        session_id=d.get('session_id'),
                    ))
            finally:
                session.close()
        except Exception:
            pass
        return items

    def _query_pending_companies_for_company(self, company_id: int) -> List[GenerationHistoryItem]:
        items = []
        try:
            session = self._session()
            try:
                from processing.infrastructure.models.pending_model import PendingCompanyModel
                rows = session.query(PendingCompanyModel).filter(
                    PendingCompanyModel.company_id == company_id,
                ).order_by(PendingCompanyModel.created_at.desc()).all()
                from shared.infrastructure.database.mappers import pending_company_model_to_dict
                for r in rows:
                    d = pending_company_model_to_dict(r)
                    items.append(GenerationHistoryItem(
                        id=d['id'],
                        source='company-processing',
                        title=d.get('company_name') or 'Company Processing',
                        status=d.get('status', 'unknown'),
                        started_at=d.get('created_at'),
                        completed_at=d.get('updated_at') if d.get('status') in ('done', 'failed') else None,
                        error=d.get('error'),
                        session_id=d.get('session_id'),
                    ))
            finally:
                session.close()
        except Exception:
            pass
        return items

    def _query_roadmap_jobs_for_skill(self, skill_name: str) -> List[GenerationHistoryItem]:
        items = []
        try:
            session = self._session()
            try:
                repo = SQLAlchemySkillRoadmapJobRepository(session)
                rows = repo.get_for_skill(skill_name)
                for r in rows:
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
                session.close()
        except Exception:
            pass
        return items

    def _query_insight_runs_for_type(self, insight_type: str) -> List[GenerationHistoryItem]:
        items = []
        try:
            session = self._session()
            try:
                repo = SQLAlchemyCareerInsightRunRepository(session)
                rows = repo.get_runs(insight_type=insight_type)
                for r in rows:
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
                session.close()
        except Exception:
            pass
        return items

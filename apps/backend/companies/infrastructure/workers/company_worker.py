"""
Background worker that processes pending companies.
Fetches company URL or uses manual notes, runs AI extraction and analysis,
then saves structured company intelligence to DB.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

from shared.infrastructure.process.worker_base import WorkerBase
from shared.infrastructure.process.models import WorkflowStep, JobStatus
from shared.infrastructure.prompts.loader import load_prompt
from shared.infrastructure.process.logging_config import get_logger
from shared.infrastructure.process_utils import broadcaster
from shared.infrastructure.process.models import StatusUpdate, LogEntry, ProcessingComplete, ProcessingError
from shared.infrastructure.ai.compat import get_llm_service
from ai.infrastructure.tools.fetch import fetch_page
from ai.infrastructure.graphs.runtime.state import create_initial_state
from ai.infrastructure.graphs.company.graph import build_company_processing_graph

from dependencies import get_session_sync
from shared.infrastructure.process.repository import PendingCompanyRepository
from companies.infrastructure.repositories.sa_company_repository import SQLAlchemyCompanyRepository
from companies.infrastructure.repositories.sa_company_intelligence_repository import SQLAlchemyCompanyIntelligenceRepository
from companies.infrastructure.repositories.sa_company_link_repository import SQLAlchemyCompanyLinkRepository
from companies.infrastructure.models.company_model import CompanyModel

log = get_logger('company_worker')

_file_dir = os.path.dirname(os.path.abspath(__file__))
_server_dir = os.path.join(_file_dir, '..')
PROJECT_ROOT = os.path.abspath(os.path.join(_file_dir, '..', '..', '..'))


# ── Legacy Procedural Helpers (kept for backward compatibility) ──────


def _update_step(pid, step, val, status=None, company_name=None, company_id=None, error=None):
    session = get_session_sync()
    try:
        pending_repo = PendingCompanyRepository(session)
        extra = {}
        if status:
            extra['status'] = status
        if company_name:
            extra['company_name'] = company_name
        if company_id:
            extra['company_id'] = company_id
        if error:
            extra['error'] = error
        extra['updated_at'] = datetime.now().isoformat()
        pending_repo.update_step(pid, step, val, **extra)
    finally:
        session.close()
    broadcaster.step_update(StatusUpdate(
        table='company', pid=pid, step=step, val=val,
        extra=extra or None,
    ))


def _mark(pid, step):
    _update_step(pid, step, 1)


def _save_session_id(pid, session_id):
    session = get_session_sync()
    try:
        pending_repo = PendingCompanyRepository(session)
        item = pending_repo.get(pid)
        if item:
            session.query(CompanyModel).filter(CompanyModel.id == pid).update({'session_id': session_id})
            session.commit()
    finally:
        session.close()
    broadcaster.step_update(StatusUpdate(
        table='company', pid=pid, step='session_id', val=0,
        extra={'session_id': session_id},
    ))


def _log(pid, step, msg):
    session = get_session_sync()
    try:
        pending_repo = PendingCompanyRepository(session)
        item = pending_repo.get(pid)
        logs = json.loads(item.get('workflow_log') or '[]') if item else []
        logs.append({'step': step, 'msg': msg, 'ts': datetime.now().strftime('%H:%M:%S')})
        from shared.infrastructure.process.models import WorkflowLogEntry
        pending_repo.append_log(pid, WorkflowLogEntry(step=step, msg=msg))
    finally:
        session.close()
    broadcaster.log(LogEntry(
        table='company', pid=pid, step=step, msg=msg,
    ))


def _fail(pid, msg, step=None):
    STEP_LABELS = {
        'fetch': 'Fetching content',
        'extract': 'Extracting company info',
        'analyze': 'Analyzing company',
        'save': 'Saving to database',
        'pipeline': 'Processing',
    }
    label = STEP_LABELS.get(step, step) if step else 'Processing'
    error_msg = f"[{label}] {msg}" if step else msg
    _update_step(pid, 'step_done', 0, status='failed', error=error_msg)
    broadcaster.error(ProcessingError(
        table='company', pid=pid, msg=error_msg, step=step,
    ))


def _is_paused_or_stopped(pid):
    session = get_session_sync()
    try:
        pending_repo = PendingCompanyRepository(session)
        item = pending_repo.get(pid)
        if not item:
            return True
        return item.get('status') not in ('processing',)
    finally:
        session.close()


def _fetch_url(url):
    page = fetch_page(url, max_length=8000)
    if page.is_ok:
        return page.plain_text
    else:
        raise RuntimeError(page.error.message if page.error else f"Failed to fetch URL: {url}")


def _extract_company_info(input_text, input_type, pid):
    if input_type == 'multi_note':
        content = input_text[:8000]
    elif input_type == 'manual':
        content = input_text[:6000]
    else:
        content = f"URL: {input_text}"
    prompt = load_prompt('company/company_extract',
        content=content, input_type=input_type)

    try:
        llm = get_llm_service()
        resp = llm.generate_structured(prompt, timeout=180)
        return json.loads(resp.content)
    except Exception as e:
        _log(pid, 'extract', f'Warning: LLM extraction failed: {e}')
    return None


def _load_rules(context='company', company_type='UNKNOWN'):
    session = get_session_sync()
    try:
        rule_repo = SQLAlchemyRuleRepository(session)
        if context == 'company':
            scope_map = {
                'PRODUCT_COMPANY': 'COMPANY_PRODUCT',
                'RECRUITING_AGENCY': 'COMPANY_RECRUITING',
                'STAFFING_COMPANY': 'COMPANY_RECRUITING',
                'CONSULTING_COMPANY': 'COMPANY_PRODUCT',
                'UNKNOWN': 'COMPANY_PRODUCT',
            }
            entity_scope = scope_map.get(company_type, 'COMPANY_PRODUCT')
            rows = rule_repo.get_enabled_by_scopes(['SHARED', entity_scope])
        else:
            rows = rule_repo.get_enabled_by_scopes(['SHARED', 'JOB'])
    finally:
        session.close()
    if not rows:
        return "No scoring rules set."
    lines = []
    current_cat = None
    for r in rows:
        cat = r['category']
        if cat != current_cat:
            current_cat = cat
            lines.append(f"\n\u2015\u2015 {cat.upper()} {'\u2500' * (35 - len(cat))}")
        weight = r.get('score_weight') or r['priority']
        lines.append(f"  #{r['priority']:>3}  {r['key']} (weight:{weight}): {r['value']}")
    return '\n'.join(lines)


def _analyze_company(company_data, pid, company_type='UNKNOWN'):
    rules = _load_rules(context='company', company_type=company_type)
    prompt = load_prompt('company/company_analyze',
        company_data=json.dumps(company_data, ensure_ascii=False)[:4000],
        company_type=company_type,
        rules=rules)

    try:
        llm = get_llm_service()
        resp = llm.generate_structured(prompt, timeout=300)
        return json.loads(resp.content)
    except Exception:
        pass
    return None


def _save_company(company_data, intelligence_data, raw_source, notes=None, pending_company_id=None):
    session = get_session_sync()
    try:
        company_repo = SQLAlchemyCompanyRepository(session)
        intel_repo = SQLAlchemyCompanyIntelligenceRepository(session)
        now = datetime.now().isoformat()

        fields = {
            'name': company_data.get('name', ''),
            'website': company_data.get('website', ''),
            'domain': company_data.get('domain', ''),
            'industry': company_data.get('industry', ''),
            'country': company_data.get('country', ''),
            'city': company_data.get('city', ''),
            'description': company_data.get('description', ''),
            'company_size': company_data.get('company_size', ''),
            'company_type': company_data.get('company_type', ''),
            'logo_url': company_data.get('logo_url', ''),
            'founded_year': company_data.get('founded_year', ''),
            'headquarters_full': company_data.get('headquarters_full', ''),
            'countries_of_operation': json.dumps(company_data.get('countries_of_operation', []), ensure_ascii=False),
            'funding_stage': company_data.get('funding_stage', ''),
            'funding_amount': company_data.get('funding_amount', ''),
            'products': json.dumps(company_data.get('products', []), ensure_ascii=False),
            'tech_stack': json.dumps(company_data.get('tech_stack', {}), ensure_ascii=False),
            'work_environment': json.dumps(company_data.get('work_environment', {}), ensure_ascii=False),
            'extra': json.dumps({
                'key_clients': company_data.get('key_clients', []),
                'competitors': company_data.get('competitors', []),
                'investors': company_data.get('investors', []),
                'contact_info': company_data.get('contact_info', {}),
                'engineering_culture': company_data.get('engineering_culture', {}),
                'culture_signals': company_data.get('culture_signals', {}),
                'international_signals': company_data.get('international_signals', {}),
                'benefits': company_data.get('benefits', {}),
                'any_other_notable_info': company_data.get('extra', {}).get('any_other_notable_info', ''),
            }, ensure_ascii=False),
        }

        company_id = pending_company_id or company_data.get('id')
        if company_id:
            model = session.query(CompanyModel).filter(CompanyModel.id == company_id).first()
            if model:
                for k, v in fields.items():
                    if hasattr(model, k):
                        setattr(model, k, v)
                model.processing_status = 'completed'
                model.updated_at = now
                session.commit()
            else:
                company_id = None

        if not company_id:
            fields['processing_status'] = 'completed'
            fields['updated_at'] = now
            result = company_repo.insert(fields)
            company_id = result['id']

        scores = intelligence_data.get('scores', {})
        intel_data = {
            'overview': json.dumps(intelligence_data.get('overview', {}), ensure_ascii=False),
            'culture_analysis': json.dumps(intelligence_data.get('culture_analysis', {}), ensure_ascii=False),
            'international_analysis': json.dumps(intelligence_data.get('international_analysis', {}), ensure_ascii=False),
            'career_analysis': json.dumps(intelligence_data.get('career_analysis', {}), ensure_ascii=False),
            'benefits_analysis': json.dumps(intelligence_data.get('benefits_analysis', {}), ensure_ascii=False),
            'visa_analysis': json.dumps(intelligence_data.get('visa_analysis', {}), ensure_ascii=False),
            'technology_analysis': json.dumps(intelligence_data.get('technology_analysis', {}), ensure_ascii=False),
            'recommendation': json.dumps(intelligence_data.get('recommendation', {}), ensure_ascii=False),
            'scores': json.dumps(scores, ensure_ascii=False),
            'raw_source_data': json.dumps(raw_source[:10000] if raw_source else '', ensure_ascii=False),
            'generated_at': now,
        }
        intel_repo.upsert(company_id, intel_data)

        return company_id
    finally:
        session.close()


def process_company(pid):
    """Legacy procedural company processing — delegates to CompanyWorker (OOP + LangGraph)."""
    from shared.infrastructure.process_utils import ProcessManager, TempFileManager, MimoRunner, broadcaster
    from shared.infrastructure.process.repository import PendingCompanyRepository

    session = get_session_sync()
    try:
        pending_repo = PendingCompanyRepository(session)
        proc_mgr = ProcessManager()
        temp_mgr = TempFileManager()
        provider_runner = MimoRunner(proc_mgr)

        worker = CompanyWorker(
            pending_repo=pending_repo,
            process_mgr=proc_mgr,
            temp_mgr=temp_mgr,
            provider_runner=provider_runner,
            broadcaster=broadcaster,
        )
        worker.process(pid)
    finally:
        session.close()
        try:
            from shared.infrastructure.config.queue import get_queue_manager
            get_queue_manager().signal_job_done(pid)
        except Exception:
            pass


# ── OOP LangGraph Worker ──────────────────────────────────────────────


NODE_TO_STATUS = {
    'load_context': JobStatus.PROCESSING,
    'validate_input': JobStatus.PROCESSING,
    'fetch_content': JobStatus.PROCESSING,
    'extract_company_data': JobStatus.PROCESSING,
    'analyze_company': JobStatus.PROCESSING,
    'score_company': JobStatus.PROCESSING,
    'save_results': JobStatus.PROCESSING,
    'completion_event': JobStatus.PROCESSING,
}

NODE_TO_STEP = {
    'load_context': WorkflowStep.VALIDATE,
    'validate_input': WorkflowStep.VALIDATE,
    'fetch_content': WorkflowStep.FETCH,
    'extract_company_data': WorkflowStep.EXTRACT,
    'analyze_company': WorkflowStep.ANALYZE,
    'score_company': WorkflowStep.SCORE,
    'save_results': WorkflowStep.PERSIST,
    'completion_event': WorkflowStep.COMPLETE,
}

TOTAL_NODES = len(NODE_TO_STATUS)


class CompanyWorker(WorkerBase):
    """Concrete worker for company processing using LangGraph state management.

    Template Method: process() is defined by WorkerBase.
    This class implements _execute_pipeline() using the LangGraph company graph.
    Workflow progress is emitted via WebSocket events through the broadcaster.
    """

    def __init__(self, pending_repo, process_mgr, temp_mgr, provider_runner, broadcaster,
                 llm_service=None):
        super().__init__(pending_repo, process_mgr, temp_mgr, provider_runner, broadcaster)
        self._llm = llm_service
        self._graph = None

    @property
    def table(self) -> str:
        return 'company'

    @property
    def pipeline_steps(self) -> list:
        return []

    def _reset_steps(self, pid: int) -> None:
        self._pending_repo.update_status(pid, 'processing', workflow_log='[]')

    def _get_graph(self):
        if self._graph is None:
            builder = build_company_processing_graph()
            self._graph = builder.compile()
        return self._graph

    def _update_node_status(self, pid: int, node_name: str) -> None:
        status = NODE_TO_STATUS.get(node_name)
        step = NODE_TO_STEP.get(node_name)
        if status:
            self._pending_repo.update_status(
                pid, status,
                current_node=node_name,
            )
        if step:
            self._log(pid, step.value, f'Starting: {step.label}')

    def _execute_pipeline(self, pid: int, item: dict) -> Dict[str, Any]:
        notes_raw = item.get('notes', '[]')
        try:
            notes = json.loads(notes_raw) if isinstance(notes_raw, str) else notes_raw
        except (json.JSONDecodeError, TypeError):
            notes = []

        if not notes:
            input_text = item.get('input_text', '')
            note_type = 'url' if input_text.startswith('http') else 'text'
            notes = [{"type": note_type, "content": input_text}]

        links_raw = item.get('links', '[]')
        try:
            links = json.loads(links_raw) if isinstance(links_raw, str) else links_raw
        except (json.JSONDecodeError, TypeError):
            links = []

        company_id = item.get('company_id')
        source = item.get('source', 'web')

        note_summary = '; '.join([n.get('content', '')[:40] for n in notes[:3]])
        self._log(pid, 'fetch', f'Processing {len(notes)} note(s): {note_summary}...')

        context = {
            "pid": str(pid),
            "content": "",
            "notes": json.dumps(notes),
            "links": json.dumps(links),
            "source": source,
            "company_id": company_id,
        }

        self._pending_repo.update_status(pid, JobStatus.PROCESSING, current_node='load_context')

        initial = create_initial_state(
            input="",
            context=context,
        )

        graph = self._get_graph()

        result = graph.invoke(initial)
        progress = result.get("progress", {})
        completed = progress.get("completed_nodes", [])
        for node_name in completed:
            self._update_node_status(pid, node_name)

        errors = result.get("errors", [])
        failure_details_ = result.get("failure_details", [])
        if errors:
            formatted = " | ".join(errors)
            for err in errors:
                self._log(pid, 'error', err)
            details_json = json.dumps(failure_details_, indent=2) if failure_details_ else "[]"
            self._pending_repo.update_fields(pid, "pending_companies", failure_reason=details_json)
            raise RuntimeError(formatted)

        metadata = result.get("metadata", {})
        persistence = metadata.get("persistence", {})
        if persistence.get("success"):
            company_id = persistence.get("company_id")
            company_name = persistence.get("company_name", "")
            self._log(pid, 'save', f'Saved company #{company_id}: {company_name} to DB')
            return {'company_id': company_id, 'name': company_name}

        self._log(pid, 'error', 'Persistence did not complete successfully')
        raise RuntimeError("Company processing failed to persist results")

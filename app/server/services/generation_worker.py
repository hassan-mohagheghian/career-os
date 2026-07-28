"""Background worker for resume/cover letter generation.

Follows the same pattern as worker.py and company_worker.py:
- Background thread processing
- Step-by-step progress tracking
- WebSocket real-time updates via broadcaster
- Structured logging via structlog
- LLMService for AI calls
"""

import json
import os
from datetime import datetime

from services.process.logging_config import get_logger
from services.process_utils import broadcaster
from services.process.models import StatusUpdate, LogEntry, ProcessingComplete, ProcessingError
from ai_compat import get_llm_service
from dependencies import get_session_sync

log = get_logger('generation_worker')


def _update_step(gen_id, step, val, status=None, error=None):
    """Update a generation step and emit WebSocket progress."""
    session = get_session_sync()
    try:
        from pending.infrastructure.repositories.sa_pending_generation_repository import SQLAlchemyPendingGenerationRepository
        repo = SQLAlchemyPendingGenerationRepository(session)
        fields = {step: val}
        if status:
            fields['status'] = status
        if error:
            fields['error'] = error
        repo.update_fields(gen_id, **fields)
    finally:
        session.close()

    extra = {}
    if status:
        extra['status'] = status
    if error:
        extra['error'] = error
    broadcaster.step_update(StatusUpdate(
        table='pending_generations', pid=gen_id, step=step, val=val,
        extra=extra or None,
    ))


def _log_event(gen_id, step, msg):
    """Log and emit WebSocket log event."""
    log.info(f"[generation] gen={gen_id} {step}: {msg}")
    broadcaster.log(LogEntry(
        table='pending_generations', pid=gen_id, step=step, msg=msg,
    ))


def _load_company_context(job_num):
    """Load company intelligence for enrichment when job is linked to a company."""
    session = get_session_sync()
    try:
        from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository
        from companies.infrastructure.repositories.sa_company_intelligence_repository import SQLAlchemyCompanyIntelligenceRepository
        job_repo = SQLAlchemyJobRepository(session)
        intel_repo = SQLAlchemyCompanyIntelligenceRepository(session)

        company_id = job_repo.get_company_id_by_num(job_num)
        if not company_id:
            return None

        intel = intel_repo.get_by_company_id(company_id)
        if not intel:
            return None

        return {
            'overview': json.loads(intel.get('overview') or '{}'),
            'culture': json.loads(intel.get('culture_analysis') or '{}'),
            'technology': json.loads(intel.get('technology_analysis') or '{}'),
            'visa': json.loads(intel.get('visa_analysis') or '{}'),
            'scores': json.loads(intel.get('scores') or '{}'),
        }
    finally:
        session.close()


def process_generation(gen_id):
    """Process a resume or cover letter generation request.

    Steps:
    1. prepare — Load job and resume data
    2. context — Load company intelligence (if linked)
    3. generate — Call LLMService
    4. save — Save result to resumes table
    5. done — Mark complete
    """
    session = get_session_sync()
    try:
        from pending.infrastructure.repositories.sa_pending_generation_repository import SQLAlchemyPendingGenerationRepository
        pending_repo = SQLAlchemyPendingGenerationRepository(session)
        gen = pending_repo.get_by_id(gen_id)
    finally:
        session.close()

    if not gen:
        return

    job_num = gen['job_num']
    gen_type = gen['type']

    _update_step(gen_id, 'step_prepare', 1, status='processing')
    _log_event(gen_id, 'prepare', f'Loading job #{job_num} data')

    job_file = None
    resume_file = None

    try:
        session = get_session_sync()
        try:
            from jobs.infrastructure.repositories.sa_job_repository import SQLAlchemyJobRepository
            from resume.infrastructure.repositories.sa_resume_repository import SQLAlchemyResumeRepository
            job_repo = SQLAlchemyJobRepository(session)
            resume_repo = SQLAlchemyResumeRepository(session)

            job = job_repo.get_by_num(job_num)
            if not job:
                raise RuntimeError(f"Job #{job_num} not found")

            resume_text = resume_repo.get_latest_original_raw_text()
            if not resume_text:
                raise RuntimeError("No master resume uploaded")

            raw_desc = job.get('raw_description', '')
            if not raw_desc:
                raise RuntimeError("No job description available")
        finally:
            session.close()

        _update_step(gen_id, 'step_prepare', 1)
        _log_event(gen_id, 'prepare', f'Job: {job.get("company")} — {job.get("role")}')

        _update_step(gen_id, 'step_context', 1, status='processing')
        company_context = _load_company_context(job_num)

        if company_context:
            _log_event(gen_id, 'context', 'Company intelligence loaded — will enrich prompt')
        else:
            _log_event(gen_id, 'context', 'No linked company — using standard prompt')
        _update_step(gen_id, 'step_context', 1)

        _update_step(gen_id, 'step_generate', 1, status='processing')
        _log_event(gen_id, 'generate', f'Calling LLM for {gen_type} generation')

        from prompts import load_prompt
        _tmp = os.environ.get('TEMP_DIR', 'tmp')
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        tmp_dir = _tmp if os.path.isabs(_tmp) else os.path.join(project_root, _tmp)
        os.makedirs(tmp_dir, exist_ok=True)
        pid = f'{job_num}_{int(datetime.now().timestamp()*1000)}'

        job_file = os.path.join(tmp_dir, f'gen_job_{pid}.txt')
        resume_file = os.path.join(tmp_dir, f'gen_resume_{pid}.txt')
        with open(job_file, 'w') as f:
            f.write(raw_desc)
        with open(resume_file, 'w') as f:
            f.write(resume_text)

        company_context_str = ''
        if company_context:
            parts = []
            if company_context.get('overview'):
                parts.append(f"Company Overview: {json.dumps(company_context['overview'], ensure_ascii=False)[:500]}")
            if company_context.get('technology'):
                parts.append(f"Tech Stack: {json.dumps(company_context['technology'], ensure_ascii=False)[:500]}")
            if company_context.get('culture'):
                parts.append(f"Culture: {json.dumps(company_context['culture'], ensure_ascii=False)[:300]}")
            if company_context.get('visa'):
                parts.append(f"Visa Info: {json.dumps(company_context['visa'], ensure_ascii=False)[:300]}")
            company_context_str = '\n'.join(parts)

        company_context_safe = company_context_str.replace('{', '{{').replace('}', '}}') if company_context_str else ''

        if gen_type == 'resume':
            prompt = load_prompt('resume/step_resume_generate',
                job_file=job_file, resume_file=resume_file,
                tmp_dir=tmp_dir, pid=pid,
                company_context=company_context_safe)
            result_path = os.path.join(tmp_dir, f'resume_{pid}.json')
        else:
            session = get_session_sync()
            try:
                from career.infrastructure.repositories.sa_preference_repository import SQLAlchemyPreferenceRepository
                pref_repo = SQLAlchemyPreferenceRepository(session)
                rule_rows = pref_repo.get_enabled_by_scopes(['SHARED', 'JOB'])
            finally:
                session.close()

            rules_text = ''
            if rule_rows:
                rules_text = '\n'.join([
                    f"- {r['key']} (weight:{r.get('score_weight') or r['priority']}): {r['value']}"
                    for r in rule_rows
                ])

            prompt = load_prompt('resume/step7_cover_generate',
                url=job.get('url', ''), job_file=job_file, resume_file=resume_file,
                tmp_dir=tmp_dir, pid=pid, rules=rules_text,
                company_context=company_context_safe)
            result_path = os.path.join(tmp_dir, f'cover_{pid}.json')

        llm = get_llm_service()
        resp = llm.generate_structured(
            prompt,
            context={"result_file": result_path, "pid": pid},
            timeout=300,
        )
        data = json.loads(resp.content)
        session_id = resp.metadata.get("session_id")

        for f in [job_file, resume_file]:
            try:
                os.remove(f)
            except OSError:
                pass
        job_file = None
        resume_file = None

        _update_step(gen_id, 'step_generate', 1)
        _log_event(gen_id, 'generate', f'LLM returned {len(resp.content)} chars')

        _update_step(gen_id, 'step_save', 1, status='processing')
        _log_event(gen_id, 'save', 'Saving to resumes table')

        if gen_type == 'resume':
            content = data.get('resume_html', '')
            title = f"{job.get('company', 'Unknown')} (Score {job.get('score', 'P')})"
        else:
            content = data.get('cover_letter', '')
            title = f"{job.get('company', 'Unknown')} Cover Letter"

        if not content:
            raise RuntimeError(f"LLM returned empty {gen_type} content")

        resume_id = f'{gen_type}_{job_num}'
        session = get_session_sync()
        try:
            from resume.infrastructure.repositories.sa_resume_repository import SQLAlchemyResumeRepository
            resume_repo = SQLAlchemyResumeRepository(session)
            resume_repo.upsert({
                'id': resume_id,
                'title': title,
                'company': job.get('company'),
                'role': job.get('role'),
                'content': content,
                'version': 1,
                'raw_text': '',
                'job_num': job_num,
            })
        finally:
            session.close()

        _update_step(gen_id, 'step_save', 1)

        _update_step(gen_id, 'step_done', 1, status='done')
        _log_event(gen_id, 'done', f'{gen_type.title()} generated for #{job_num}')

        session = get_session_sync()
        try:
            from pending.infrastructure.repositories.sa_pending_generation_repository import SQLAlchemyPendingGenerationRepository
            pending_repo = SQLAlchemyPendingGenerationRepository(session)
            pending_repo.update_fields(gen_id,
                result=json.dumps({'id': resume_id, 'content': content, 'title': title}),
                status='done',
                session_id=session_id or pid,
            )
        finally:
            session.close()

        broadcaster.complete(ProcessingComplete(
            table='pending_generations', pid=gen_id,
            result={
                'id': resume_id, 'content': content, 'title': title,
                'type': gen_type, 'job_num': job_num, 'session_id': session_id or pid,
            },
        ))

    except Exception as e:
        log.error(f"[generation] gen={gen_id} failed: {e}")
        _update_step(gen_id, 'step_generate', 0, status='failed', error=str(e))
        broadcaster.error(ProcessingError(
            table='pending_generations', pid=gen_id,
            msg=str(e), step='generate',
        ))
        for f in [job_file, resume_file]:
            try:
                os.remove(f)
            except (OSError, UnboundLocalError):
                pass

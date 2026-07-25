"""Background worker for resume/cover letter generation.

Follows the same pattern as worker.py and company_worker.py:
- Background thread processing
- Step-by-step progress tracking
- Structured logging via structlog
- LLMService for AI calls
"""

import json
import os
import threading
from datetime import datetime

from services.process.logging_config import get_logger
from ai_compat import get_llm_service

log = get_logger('generation_worker')


def _db():
    from database import get_db
    return get_db()


def _update_step(gen_id, step, val, status=None, error=None):
    """Update a generation step and emit progress."""
    conn = _db()
    fields = [f'{step}=?']
    values = [val]
    if status:
        fields.append('status=?')
        values.append(status)
    if error:
        fields.append('error=?')
        values.append(error)
    fields.append('updated_at=?')
    values.append(datetime.now().isoformat())
    values.append(gen_id)
    conn.execute(f'UPDATE pending_generations SET {",".join(fields)} WHERE id=?', values)
    conn.commit()
    conn.close()


def _log(gen_id, step, msg):
    """Append a workflow log entry."""
    log.info(f"[generation] gen={gen_id} {step}: {msg}")


def _load_company_context(job_num):
    """Load company intelligence for enrichment when job is linked to a company."""
    conn = _db()
    job = conn.execute('SELECT company_id FROM jobs WHERE num=?', (job_num,)).fetchone()
    if not job:
        conn.close()
        return None
    company_id = dict(job).get('company_id')
    if not company_id:
        conn.close()
        return None

    intel = conn.execute(
        'SELECT overview, culture_analysis, technology_analysis, visa_analysis, scores '
        'FROM company_intelligence WHERE company_id=?',
        (company_id,)
    ).fetchone()
    conn.close()
    if not intel:
        return None

    intel_dict = dict(intel)
    return {
        'overview': json.loads(intel_dict.get('overview') or '{}'),
        'culture': json.loads(intel_dict.get('culture_analysis') or '{}'),
        'technology': json.loads(intel_dict.get('technology_analysis') or '{}'),
        'visa': json.loads(intel_dict.get('visa_analysis') or '{}'),
        'scores': json.loads(intel_dict.get('scores') or '{}'),
    }


def process_generation(gen_id):
    """Process a resume or cover letter generation request.

    Steps:
    1. prepare — Load job and resume data
    2. context — Load company intelligence (if linked)
    3. generate — Call LLMService
    4. save — Save result to resumes table
    5. done — Mark complete
    """
    conn = _db()
    row = conn.execute('SELECT * FROM pending_generations WHERE id=?', (gen_id,)).fetchone()
    conn.close()
    if not row:
        return

    gen = dict(row)
    job_num = gen['job_num']
    gen_type = gen['type']

    try:
        # Step 1: Prepare
        _update_step(gen_id, 'step_prepare', 1, status='processing')
        _log(gen_id, 'prepare', f'Loading job #{job_num} data')

        conn = _db()
        job = conn.execute('SELECT * FROM jobs WHERE num=? AND deleted=0', (job_num,)).fetchone()
        if not job:
            raise RuntimeError(f"Job #{job_num} not found")
        job_dict = dict(job)

        resume_row = conn.execute(
            "SELECT raw_text FROM resumes WHERE id LIKE 'original_%' ORDER BY version DESC LIMIT 1"
        ).fetchone()
        if not resume_row or not dict(resume_row).get('raw_text'):
            raise RuntimeError("No master resume uploaded")
        resume_text = dict(resume_row)['raw_text']

        raw_desc = job_dict.get('raw_description', '')
        if not raw_desc:
            raise RuntimeError("No job description available")
        conn.close()

        _update_step(gen_id, 'step_prepare', 1)
        _log(gen_id, 'prepare', f'Job: {job_dict.get("company")} — {job_dict.get("role")}')

        # Step 2: Load company context
        _update_step(gen_id, 'step_context', 1, status='processing')
        company_context = _load_company_context(job_num)

        if company_context:
            _log(gen_id, 'context', 'Company intelligence loaded — will enrich prompt')
        else:
            _log(gen_id, 'context', 'No linked company — using standard prompt')
        _update_step(gen_id, 'step_context', 1)

        # Step 3: Generate
        _update_step(gen_id, 'step_generate', 1, status='processing')
        _log(gen_id, 'generate', f'Calling LLM for {gen_type} generation')

        from prompts import load_prompt
        _tmp = os.environ.get('TEMP_DIR', 'tmp')
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        tmp_dir = _tmp if os.path.isabs(_tmp) else os.path.join(project_root, _tmp)
        os.makedirs(tmp_dir, exist_ok=True)
        pid = f'{gen_type}_{job_num}_{int(datetime.now().timestamp()*1000)}'

        # Write temp files
        job_file = os.path.join(tmp_dir, f'gen_job_{pid}.txt')
        resume_file = os.path.join(tmp_dir, f'gen_resume_{pid}.txt')
        with open(job_file, 'w') as f:
            f.write(raw_desc)
        with open(resume_file, 'w') as f:
            f.write(resume_text)

        # Build company context string for prompt
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

        if gen_type == 'resume':
            prompt = load_prompt('resume/step_resume_generate',
                job_file=job_file, resume_file=resume_file,
                tmp_dir=tmp_dir, pid=pid,
                company_context=company_context_str)
            result_path = os.path.join(tmp_dir, f'resume_{pid}.json')
        else:
            # Load rules for cover letter
            rules_text = ''
            conn = _db()
            rule_rows = conn.execute(
                "SELECT key, value, priority, score_weight FROM preferences "
                "WHERE enabled=1 AND scope IN ('SHARED', 'JOB') "
                "ORDER BY priority DESC"
            ).fetchall()
            conn.close()
            if rule_rows:
                rules_text = '\n'.join([
                    f"- {r['key']} (weight:{r.get('score_weight') or r['priority']}): {r['value']}"
                    for r in rule_rows
                ])

            prompt = load_prompt('resume/step7_cover_generate',
                url=job_dict.get('url', ''), job_file=job_file, resume_file=resume_file,
                tmp_dir=tmp_dir, pid=pid, rules=rules_text,
                company_context=company_context_str)
            result_path = os.path.join(tmp_dir, f'cover_{pid}.json')

        llm = get_llm_service()
        resp = llm.generate_structured(
            prompt,
            context={"result_file": result_path, "pid": pid},
            timeout=300,
        )
        data = json.loads(resp.content)

        # Cleanup temp files
        for f in [job_file, resume_file]:
            try:
                os.remove(f)
            except OSError:
                pass

        _update_step(gen_id, 'step_generate', 1)
        _log(gen_id, 'generate', f'LLM returned {len(resp.content)} chars')

        # Step 4: Save
        _update_step(gen_id, 'step_save', 1, status='processing')
        _log(gen_id, 'save', 'Saving to resumes table')

        if gen_type == 'resume':
            content = data.get('resume_html', '')
            title = f"{job_dict.get('company', 'Unknown')} (Score {job_dict.get('score', 'P')})"
        else:
            content = data.get('cover_letter', '')
            title = f"{job_dict.get('company', 'Unknown')} Cover Letter"

        if not content:
            raise RuntimeError(f"LLM returned empty {gen_type} content")

        resume_id = f'{gen_type}_{job_num}'
        conn = _db()
        conn.execute(
            '''INSERT OR REPLACE INTO resumes (id, title, company, role, content, version, raw_text, created_at, job_num)
            VALUES (?,?,?,?,?,?,?,?,?)''',
            (resume_id, title, job_dict.get('company'), job_dict.get('role'),
             content, 1, '', datetime.now().isoformat(), job_num)
        )
        conn.commit()
        conn.close()

        _update_step(gen_id, 'step_save', 1)

        # Step 5: Done
        _update_step(gen_id, 'step_done', 1, status='done')
        _log(gen_id, 'done', f'{gen_type.title()} generated for #{job_num}')

        # Update result in pending_generations
        conn = _db()
        conn.execute(
            'UPDATE pending_generations SET result=?, status=? WHERE id=?',
            (json.dumps({'id': resume_id, 'content': content}), 'done', gen_id)
        )
        conn.commit()
        conn.close()

    except Exception as e:
        log.error(f"[generation] gen={gen_id} failed: {e}")
        _update_step(gen_id, 'step_generate', 0, status='failed', error=str(e))
        # Cleanup temp files on error
        for f in [job_file, resume_file]:
            try:
                os.remove(f)
            except (OSError, UnboundLocalError):
                pass

"""
Generation worker (resume/cover letter) — extends WorkerBase with Template Method.

Handles: prepare -> context -> generate -> save -> done

SOLID: SRP, OCP, LSP, DIP
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

from .worker_base import WorkerBase


class GenerationWorker(WorkerBase):
    """Concrete worker for resume/cover letter generation."""

    def __init__(self, pending_repo, process_mgr, temp_mgr, mimo_runner, broadcaster):
        super().__init__(pending_repo, process_mgr, temp_mgr, mimo_runner, broadcaster)

    @property
    def table(self) -> str:
        return 'pending_generations'

    @property
    def pipeline_steps(self) -> list:
        return ['step_prepare', 'step_context', 'step_generate', 'step_save', 'step_done']

    def _execute_pipeline(self, pid: int, item: dict) -> Dict[str, Any]:
        """Execute the generation pipeline."""
        job_num = item.get('job_num')
        gen_type = item.get('type', 'resume')

        # Step 1: Prepare
        self._start_step(pid, 'step_prepare')
        context = self._step_prepare(pid, item)
        if context is None:
            return None
        self._mark_step(pid, 'step_prepare')

        if self._is_cancelled(pid):
            return None

        # Step 2: Load company context
        self._start_step(pid, 'step_context')
        company_ctx = self._step_context(pid, job_num)
        self._mark_step(pid, 'step_context')

        if self._is_cancelled(pid):
            return None

        # Step 3: Generate via LLM
        self._start_step(pid, 'step_generate')
        result = self._step_generate(pid, gen_type, context, company_ctx)
        if result is None:
            return None
        self._mark_step(pid, 'step_generate')

        if self._is_cancelled(pid):
            return None

        # Step 4: Save
        self._start_step(pid, 'step_save')
        saved = self._step_save(pid, gen_type, job_num, result)
        self._mark_step(pid, 'step_save')

        return saved

    def _step_prepare(self, pid: int, item: dict) -> Optional[dict]:
        """Load job and resume data."""
        self._log(pid, 'prepare', f'Loading job #{item.get("job_num")} data')
        from generation_worker import _db
        conn = _db()
        try:
            job = conn.execute(
                'SELECT * FROM jobs WHERE num=? AND deleted=0',
                (item.get('job_num'),)
            ).fetchone()
            if not job:
                raise RuntimeError(f"Job #{item.get('job_num')} not found")

            resume_row = conn.execute(
                "SELECT raw_text FROM resumes WHERE id LIKE 'original_%' ORDER BY version DESC LIMIT 1"
            ).fetchone()
            if not resume_row or not dict(resume_row).get('raw_text'):
                raise RuntimeError("No master resume uploaded")

            return {
                'job': dict(job),
                'resume_text': dict(resume_row)['raw_text'],
            }
        finally:
            conn.close()

    def _step_context(self, pid: int, job_num: int) -> Optional[dict]:
        """Load company intelligence for enrichment."""
        self._log(pid, 'context', 'Loading company context...')
        from generation_worker import _load_company_context
        return _load_company_context(job_num)

    def _step_generate(self, pid: int, gen_type: str, context: dict,
                       company_ctx: Optional[dict]) -> Optional[dict]:
        """Call LLM to generate resume or cover letter."""
        self._log(pid, 'generate', f'Generating {gen_type}...')
        from generation_worker import _db, _load_company_context
        from prompts import load_prompt
        from ai_compat import get_llm_service

        job_dict = context['job']
        resume_text = context['resume_text']
        raw_desc = job_dict.get('raw_description', '')
        if not raw_desc:
            raise RuntimeError("No job description available")

        _tmp = os.environ.get('TEMP_DIR', 'tmp')
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        tmp_dir = _tmp if os.path.isabs(_tmp) else os.path.join(project_root, _tmp)
        os.makedirs(tmp_dir, exist_ok=True)
        pid_str = f'{job_num}_{int(datetime.now().timestamp()*1000)}'

        job_file = os.path.join(tmp_dir, f'gen_job_{pid_str}.txt')
        resume_file = os.path.join(tmp_dir, f'gen_resume_{pid_str}.txt')
        try:
            with open(job_file, 'w') as f:
                f.write(raw_desc)
            with open(resume_file, 'w') as f:
                f.write(resume_text)

            company_context_str = ''
            if company_ctx:
                parts = []
                if company_ctx.get('overview'):
                    parts.append(f"Company Overview: {json.dumps(company_ctx['overview'], ensure_ascii=False)[:500]}")
                if company_ctx.get('technology'):
                    parts.append(f"Tech Stack: {json.dumps(company_ctx['technology'], ensure_ascii=False)[:500]}")
                company_context_str = '\n'.join(parts)

            company_context_safe = company_context_str.replace('{', '{{').replace('}', '}}') if company_context_str else ''

            if gen_type == 'resume':
                prompt = load_prompt('resume/step_resume_generate',
                    job_file=job_file, resume_file=resume_file,
                    tmp_dir=tmp_dir, pid=pid_str,
                    company_context=company_context_safe)
                result_path = os.path.join(tmp_dir, f'resume_{pid_str}.json')
            else:
                prompt = load_prompt('resume/step7_cover_generate',
                    url=job_dict.get('url', ''), job_file=job_file, resume_file=resume_file,
                    tmp_dir=tmp_dir, pid=pid_str, rules='',
                    company_context=company_context_safe)
                result_path = os.path.join(tmp_dir, f'cover_{pid_str}.json')

            llm = get_llm_service()
            resp = llm.generate_structured(
                prompt,
                context={"result_file": result_path, "pid": pid_str},
                timeout=300,
            )
            data = json.loads(resp.content)
            session_id = resp.metadata.get("session_id")

            if gen_type == 'resume':
                content = data.get('resume_html', '')
                title = f"{job_dict.get('company', 'Unknown')} (Score {job_dict.get('score', 'P')})"
            else:
                content = data.get('cover_letter', '')
                title = f"{job_dict.get('company', 'Unknown')} Cover Letter"

            if not content:
                raise RuntimeError(f"LLM returned empty {gen_type} content")

            return {
                'content': content,
                'title': title,
                'session_id': session_id or pid_str,
            }
        finally:
            for f in [job_file, resume_file]:
                try:
                    os.remove(f)
                except OSError:
                    pass

    def _step_save(self, pid: int, gen_type: str, job_num: int, result: dict) -> dict:
        """Save generated content to DB."""
        self._log(pid, 'save', 'Saving to database...')
        from generation_worker import _db
        conn = _db()
        try:
            resume_id = f'{gen_type}_{job_num}'
            conn.execute(
                '''INSERT OR REPLACE INTO resumes (id, title, company, role, content, version, raw_text, created_at, job_num)
                VALUES (?,?,?,?,?,?,?,?,?)''',
                (resume_id, result['title'], '', '',
                 result['content'], 1, '', datetime.now().isoformat(), job_num)
            )
            conn.commit()

            conn.execute(
                'UPDATE pending_generations SET result=?, status=?, session_id=? WHERE id=?',
                (json.dumps({'id': resume_id, 'content': result['content'], 'title': result['title']}),
                 'done', result['session_id'], pid)
            )
            conn.commit()
            return {
                'content_id': resume_id,
                'content': result['content'],
                'title': result['title'],
                'session_id': result['session_id'],
                'type': gen_type,
                'job_num': job_num,
            }
        finally:
            conn.close()

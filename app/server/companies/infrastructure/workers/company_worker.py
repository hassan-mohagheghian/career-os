"""
Background worker that processes pending companies.
Fetches company URL or uses manual notes, runs AI extraction and analysis,
then saves structured company intelligence to DB.
"""
import os
import re
import json
import subprocess
import uuid
import threading
import urllib.request
import urllib.error
from datetime import datetime
from shared.infrastructure.prompts.loader import load_prompt
from shared.infrastructure.process.logging_config import get_logger
from shared.infrastructure.process_utils import broadcaster
from shared.infrastructure.process.models import StatusUpdate, LogEntry, ProcessingComplete, ProcessingError

# AI Agent Layer — unified LLM service
from shared.infrastructure.ai.compat import get_llm_service

# Unified Tool Layer — local-first URL fetching
from ai.infrastructure.tools.fetch import fetch_page

# SQLAlchemy session + repositories
from dependencies import get_session_sync
from processing.infrastructure.repositories.sa_pending_repository import SQLAlchemyPendingRepository
from companies.infrastructure.repositories.sa_company_repository import SQLAlchemyCompanyRepository
from companies.infrastructure.repositories.sa_company_intelligence_repository import SQLAlchemyCompanyIntelligenceRepository
from companies.infrastructure.repositories.sa_company_link_repository import SQLAlchemyCompanyLinkRepository
from career.infrastructure.repositories.sa_preference_repository import SQLAlchemyPreferenceRepository
from companies.infrastructure.models.company_model import CompanyModel

log = get_logger('company_worker')

_file_dir = os.path.dirname(os.path.abspath(__file__))
_server_dir = os.path.join(_file_dir, '..')
PROJECT_ROOT = os.path.abspath(os.path.join(_file_dir, '..', '..', '..'))
_tmp = os.environ.get('TEMP_DIR', 'tmp')
TMP_DIR = _tmp if os.path.isabs(_tmp) else os.path.join(PROJECT_ROOT, _tmp)
os.makedirs(TMP_DIR, exist_ok=True)


def _update_step(pid, step, val, status=None, company_name=None, company_id=None, error=None):
    session = get_session_sync()
    try:
        pending_repo = SQLAlchemyPendingRepository(session)
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
        pending_repo.update_step(pid, step, val, table="pending_companies", **extra)
    finally:
        session.close()
    broadcaster.step_update(StatusUpdate(
        table='pending_companies', pid=pid, step=step, val=val,
        extra=extra or None,
    ))


def _mark(pid, step):
    _update_step(pid, step, 1)


def _save_session_id(pid, session_id):
    """Save mimo session_id to pending_companies."""
    session = get_session_sync()
    try:
        pending_repo = SQLAlchemyPendingRepository(session)
        pending_repo.save_session_id(pid, session_id, table="pending_companies")
    finally:
        session.close()
    broadcaster.step_update(StatusUpdate(
        table='pending_companies', pid=pid, step='session_id', val=0,
        extra={'session_id': session_id},
    ))


def _log(pid, step, msg):
    session = get_session_sync()
    try:
        pending_repo = SQLAlchemyPendingRepository(session)
        item = pending_repo.get_by_id(pid, table="pending_companies")
        logs = json.loads(item.get('workflow_log') or '[]') if item else []
        logs.append({'step': step, 'msg': msg, 'ts': datetime.now().strftime('%H:%M:%S')})
        pending_repo.update_workflow_log(pid, json.dumps(logs), table="pending_companies")
    finally:
        session.close()
    broadcaster.log(LogEntry(
        table='pending_companies', pid=pid, step=step, msg=msg,
    ))


def _fail(pid, msg, step=None):
    # Map step keys to human-readable labels
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
        table='pending_companies', pid=pid, msg=error_msg, step=step,
    ))


def _is_paused_or_stopped(pid):
    session = get_session_sync()
    try:
        pending_repo = SQLAlchemyPendingRepository(session)
        item = pending_repo.get_by_id(pid, table="pending_companies")
        if not item:
            return True
        return item.get('status') not in ('processing',)
    finally:
        session.close()


def _fetch_url(url):
    """Fetch a URL using the unified Tool Layer.

    Local-first approach: fetch → preprocess → return cleaned text.
    Raises RuntimeError for backward compatibility with existing callers.
    """
    page = fetch_page(url, max_length=8000)
    if page.is_ok:
        return page.plain_text
    else:
        raise RuntimeError(page.error.message if page.error else f"Failed to fetch URL: {url}")


def _stream_mimo_output(cmd, cwd, env, timeout, pid):
    """Run mimo with streaming output, logging events to DB in real-time."""
    proc = subprocess.Popen(
        cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, env=env,
    )
    all_lines = []
    session_id = None
    timed_out = threading.Event()

    def watchdog():
        timed_out.wait(timeout)
        if not timed_out.is_set():
            try:
                proc.kill()
            except OSError:
                pass

    timer = threading.Thread(target=watchdog, daemon=True)
    timer.start()

    try:
        for raw_line in proc.stdout:
            line = raw_line.rstrip('\n')
            if not line:
                continue
            all_lines.append(line)
            try:
                evt = json.loads(line)
                # Extract session_id from mimo output — broadcast immediately
                if not session_id:
                    sid = (evt.get('sessionID') or evt.get('session_id')
                           or evt.get('sessionId'))
                    if not sid and 'session' in evt and isinstance(evt['session'], dict):
                        sid = evt['session'].get('id') or evt['session'].get('ID')
                    if sid:
                        session_id = sid
                        _save_session_id(pid, sid)
                event_type = evt.get('type', '')
                if event_type == 'text':
                    text = evt.get('part', {}).get('text', '')
                    if text:
                        _log(pid, 'mimo', f'text: {text[:200]}')
                elif event_type == 'tool_use':
                    part = evt.get('part', {})
                    tool = part.get('tool', 'unknown')
                    _log(pid, 'mimo', f'tool: {tool}')
                elif event_type == 'step_finish':
                    part = evt.get('part', {})
                    tokens = part.get('tokens', {})
                    _log(pid, 'mimo', f'step: {part.get("reason", "")} ({tokens.get("total", 0)} tokens)')
            except json.JSONDecodeError:
                _log(pid, 'mimo', f'[raw] {line[:200]}')

        timed_out.set()
        proc.wait()

        # Generate fallback session_id if mimo didn't provide one
        if not session_id:
            session_id = f"mimo_{uuid.uuid4().hex[:12]}"
            _save_session_id(pid, session_id)

        if proc.returncode == -9:
            raise RuntimeError(f"mimo timed out after {timeout}s")
        return proc.returncode, all_lines, session_id
    except:
        timed_out.set()
        try:
            proc.kill()
        except OSError:
            pass
        proc.wait()
        raise


def _extract_company_info(input_text, input_type, pid):
    """Step 1: Extract structured company data using LLM service."""
    output_file = os.path.join(TMP_DIR, f'company_extract_{pid}.json')
    if input_type == 'multi_note':
        content = input_text[:8000]
    elif input_type == 'manual':
        content = input_text[:6000]
    else:
        content = f"URL: {input_text}"
    prompt = load_prompt('company/company_extract',
        content=content, input_type=input_type, output_file=output_file)

    try:
        llm = get_llm_service()
        resp = llm.generate_structured(
            prompt,
            context={"result_file": output_file, "pid": str(pid)},
            timeout=180,
        )
        return json.loads(resp.content)
    except Exception as e:
        _log(pid, 'extract', f'Warning: LLM extraction failed: {e}')
    return None


def _load_rules(context='company', company_type='UNKNOWN'):
    """Load enabled scoring rules from DB, filtered by context and company type."""
    session = get_session_sync()
    try:
        pref_repo = SQLAlchemyPreferenceRepository(session)
        if context == 'company':
            scope_map = {
                'PRODUCT_COMPANY': 'COMPANY_PRODUCT',
                'RECRUITING_AGENCY': 'COMPANY_RECRUITING',
                'STAFFING_COMPANY': 'COMPANY_RECRUITING',
                'CONSULTING_COMPANY': 'COMPANY_PRODUCT',
                'UNKNOWN': 'COMPANY_PRODUCT',
            }
            entity_scope = scope_map.get(company_type, 'COMPANY_PRODUCT')
            rows = pref_repo.get_enabled_by_scopes(['SHARED', entity_scope])
        else:
            rows = pref_repo.get_enabled_by_scopes(['SHARED', 'JOB'])
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
            lines.append(f"\n── {cat.upper()} {'─' * (35 - len(cat))}")
        weight = r.get('score_weight') or r['priority']
        lines.append(f"  #{r['priority']:>3}  {r['key']} (weight:{weight}): {r['value']}")
    return '\n'.join(lines)


def _analyze_company(company_data, pid, company_type='UNKNOWN'):
    """Step 2: Generate full intelligence analysis using LLM service."""
    output_file = os.path.join(TMP_DIR, f'company_analyze_{pid}.json')
    rules = _load_rules(context='company', company_type=company_type)
    prompt = load_prompt('company/company_analyze',
        company_data=json.dumps(company_data, ensure_ascii=False)[:4000],
        company_type=company_type,
        rules=rules,
        output_file=output_file)

    try:
        llm = get_llm_service()
        resp = llm.generate_structured(
            prompt,
            context={"result_file": output_file, "pid": str(pid)},
            timeout=300,
        )
        return json.loads(resp.content)
    except Exception:
        pass
    return None


def _save_company(company_data, intelligence_data, raw_source, notes=None, pending_company_id=None):
    """Step 3: Save company + intelligence to DB."""
    session = get_session_sync()
    try:
        company_repo = SQLAlchemyCompanyRepository(session)
        intel_repo = SQLAlchemyCompanyIntelligenceRepository(session)
        now = datetime.now().isoformat()

        # Prepare all fields
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

        # Determine company_id: prefer pending item's company_id, then LLM-provided id
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

        # Save intelligence
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
    """
    Full pipeline for company processing:
    1. Fetch     — fetch URL content from notes and links, combine all text
    2. Extract   — extract structured company data via mimo
    3. Analyze   — generate intelligence analysis via mimo
    4. Save      — write to DB (companies, company_intelligence)
    Done         — finalize
    """
    session = get_session_sync()
    try:
        pending_repo = SQLAlchemyPendingRepository(session)
        item = pending_repo.get_by_id(pid, table="pending_companies")
    finally:
        session.close()
    if not item:
        return

    # Parse notes (new multi-note system)
    notes_raw = item.get('notes', '[]')
    try:
        notes = json.loads(notes_raw) if isinstance(notes_raw, str) else notes_raw
    except (json.JSONDecodeError, TypeError):
        notes = []

    # Fallback to legacy input_text if no notes
    if not notes:
        input_text = item.get('input_text', '')
        note_type = 'url' if input_text.startswith('http') else 'text'
        notes = [{"type": note_type, "content": input_text}]

    # Get company_id from pending item or from company_name lookup
    company_id = item.get('company_id')

    # Reset link statuses for this company if company_id exists
    if company_id:
        try:
            link_session = get_session_sync()
            try:
                link_repo = SQLAlchemyCompanyLinkRepository(link_session)
                link_repo.reset_statuses(company_id)
            finally:
                link_session.close()
        except:
            pass

    try:
        note_summary = '; '.join([n.get('content', '')[:40] for n in notes[:3]])
        _log(pid, 'start', f'Processing {len(notes)} note(s): {note_summary}...')

        # ── Step 1: Fetch all URLs and combine all text ──
        _update_step(pid, 'step_fetch', 0, status='processing')
        _log(pid, 'fetch', f'Processing {len(notes)} note(s)...')

        valid_content_parts = []
        failed_urls = []
        url_count = 0

        # Process notes (text content and inline URLs)
        for note in notes:
            ntype = note.get('type', 'text')
            content = note.get('content', '').strip()
            if not content:
                continue
            if ntype == 'url' or content.startswith('http'):
                try:
                    _log(pid, 'fetch', f'Fetching URL: {content[:60]}...')
                    fetched = _fetch_url(content)
                    valid_content_parts.append(f"[SOURCE: {content}]\n{fetched}")
                    url_count += 1
                except Exception as e:
                    _log(pid, 'fetch', f'Warning: Failed to fetch {content[:40]}: {e}')
                    failed_urls.append(content)
            else:
                valid_content_parts.append(f"[NOTE]\n{content}")

        # Process company links (from company_links table if company_id exists)
        if company_id:
            try:
                link_session = get_session_sync()
                try:
                    link_repo = SQLAlchemyCompanyLinkRepository(link_session)
                    links = link_repo.get_by_company_id(company_id)
                    if links:
                        _log(pid, 'fetch', f'Processing {len(links)} company link(s)...')
                        for link_dict in links:
                            link_url = link_dict.get('url', '').strip()
                            if not link_url:
                                continue
                            link_title = link_dict.get('title', '') or ''
                            link_desc = link_dict.get('description', '') or ''
                            try:
                                _log(pid, 'fetch', f'Fetching link: {link_url[:60]}...')
                                fetched = _fetch_url(link_url)
                                header = f"[LINK: {link_url}]"
                                if link_title:
                                    header += f" Title: {link_title}"
                                if link_desc:
                                    header += f" - {link_desc}"
                                valid_content_parts.append(f"{header}\n{fetched}")
                                url_count += 1
                                try:
                                    update_session = get_session_sync()
                                    try:
                                        update_repo = SQLAlchemyCompanyLinkRepository(update_session)
                                        update_repo.update_status(link_dict['id'], 'processed', fetched[:5000])
                                    finally:
                                        update_session.close()
                                except:
                                    pass
                            except Exception as e:
                                _log(pid, 'fetch', f'Warning: Failed to fetch link {link_url[:40]}: {e}')
                                failed_urls.append(link_url)
                                try:
                                    fail_session = get_session_sync()
                                    try:
                                        fail_repo = SQLAlchemyCompanyLinkRepository(fail_session)
                                        fail_repo.update_status(link_dict['id'], 'failed')
                                    finally:
                                        fail_session.close()
                                except:
                                    pass
                finally:
                    link_session.close()
            except Exception as e:
                _log(pid, 'fetch', f'Warning: Failed to process links: {e}')

        # Also process links from pending_companies.links (for new companies without company_id yet)
        try:
            pending_links_raw = item.get('links') or '[]'
            pending_links = json.loads(pending_links_raw) if isinstance(pending_links_raw, str) else pending_links_raw
            if pending_links:
                _log(pid, 'fetch', f'Processing {len(pending_links)} pending link(s)...')
                for link in pending_links:
                    link_url = link.get('url', '').strip()
                    if not link_url:
                        continue
                    link_title = link.get('title', '') or ''
                    link_desc = link.get('description', '') or ''
                    try:
                        _log(pid, 'fetch', f'Fetching pending link: {link_url[:60]}...')
                        fetched = _fetch_url(link_url)
                        header = f"[LINK: {link_url}]"
                        if link_title:
                            header += f" Title: {link_title}"
                        if link_desc:
                            header += f" - {link_desc}"
                        valid_content_parts.append(f"{header}\n{fetched}")
                        url_count += 1
                    except Exception as e:
                        _log(pid, 'fetch', f'Warning: Failed to fetch pending link {link_url[:40]}: {e}')
                        failed_urls.append(link_url)
        except Exception as e:
            _log(pid, 'fetch', f'Warning: Failed to process pending links: {e}')

        if failed_urls:
            _log(pid, 'fetch', f'Skipped {len(failed_urls)} failed URL(s) — continuing with available content')

        raw_content = '\n\n---\n\n'.join(valid_content_parts)

        if not raw_content.strip():
            raise RuntimeError("No content to process — all notes were empty and all URLs failed to load. Add at least one note with company information and try again.")

        if _is_paused_or_stopped(pid):
            return
        _mark(pid, 'step_fetch')
        _log(pid, 'fetch', f'Collected {len(raw_content)} chars from {url_count} URL(s) + {len(valid_content_parts) - url_count} text note(s)')

        # ── Step 2: Extract ──
        _update_step(pid, 'step_extract', 0, status='processing')
        _log(pid, 'extract', 'Extracting company information from all sources...')

        company_data = _extract_company_info(raw_content, 'multi_note', pid)
        if not company_data:
            raise RuntimeError("Could not extract company information from the provided content. The content may be too short, in an unsupported format, or the AI service may be temporarily unavailable.")

        if _is_paused_or_stopped(pid):
            return
        _mark(pid, 'step_extract')
        _log(pid, 'extract', f'Extracted: {company_data.get("name", "Unknown")} — {company_data.get("industry", "Unknown industry")}')

        # Update pending item with detected company name
        _update_step(pid, 'step_extract', 1, company_name=company_data.get('name', ''))

        # Detect company type for type-specific scoring
        company_type = company_data.get('company_type', 'UNKNOWN')
        _log(pid, 'extract', f'Company type detected: {company_type}')

        # ── Step 3: Analyze ──
        _update_step(pid, 'step_analyze', 0, status='processing')
        _log(pid, 'analyze', f'Generating intelligence analysis (rules: {company_type})...')

        intelligence_data = _analyze_company(company_data, pid, company_type=company_type)
        if not intelligence_data:
            raise RuntimeError("AI analysis failed — the analysis service may be temporarily unavailable or the company data was too complex to process. You can retry this step.")

        if _is_paused_or_stopped(pid):
            return
        _mark(pid, 'step_analyze')
        scores = intelligence_data.get('scores', {})
        _log(pid, 'analyze', f'Fit: {scores.get("company_fit_score", "?")} | Success: {scores.get("company_success_score", "?")} | Overall: {scores.get("company_overall_score", "?")} | Grade: {scores.get("overall_grade", "?")}')

        # ── Step 4: Save ──
        _update_step(pid, 'step_save', 0, status='processing')
        _log(pid, 'save', 'Saving to database...')

        company_id = _save_company(company_data, intelligence_data, raw_content, notes=notes, pending_company_id=item.get('company_id'))

        # Move links from pending_companies to company_links
        try:
            pending_links_raw = item.get('links') or '[]'
            pending_links = json.loads(pending_links_raw) if isinstance(pending_links_raw, str) else pending_links_raw
            if pending_links and company_id:
                save_session = get_session_sync()
                try:
                    save_link_repo = SQLAlchemyCompanyLinkRepository(save_session)
                    for link in pending_links:
                        url = link.get('url', '').strip()
                        if not url:
                            continue
                        title = link.get('title', '') or ''
                        desc = link.get('description', '') or ''
                        save_link_repo.create(company_id, url, title, desc)
                    _log(pid, 'save', f'Saved {len(pending_links)} link(s) to company_links')
                finally:
                    save_session.close()
        except Exception as e:
            _log(pid, 'save', f'Warning: Failed to save pending links: {e}')

        if _is_paused_or_stopped(pid):
            return
        _mark(pid, 'step_save')
        _update_step(pid, 'step_save', 1, company_id=company_id)
        _log(pid, 'save', f'Saved company #{company_id}: {company_data.get("name", "Unknown")}')

        # ── Done ──
        _mark(pid, 'step_done')
        _update_step(pid, 'step_done', 1, status='done')
        _log(pid, 'done', f'Company intelligence complete: {company_data.get("name", "Unknown")}')
        broadcaster.complete(ProcessingComplete(
            table='pending_companies', pid=pid, result={'company_id': company_id, 'name': company_data.get('name')},
        ))

        log.info("company_worker.done", name=company_data.get('name', 'Unknown'), company_id=company_id)

    except Exception as e:
        log.error("company_worker.failed", pid=pid, error=str(e))
        # Detect which step was active when the error occurred
        step_labels = {
            'step_fetch': 'fetch',
            'step_extract': 'extract',
            'step_analyze': 'analyze',
            'step_save': 'save',
        }
        failed_step = 'pipeline'
        err_session = get_session_sync()
        try:
            err_pending_repo = SQLAlchemyPendingRepository(err_session)
            err_item = err_pending_repo.get_by_id(pid, table="pending_companies")
            if err_item:
                for step_key, step_name in step_labels.items():
                    if err_item.get(step_key) == 0 and all(err_item.get(k) == 1 for k in list(step_labels.keys())[:list(step_labels.keys()).index(step_key)]):
                        failed_step = step_name
                        break
        finally:
            err_session.close()
        _fail(pid, str(e), step=failed_step)

"""Resume and LinkedIn profile routes."""

import json
import os
import subprocess
import threading
from datetime import datetime

from flask import Blueprint, jsonify, request

from config import DB_PATH, PROJECT_ROOT
from database import get_db, row_to_dict, rows_to_list
from utils import stream_json, mask_pii, text_to_html

# AI Agent Layer — unified LLM service
from ai_compat import get_llm_service

bp = Blueprint('resumes', __name__)


@bp.route('/api/resumes')
def get_resumes():
    conn = get_db()
    rows = conn.execute('SELECT * FROM resumes ORDER BY created_at DESC').fetchall()
    conn.close()
    return stream_json(rows_to_list(rows))


@bp.route('/api/resumes/latest')
def get_latest_resume():
    conn = get_db()
    row = conn.execute("SELECT * FROM resumes WHERE id LIKE 'original_%' ORDER BY version DESC LIMIT 1").fetchone()
    conn.close()
    if row:
        return jsonify(row_to_dict(row))
    return jsonify({})


@bp.route('/api/resumes', methods=['POST'])
def save_resume():
    data = request.get_json()
    raw_text = data.get('raw_text', '').strip()
    if not raw_text:
        return jsonify({'error': 'Resume text required'}), 400

    conn = get_db()
    row = conn.execute("SELECT MAX(version) as max_v FROM resumes WHERE id LIKE 'original_%'").fetchone()
    next_version = (dict(row)['max_v'] or 0) + 1

    masked_text = mask_pii(raw_text)
    content_html = text_to_html(masked_text)

    resume_id = f'original_{next_version}'
    conn.execute('''INSERT OR REPLACE INTO resumes (id, title, company, role, content, version, raw_text, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (resume_id, f'Resume v{next_version}', '', '', content_html, next_version, raw_text, datetime.now().isoformat()))
    conn.commit()
    conn.close()

    return jsonify({
        'status': 'saved', 'id': resume_id, 'version': next_version,
        'content': content_html, 'raw_text': raw_text, 'masked_text': masked_text
    })


@bp.route('/api/resumes/<version>', methods=['DELETE'])
def delete_resume_version(version):
    conn = get_db()
    resume_id = f'original_{version}'
    deleted = conn.execute("DELETE FROM resumes WHERE id=?", (resume_id,)).rowcount
    if not deleted:
        deleted = conn.execute("DELETE FROM resumes WHERE id=?", (version,)).rowcount
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted', 'id': resume_id if deleted else version})


# --- LinkedIn Profile endpoints ---

@bp.route('/api/linkedin')
def get_linkedin_profiles():
    conn = get_db()
    rows = conn.execute("SELECT * FROM resumes WHERE id LIKE 'linkedin_%' ORDER BY created_at DESC").fetchall()
    conn.close()
    return stream_json(rows_to_list(rows))


@bp.route('/api/linkedin/latest')
def get_latest_linkedin():
    conn = get_db()
    row = conn.execute("SELECT * FROM resumes WHERE id LIKE 'linkedin_%' ORDER BY version DESC LIMIT 1").fetchone()
    conn.close()
    if row:
        return jsonify(row_to_dict(row))
    return jsonify({})


@bp.route('/api/linkedin', methods=['POST'])
def save_linkedin():
    data = request.get_json()
    raw_text = data.get('raw_text', '').strip()
    if not raw_text:
        return jsonify({'error': 'LinkedIn profile text required'}), 400

    conn = get_db()
    row = conn.execute("SELECT MAX(version) as max_v FROM resumes WHERE id LIKE 'linkedin_%'").fetchone()
    next_version = (dict(row)['max_v'] or 0) + 1

    masked_text = mask_pii(raw_text)
    content_html = text_to_html(masked_text)

    profile_id = f'linkedin_{next_version}'
    conn.execute('''INSERT OR REPLACE INTO resumes (id, title, company, role, content, version, raw_text, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (profile_id, f'LinkedIn Profile v{next_version}', '', '', content_html, next_version, raw_text, datetime.now().isoformat()))
    conn.commit()
    conn.close()

    return jsonify({
        'status': 'saved', 'id': profile_id, 'version': next_version,
        'content': content_html, 'raw_text': raw_text, 'masked_text': masked_text
    })


@bp.route('/api/linkedin/<version>', methods=['DELETE'])
def delete_linkedin(version):
    conn = get_db()
    profile_id = f'linkedin_{version}'
    deleted = conn.execute("DELETE FROM resumes WHERE id=?", (profile_id,)).rowcount
    if not deleted:
        deleted = conn.execute("DELETE FROM resumes WHERE id=?", (version,)).rowcount
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted', 'id': profile_id if deleted else version})


@bp.route('/api/jobs/<int:num>/generate-resume', methods=['POST'])
def generate_resume(num):
    """Start async resume generation. Returns gen_id for progress tracking."""
    conn = get_db()
    job = conn.execute('SELECT * FROM jobs WHERE num=? AND deleted=0', (num,)).fetchone()
    if not job:
        conn.close()
        return jsonify({'error': 'Job not found'}), 404

    resume_row = conn.execute(
        "SELECT raw_text FROM resumes WHERE id LIKE 'original_%' ORDER BY version DESC LIMIT 1"
    ).fetchone()
    if not resume_row or not dict(resume_row).get('raw_text'):
        conn.close()
        return jsonify({'error': 'No master resume uploaded'}), 400
    conn.close()

    conn = get_db()
    cur = conn.execute(
        "INSERT INTO pending_generations (job_num, type, status) VALUES (?, 'resume', 'queued')",
        (num,)
    )
    gen_id = cur.lastrowid
    conn.commit()
    conn.close()

    from services.generation_worker import process_generation
    threading.Thread(target=process_generation, args=(gen_id,), daemon=True).start()

    return jsonify({'gen_id': gen_id, 'status': 'queued'})


@bp.route('/api/jobs/<int:num>/generate-cover', methods=['POST'])
def generate_cover(num):
    """Start async cover letter generation. Returns gen_id for progress tracking."""
    conn = get_db()
    job = conn.execute('SELECT * FROM jobs WHERE num=? AND deleted=0', (num,)).fetchone()
    if not job:
        conn.close()
        return jsonify({'error': 'Job not found'}), 404

    resume_row = conn.execute(
        "SELECT raw_text FROM resumes WHERE id LIKE 'original_%' ORDER BY version DESC LIMIT 1"
    ).fetchone()
    if not resume_row or not dict(resume_row).get('raw_text'):
        conn.close()
        return jsonify({'error': 'No master resume uploaded'}), 400
    conn.close()

    conn = get_db()
    cur = conn.execute(
        "INSERT INTO pending_generations (job_num, type, status) VALUES (?, 'cover', 'queued')",
        (num,)
    )
    gen_id = cur.lastrowid
    conn.commit()
    conn.close()

    from services.generation_worker import process_generation
    threading.Thread(target=process_generation, args=(gen_id,), daemon=True).start()

    return jsonify({'gen_id': gen_id, 'status': 'queued'})


@bp.route('/api/generations/<int:gen_id>')
def get_generation_progress(gen_id):
    """Get progress for a specific generation."""
    conn = get_db()
    row = conn.execute('SELECT * FROM pending_generations WHERE id=?', (gen_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'Generation not found'}), 404
    gen = dict(row)
    if gen.get('result'):
        try:
            gen['result'] = json.loads(gen['result'])
        except (json.JSONDecodeError, TypeError):
            pass
    return jsonify(gen)


@bp.route('/api/generations/<int:gen_id>/cancel', methods=['POST'])
def cancel_generation(gen_id):
    """Cancel a running generation."""
    conn = get_db()
    conn.execute(
        "UPDATE pending_generations SET status='cancelled', error='Cancelled by user', updated_at=? WHERE id=? AND status IN ('queued', 'processing')",
        (datetime.now().isoformat(), gen_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'status': 'cancelled'})

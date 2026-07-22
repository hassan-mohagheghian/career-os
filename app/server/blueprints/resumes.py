"""Resume and LinkedIn profile routes."""

import json
import os
import subprocess
from datetime import datetime

from flask import Blueprint, jsonify, request

from config import DB_PATH, PROJECT_ROOT
from database import get_db, row_to_dict, rows_to_list
from utils import stream_json, mask_pii, text_to_html

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
    from prompts import load_prompt

    conn = get_db()
    job = conn.execute('SELECT * FROM jobs WHERE num=? AND deleted=0', (num,)).fetchone()
    if not job:
        conn.close()
        return jsonify({'error': 'Job not found'}), 404
    j = dict(job)

    resume_row = conn.execute("SELECT raw_text FROM resumes WHERE id LIKE 'original_%' ORDER BY version DESC LIMIT 1").fetchone()
    conn.close()
    if not resume_row or not dict(resume_row).get('raw_text'):
        return jsonify({'error': 'No master resume uploaded'}), 400

    _tmp = os.environ.get('TEMP_DIR', 'tmp')
    tmp_dir = _tmp if os.path.isabs(_tmp) else os.path.join(PROJECT_ROOT, _tmp)
    os.makedirs(tmp_dir, exist_ok=True)
    pid = f'resume_{num}_{int(datetime.now().timestamp()*1000)}'
    job_file = os.path.join(tmp_dir, f'gen_job_{pid}.txt')
    resume_file = os.path.join(tmp_dir, f'gen_resume_{pid}.txt')

    raw_desc = j.get('raw_description', '')
    if not raw_desc:
        return jsonify({'error': 'No job description available'}), 400

    with open(job_file, 'w') as f:
        f.write(raw_desc)
    with open(resume_file, 'w') as f:
        f.write(dict(resume_row)['raw_text'])

    try:
        prompt = load_prompt('step_resume_generate',
            job_file=job_file, resume_file=resume_file,
            tmp_dir=tmp_dir, pid=pid)

        mimo_bin = os.path.expanduser('~/.mimocode/bin/mimo')
        proc = subprocess.run(
            [mimo_bin, 'run', prompt, '--format', 'json', '--dangerously-skip-permissions'],
            cwd=PROJECT_ROOT, capture_output=True, text=True,
            env={**os.environ, 'NO_COLOR': '1'}, timeout=180
        )

        result_path = os.path.join(tmp_dir, f'resume_{pid}.json')
        if not os.path.exists(result_path):
            return jsonify({'error': 'Resume generation failed — no output file'}), 500

        with open(result_path) as f:
            data = json.loads(f.read(), strict=False)

        resume_html = data.get('resume_html', '')
        if not resume_html:
            return jsonify({'error': 'Resume generation returned empty content'}), 500

        conn = get_db()
        conn.execute('''INSERT OR REPLACE INTO resumes (id, title, company, role, content, version, raw_text, created_at, job_num)
            VALUES (?,?,?,?,?,?,?,?,?)''',
            (f'pending_{num}', f"{j['company']} (Score {j['score']})", j['company'], j['role'],
             resume_html, 1, '', datetime.now().isoformat(), num))
        conn.commit()
        conn.close()

        try: os.remove(result_path)
        except OSError: pass

        return jsonify({'status': 'generated', 'id': f'pending_{num}', 'content': resume_html})
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Resume generation timed out'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        for f in [job_file, resume_file]:
            try: os.remove(f)
            except OSError: pass


@bp.route('/api/jobs/<int:num>/generate-cover', methods=['POST'])
def generate_cover(num):
    from prompts import load_prompt

    conn = get_db()
    job = conn.execute('SELECT * FROM jobs WHERE num=? AND deleted=0', (num,)).fetchone()
    if not job:
        conn.close()
        return jsonify({'error': 'Job not found'}), 404
    j = dict(job)

    resume_row = conn.execute("SELECT raw_text FROM resumes WHERE id LIKE 'original_%' ORDER BY version DESC LIMIT 1").fetchone()
    conn.close()
    if not resume_row or not dict(resume_row).get('raw_text'):
        return jsonify({'error': 'No master resume uploaded'}), 400

    _tmp = os.environ.get('TEMP_DIR', 'tmp')
    tmp_dir = _tmp if os.path.isabs(_tmp) else os.path.join(PROJECT_ROOT, _tmp)
    os.makedirs(tmp_dir, exist_ok=True)
    pid = f'cover_{num}_{int(datetime.now().timestamp()*1000)}'
    job_file = os.path.join(tmp_dir, f'gen_job_{pid}.txt')
    resume_file = os.path.join(tmp_dir, f'gen_resume_{pid}.txt')

    raw_desc = j.get('raw_description', '')
    if not raw_desc:
        return jsonify({'error': 'No job description available'}), 400

    with open(job_file, 'w') as f:
        f.write(raw_desc)
    with open(resume_file, 'w') as f:
        f.write(dict(resume_row)['raw_text'])

    try:
        rules_text = ''
        conn = get_db()
        rule_rows = conn.execute("SELECT key, value, priority FROM preferences WHERE enabled=1 ORDER BY priority DESC").fetchall()
        conn.close()
        if rule_rows:
            rules_text = '\n'.join([f"- {r['key']}: {r['value']} (priority: {r['priority']})" for r in rule_rows])

        prompt = load_prompt('step7_cover_generate',
            url=j.get('url', ''), job_file=job_file, resume_file=resume_file,
            tmp_dir=tmp_dir, pid=pid, rules=rules_text)

        mimo_bin = os.path.expanduser('~/.mimocode/bin/mimo')
        proc = subprocess.run(
            [mimo_bin, 'run', prompt, '--format', 'json', '--dangerously-skip-permissions'],
            cwd=PROJECT_ROOT, capture_output=True, text=True,
            env={**os.environ, 'NO_COLOR': '1'}, timeout=120
        )

        result_path = os.path.join(tmp_dir, f'cover_{pid}.json')
        if not os.path.exists(result_path):
            return jsonify({'error': 'Cover letter generation failed — no output file'}), 500

        with open(result_path) as f:
            data = json.loads(f.read(), strict=False)

        cover_html = data.get('cover_letter', '')
        if not cover_html:
            return jsonify({'error': 'Cover letter generation returned empty content'}), 500

        conn = get_db()
        conn.execute('''INSERT OR REPLACE INTO resumes (id, title, company, role, content, version, raw_text, created_at, job_num)
            VALUES (?,?,?,?,?,?,?,?,?)''',
            (f'cover_{num}', f"{j['company']} Cover Letter", j['company'], j['role'],
             cover_html, 1, '', datetime.now().isoformat(), num))
        conn.commit()
        conn.close()

        try: os.remove(result_path)
        except OSError: pass

        return jsonify({'status': 'generated', 'id': f'cover_{num}', 'content': cover_html})
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Cover letter generation timed out'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        for f in [job_file, resume_file]:
            try: os.remove(f)
            except OSError: pass

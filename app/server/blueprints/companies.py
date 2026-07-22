"""Company intelligence and CRUD routes."""

import json
from datetime import datetime

from flask import Blueprint, jsonify, request, Response

from database import get_db, rows_to_list
from utils import stream_json

bp = Blueprint('companies', __name__)


@bp.route('/api/companies', methods=['GET'])
def get_companies():
    conn = get_db()
    rows = conn.execute('''SELECT c.*, ci.scores,
        (SELECT COUNT(*) FROM jobs WHERE company_id = c.id AND deleted = 0) as job_count
        FROM companies c
        LEFT JOIN company_intelligence ci ON ci.company_id = c.id
        ORDER BY c.created_at DESC''').fetchall()
    conn.close()
    result = []
    for row in rows:
        d = dict(row)
        if d.get('scores'):
            try:
                d['scores'] = json.loads(d['scores'])
            except (json.JSONDecodeError, TypeError):
                d['scores'] = {}
        else:
            d['scores'] = {}
        for field in ['countries_of_operation', 'products', 'tech_stack', 'work_environment', 'extra']:
            if d.get(field):
                try:
                    d[field] = json.loads(d[field])
                except (json.JSONDecodeError, TypeError):
                    pass
        result.append(d)
    return stream_json(result)


@bp.route('/api/companies', methods=['POST'])
def add_company():
    data = request.get_json()
    source = data.get('source', 'web')

    notes = data.get('notes', [])
    if not notes:
        input_text = data.get('input', '').strip()
        if not input_text:
            return jsonify({'error': 'Input required'}), 400
        note_type = 'url' if input_text.startswith('http') else 'text'
        notes = [{"type": note_type, "content": input_text}]

    if not notes:
        return jsonify({'error': 'At least one note required'}), 400

    first_content = notes[0].get('content', '').strip()
    if not first_content:
        return jsonify({'error': 'Empty note'}), 400

    links = data.get('links', [])

    conn = get_db()
    cur = conn.execute('INSERT INTO pending_companies (input_text, notes, links, input_type, source, status) VALUES (?,?,?,?,?,?)',
                       (first_content, json.dumps(notes, ensure_ascii=False), json.dumps(links, ensure_ascii=False), 'notes', source, 'pending'))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return jsonify({'status': 'pending', 'id': new_id, 'notes': notes, 'links': links})


@bp.route('/api/companies/<int:company_id>', methods=['GET'])
def get_company(company_id):
    conn = get_db()
    company = conn.execute('''SELECT *,
        (SELECT COUNT(*) FROM jobs WHERE company_id = companies.id AND deleted = 0) as job_count
        FROM companies WHERE id=?''', (company_id,)).fetchone()
    if not company:
        conn.close()
        return jsonify({'error': 'Not found'}), 404
    d = dict(company)
    for field in ['countries_of_operation', 'products', 'tech_stack', 'work_environment', 'extra', 'notes']:
        if d.get(field):
            try:
                d[field] = json.loads(d[field])
            except (json.JSONDecodeError, TypeError):
                pass
    intel = conn.execute('SELECT * FROM company_intelligence WHERE company_id=? ORDER BY generated_at DESC LIMIT 1',
                         (company_id,)).fetchone()
    if intel:
        i = dict(intel)
        for field in ['overview', 'culture_analysis', 'international_analysis', 'career_analysis',
                       'benefits_analysis', 'visa_analysis', 'technology_analysis', 'recommendation', 'scores', 'raw_source_data']:
            if i.get(field):
                try:
                    i[field] = json.loads(i[field])
                except (json.JSONDecodeError, TypeError):
                    pass
        d['intelligence'] = i
    else:
        d['intelligence'] = None
    links = conn.execute('SELECT * FROM company_links WHERE company_id=? ORDER BY created_at DESC', (company_id,)).fetchall()
    d['links'] = rows_to_list(links)
    conn.close()
    return jsonify(d)


@bp.route('/api/companies/<int:company_id>', methods=['DELETE'])
def delete_company(company_id):
    conn = get_db()
    conn.execute('DELETE FROM company_intelligence WHERE company_id=?', (company_id,))
    conn.execute('DELETE FROM company_links WHERE company_id=?', (company_id,))
    conn.execute('DELETE FROM companies WHERE id=?', (company_id,))
    conn.execute('UPDATE jobs SET company_id=NULL WHERE company_id=?', (company_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted', 'id': company_id})


@bp.route('/api/jobs/<int:num>/link-company', methods=['POST'])
def link_job_to_company(num):
    data = request.get_json(force=True)
    company_id = data.get('company_id')
    conn = get_db()
    job = conn.execute('SELECT num FROM jobs WHERE num=? AND deleted=0', (num,)).fetchone()
    if not job:
        conn.close()
        return jsonify({'error': 'Job not found'}), 404
    if company_id is not None:
        company = conn.execute('SELECT id, name FROM companies WHERE id=?', (company_id,)).fetchone()
        if not company:
            conn.close()
            return jsonify({'error': 'Company not found'}), 404
    conn.execute('UPDATE jobs SET company_id=? WHERE num=?', (company_id, num))
    conn.commit()
    row = conn.execute('SELECT * FROM jobs WHERE num=?', (num,)).fetchone()
    conn.close()
    return jsonify({'status': 'linked', 'num': num, 'company_id': company_id})


@bp.route('/api/companies/<int:company_id>/jobs', methods=['GET'])
def get_company_jobs(company_id):
    conn = get_db()
    rows = conn.execute('SELECT * FROM jobs WHERE company_id=? AND deleted=0 ORDER BY created_at DESC', (company_id,)).fetchall()
    conn.close()
    return stream_json(rows_to_list(rows))


@bp.route('/api/companies/<int:company_id>/notes', methods=['GET'])
def get_company_notes(company_id):
    conn = get_db()
    row = conn.execute('SELECT notes FROM companies WHERE id=?', (company_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'Not found'}), 404
    notes_raw = dict(row).get('notes', '[]')
    try:
        notes = json.loads(notes_raw) if isinstance(notes_raw, str) else (notes_raw or [])
    except (json.JSONDecodeError, TypeError):
        notes = []
    return jsonify(notes)


@bp.route('/api/companies/<int:company_id>/notes', methods=['POST'])
def add_company_note(company_id):
    data = request.get_json(force=True)
    note_type = data.get('type', 'text')
    content = data.get('content', '').strip()
    if not content:
        return jsonify({'error': 'Content required'}), 400
    if note_type == 'auto':
        note_type = 'url' if content.startswith('http') else 'text'
    conn = get_db()
    row = conn.execute('SELECT notes FROM companies WHERE id=?', (company_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Not found'}), 404
    notes_raw = dict(row).get('notes', '[]')
    try:
        notes = json.loads(notes_raw) if isinstance(notes_raw, str) else (notes_raw or [])
    except (json.JSONDecodeError, TypeError):
        notes = []
    notes.append({"type": note_type, "content": content, "id": int(datetime.now().timestamp() * 1000)})
    conn.execute('UPDATE companies SET notes=?, updated_at=? WHERE id=?',
                 (json.dumps(notes, ensure_ascii=False), datetime.now().isoformat(), company_id))
    conn.commit()
    conn.close()
    return jsonify(notes)


@bp.route('/api/companies/<int:company_id>/notes/<int:note_id>', methods=['PUT'])
def update_company_note(company_id, note_id):
    data = request.get_json(force=True)
    new_content = data.get('content', '').strip()
    if not new_content:
        return jsonify({'error': 'Content required'}), 400
    conn = get_db()
    row = conn.execute('SELECT notes FROM companies WHERE id=?', (company_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Not found'}), 404
    notes_raw = dict(row).get('notes', '[]')
    try:
        notes = json.loads(notes_raw) if isinstance(notes_raw, str) else (notes_raw or [])
    except (json.JSONDecodeError, TypeError):
        notes = []
    for n in notes:
        if n.get('id') == note_id:
            n['content'] = new_content
            break
    conn.execute('UPDATE companies SET notes=?, updated_at=? WHERE id=?',
                 (json.dumps(notes, ensure_ascii=False), datetime.now().isoformat(), company_id))
    conn.commit()
    conn.close()
    return jsonify(notes)


@bp.route('/api/companies/<int:company_id>/notes/<int:note_id>', methods=['DELETE'])
def delete_company_note(company_id, note_id):
    conn = get_db()
    row = conn.execute('SELECT notes FROM companies WHERE id=?', (company_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Not found'}), 404
    notes_raw = dict(row).get('notes', '[]')
    try:
        notes = json.loads(notes_raw) if isinstance(notes_raw, str) else (notes_raw or [])
    except (json.JSONDecodeError, TypeError):
        notes = []
    notes = [n for n in notes if n.get('id') != note_id]
    conn.execute('UPDATE companies SET notes=?, updated_at=? WHERE id=?',
                 (json.dumps(notes, ensure_ascii=False), datetime.now().isoformat(), company_id))
    conn.commit()
    conn.close()
    return jsonify(notes)


@bp.route('/api/companies/<int:company_id>/reprocess', methods=['POST'])
def reprocess_company(company_id):
    conn = get_db()
    company = conn.execute('SELECT * FROM companies WHERE id=?', (company_id,)).fetchone()
    if not company:
        conn.close()
        return jsonify({'error': 'Not found'}), 404
    c = dict(company)
    conn.execute('DELETE FROM company_intelligence WHERE company_id=?', (company_id,))
    conn.execute('UPDATE companies SET processing_status=? WHERE id=?', ('pending', company_id))
    # Reset link statuses for reprocessing
    conn.execute('UPDATE company_links SET status=?, extracted_content=?, updated_at=? WHERE company_id=?',
                 ('pending', '', datetime.now().isoformat(), company_id))
    notes_raw = c.get('notes', '[]')
    try:
        notes = json.loads(notes_raw) if isinstance(notes_raw, str) else (notes_raw or [])
    except (json.JSONDecodeError, TypeError):
        notes = []
    if not notes:
        if c.get('website'):
            notes.append({"type": "url", "content": c['website']})
        if c.get('name'):
            notes.append({"type": "text", "content": f"Company: {c['name']}"})
        if c.get('industry'):
            notes.append({"type": "text", "content": f"Industry: {c['industry']}"})
        if c.get('description'):
            notes.append({"type": "text", "content": c['description']})
    if not notes:
        notes = [{"type": "text", "content": c.get('name', 'Unknown company')}]
    cur = conn.execute('INSERT INTO pending_companies (input_text, notes, input_type, source, company_id, company_name, status) VALUES (?,?,?,?,?,?,?)',
                       (notes[0]['content'], json.dumps(notes, ensure_ascii=False), 'notes', 'reprocess', company_id, c.get('name', ''), 'pending'))
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return jsonify({'status': 'pending', 'pending_id': pid})


# Company Links CRUD routes

@bp.route('/api/companies/<int:company_id>/links', methods=['GET'])
def get_company_links(company_id):
    conn = get_db()
    rows = conn.execute('SELECT * FROM company_links WHERE company_id=? ORDER BY created_at DESC', (company_id,)).fetchall()
    conn.close()
    return jsonify(rows_to_list(rows))


@bp.route('/api/companies/<int:company_id>/links', methods=['POST'])
def add_company_link(company_id):
    data = request.get_json(force=True)
    url = data.get('url', '').strip()
    if not url:
        return jsonify({'error': 'URL required'}), 400
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    conn = get_db()
    company = conn.execute('SELECT id FROM companies WHERE id=?', (company_id,)).fetchone()
    if not company:
        conn.close()
        return jsonify({'error': 'Company not found'}), 404
    now = datetime.now().isoformat()
    cur = conn.execute('INSERT INTO company_links (company_id, url, title, description, status, created_at, updated_at) VALUES (?,?,?,?,?,?,?)',
                       (company_id, url, title, description, 'pending', now, now))
    conn.commit()
    link_id = cur.lastrowid
    conn.close()
    return jsonify({'status': 'created', 'id': link_id, 'url': url, 'title': title, 'description': description, 'status': 'pending'})


@bp.route('/api/companies/<int:company_id>/links/<int:link_id>', methods=['PUT'])
def update_company_link(company_id, link_id):
    data = request.get_json(force=True)
    conn = get_db()
    row = conn.execute('SELECT * FROM company_links WHERE id=? AND company_id=?', (link_id, company_id)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Not found'}), 404
    url = data.get('url', '').strip() or dict(row)['url']
    if url and not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    title = data.get('title', '').strip() if 'title' in data else dict(row)['title']
    description = data.get('description', '').strip() if 'description' in data else dict(row)['description']
    now = datetime.now().isoformat()
    conn.execute('UPDATE company_links SET url=?, title=?, description=?, updated_at=? WHERE id=?',
                 (url, title, description, now, link_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'updated', 'id': link_id, 'url': url, 'title': title, 'description': description})


@bp.route('/api/companies/<int:company_id>/links/<int:link_id>', methods=['DELETE'])
def delete_company_link(company_id, link_id):
    conn = get_db()
    row = conn.execute('SELECT * FROM company_links WHERE id=? AND company_id=?', (link_id, company_id)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Not found'}), 404
    conn.execute('DELETE FROM company_links WHERE id=?', (link_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted', 'id': link_id})


@bp.route('/api/pending-companies', methods=['GET'])
def get_pending_companies():
    conn = get_db()
    rows = conn.execute('SELECT * FROM pending_companies ORDER BY created_at DESC').fetchall()
    conn.close()
    result = []
    for row in rows:
        d = dict(row)
        if d.get('notes'):
            try:
                d['notes'] = json.loads(d['notes'])
            except (json.JSONDecodeError, TypeError):
                d['notes'] = []
        else:
            d['notes'] = []
        if d.get('links'):
            try:
                d['links'] = json.loads(d['links'])
            except (json.JSONDecodeError, TypeError):
                d['links'] = []
        else:
            d['links'] = []
        result.append(d)
    return stream_json(result)


@bp.route('/api/pending-companies', methods=['POST'])
def add_pending_company():
    data = request.get_json()
    company_id = data.get('company_id')
    note_content = data.get('note', '').strip()
    note_type = data.get('note_type', 'text')

    if not note_content:
        return jsonify({'error': 'Note content required'}), 400

    conn = get_db()

    if company_id:
        row = conn.execute('SELECT id, notes, status FROM pending_companies WHERE id=? AND company_id=? AND status NOT IN (?,?)',
                           (company_id, company_id, 'done', 'failed')).fetchone()
        if not row:
            row = conn.execute('SELECT id, notes, status FROM pending_companies WHERE company_id=? AND status NOT IN (?,?)',
                               (company_id, 'done', 'failed')).fetchone()
        if row:
            r = dict(row)
            notes = json.loads(r['notes'] or '[]')
            notes.append({"type": note_type, "content": note_content})
            conn.execute('UPDATE pending_companies SET notes=?, input_text=?, updated_at=? WHERE id=?',
                         (json.dumps(notes, ensure_ascii=False), note_content, datetime.now().isoformat(), r['id']))
            conn.commit()
            conn.close()
            return jsonify({'status': 'updated', 'id': r['id'], 'notes': notes})
        else:
            conn.close()
            return jsonify({'error': 'Pending company not found'}), 404
    else:
        note_type = 'url' if note_content.startswith('http') else 'text'
        notes = [{"type": note_type, "content": note_content}]
        cur = conn.execute('INSERT INTO pending_companies (input_text, notes, input_type, source, status) VALUES (?,?,?,?,?)',
                           (note_content, json.dumps(notes, ensure_ascii=False), 'notes', 'web', 'pending'))
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return jsonify({'status': 'pending', 'id': new_id, 'notes': notes})


@bp.route('/api/pending-companies/<int:id>/links', methods=['POST'])
def add_pending_company_links(id):
    data = request.get_json()
    links = data.get('links', [])
    if not links:
        return jsonify({'error': 'No links provided'}), 400
    conn = get_db()
    row = conn.execute('SELECT links FROM pending_companies WHERE id=?', (id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Not found'}), 404
    existing = json.loads(dict(row).get('links') or '[]')
    existing.extend(links)
    conn.execute('UPDATE pending_companies SET links=?, updated_at=? WHERE id=?',
                 (json.dumps(existing, ensure_ascii=False), datetime.now().isoformat(), id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'updated', 'links': existing})


@bp.route('/api/pending-companies/<int:id>/notes', methods=['PUT'])
def update_pending_company_notes(id):
    data = request.get_json()
    notes = data.get('notes', [])
    conn = get_db()
    row = conn.execute('SELECT id FROM pending_companies WHERE id=?', (id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Not found'}), 404
    conn.execute('UPDATE pending_companies SET notes=?, updated_at=? WHERE id=?',
                 (json.dumps(notes, ensure_ascii=False), datetime.now().isoformat(), id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'updated', 'notes': notes})


@bp.route('/api/pending-companies/<int:id>/links', methods=['PUT'])
def update_pending_company_links(id):
    data = request.get_json()
    links = data.get('links', [])
    conn = get_db()
    row = conn.execute('SELECT id FROM pending_companies WHERE id=?', (id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Not found'}), 404
    conn.execute('UPDATE pending_companies SET links=?, updated_at=? WHERE id=?',
                 (json.dumps(links, ensure_ascii=False), datetime.now().isoformat(), id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'updated', 'links': links})


@bp.route('/api/pending-companies/<int:id>', methods=['DELETE'])
def delete_pending_company(id):
    conn = get_db()
    conn.execute('DELETE FROM pending_companies WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted'})


@bp.route('/api/pending-companies/<int:id>/process', methods=['POST'])
def process_pending_company(id):
    conn = get_db()
    row = conn.execute('SELECT * FROM pending_companies WHERE id=?', (id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Not found'}), 404
    item = dict(row)
    if item['status'] in ('done', 'processing', 'queued'):
        conn.close()
        return jsonify({'error': f'Cannot process: {item["status"]}'}), 400
    if item['status'] == 'failed':
        conn.execute('UPDATE pending_companies SET error=NULL, step_fetch=0, step_extract=0, step_analyze=0, step_save=0, step_done=0, updated_at=? WHERE id=?',
                     (datetime.now().isoformat(), id))
        conn.commit()
    conn.close()
    from core.queue import get_queue_manager
    get_queue_manager().enqueue(id, table='pending_companies')
    return jsonify({'status': 'queued', 'id': id})


@bp.route('/api/pending-companies/<int:id>/reset', methods=['PUT'])
def reset_pending_company(id):
    conn = get_db()
    conn.execute('''UPDATE pending_companies SET status='pending', error=NULL,
        step_fetch=0, step_extract=0, step_analyze=0, step_save=0, step_done=0,
        updated_at=? WHERE id=?''', (datetime.now().isoformat(), id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'pending', 'id': id})


@bp.route('/api/pending-companies/stream')
def stream_pending_companies():
    import time
    def generate():
        last_hash = ''
        while True:
            conn = get_db()
            rows = conn.execute('SELECT * FROM pending_companies ORDER BY created_at DESC').fetchall()
            conn.close()
            result = []
            for row in rows:
                d = dict(row)
                if d.get('notes'):
                    try:
                        d['notes'] = json.loads(d['notes'])
                    except (json.JSONDecodeError, TypeError):
                        d['notes'] = []
                else:
                    d['notes'] = []
                if d.get('links'):
                    try:
                        d['links'] = json.loads(d['links'])
                    except (json.JSONDecodeError, TypeError):
                        d['links'] = []
                else:
                    d['links'] = []
                result.append(d)
            data = json.dumps(result, ensure_ascii=False)
            current_hash = str(hash(data))
            if current_hash != last_hash:
                last_hash = current_hash
                yield f'data: {data}\n\n'
            time.sleep(2)
    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

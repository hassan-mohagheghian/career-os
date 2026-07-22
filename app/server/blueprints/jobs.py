"""Job CRUD, rescore, and reprocess routes."""

import json
from datetime import datetime

from flask import Blueprint, jsonify, request

from database import get_db, row_to_dict, rows_to_list
from utils import stream_json, normalize_url
from core.queue import get_queue_manager

bp = Blueprint('jobs', __name__)


@bp.route('/api/jobs')
def get_jobs():
    conn = get_db()
    offset = request.args.get('offset', type=int)
    limit = request.args.get('limit', type=int)

    sort_by = request.args.get('sort_by', 'created_at')
    sort_dir = request.args.get('sort_dir', 'desc')
    allowed_sorts = {'created_at', 'overall_score', 'fit_score', 'success_score', 'score', 'score_success', 'score_combined', 'num', 'company', 'location', 'posted_at', 'applicants', 'adv_at', 'see_at', 'apply_time', 'response_time'}
    if sort_by not in allowed_sorts:
        sort_by = 'created_at'
    if sort_dir not in ('asc', 'desc'):
        sort_dir = 'desc'

    conditions = ['deleted=0']
    params = []

    filter_cities = request.args.get('filter_cities', '')
    if filter_cities:
        cities = [c.strip() for c in filter_cities.split(',') if c.strip()]
        if cities:
            city_conditions = []
            for city in cities:
                city_conditions.append("locations LIKE ?")
                params.append(f'%"{city}"%')
                city_conditions.append("location = ?")
                params.append(city)
            conditions.append(f'({" OR ".join(city_conditions)})')

    filter_companies = request.args.get('filter_companies', '')
    if filter_companies:
        companies = [c.strip() for c in filter_companies.split(',') if c.strip()]
        if companies:
            placeholders = ','.join(['?' for _ in companies])
            conditions.append(f'company IN ({placeholders})')
            params.extend(companies)

    filter_matches = request.args.get('filter_matches', '')
    if filter_matches:
        matches = [m.strip() for m in filter_matches.split(',') if m.strip()]
        if matches:
            placeholders = ','.join(['?' for _ in matches])
            conditions.append(f'match IN ({placeholders})')
            params.extend(matches)

    filter_work_types = request.args.get('filter_work_types', '')
    if filter_work_types:
        wtypes = [w.strip() for w in filter_work_types.split(',') if w.strip()]
        if wtypes:
            wt_conditions = []
            for wt in wtypes:
                wt_conditions.append("work_types LIKE ?")
                params.append(f'%"{wt}"%')
                wt_conditions.append("work_type = ?")
                params.append(wt)
            conditions.append(f'({" OR ".join(wt_conditions)})')

    filter_employment_types = request.args.get('filter_employment_types', '')
    if filter_employment_types:
        etypes = [e.strip() for e in filter_employment_types.split(',') if e.strip()]
        if etypes:
            placeholders = ','.join(['?' for _ in etypes])
            conditions.append(f'employment_type IN ({placeholders})')
            params.extend(etypes)

    filter_tech = request.args.get('filter_tech', '').strip()
    if filter_tech:
        like_param = f'%{filter_tech}%'
        conditions.append('(stack LIKE ? OR role LIKE ? OR company LIKE ? OR notes LIKE ?)')
        params.extend([like_param, like_param, like_param, like_param])

    filter_response_status = request.args.get('filter_response_status', '').strip()
    if filter_response_status:
        statuses = [s.strip() for s in filter_response_status.split(',') if s.strip()]
        if statuses:
            placeholders = ','.join(['?' for _ in statuses])
            conditions.append(f'response_status IN ({placeholders})')
            params.extend(statuses)

    filter_applied = request.args.get('filter_applied', '').strip()
    if filter_applied == 'true':
        conditions.append('apply_time IS NOT NULL')

    where_clause = ' AND '.join(conditions)
    total = conn.execute(f'SELECT COUNT(*) FROM jobs WHERE {where_clause}', params).fetchone()[0]

    stats = conn.execute('''SELECT
        COUNT(*) as total,
        SUM(CASE WHEN match='High' THEN 1 ELSE 0 END) as high_match,
        SUM(CASE WHEN score IN ('A','A+','A++') THEN 1 ELSE 0 END) as apply_now,
        SUM(CASE WHEN work_type='Remote' THEN 1 ELSE 0 END) as remote
        FROM jobs WHERE deleted=0''').fetchone()
    agg = {
        'total': stats[0] or 0,
        'high_match': stats[1] or 0,
        'apply_now': stats[2] or 0,
        'remote': stats[3] or 0,
    }

    if sort_by == 'applicants':
        order_clause = f"CAST(REPLACE(REPLACE(applicants, 'Not specified', '999'), '+', '') AS INTEGER) {sort_dir}"
    elif sort_by == 'overall_score':
        order_clause = f"COALESCE(overall_score, 0) {sort_dir}"
    elif sort_by == 'fit_score':
        order_clause = f"COALESCE(fit_score, 0) {sort_dir}"
    elif sort_by == 'success_score':
        order_clause = f"COALESCE(success_score, 0) {sort_dir}"
    elif sort_by == 'score':
        order_clause = f"COALESCE(fit_score, 0) {sort_dir}, COALESCE(success_score, 0) {sort_dir}"
    elif sort_by == 'score_success':
        order_clause = f"COALESCE(success_score, 0) {sort_dir}, COALESCE(fit_score, 0) {sort_dir}"
    elif sort_by == 'score_combined':
        order_clause = f"COALESCE(overall_score, 0) {sort_dir}"
    else:
        order_clause = f'{sort_by} {sort_dir}'

    if offset is not None and limit is not None:
        rows = conn.execute(f'SELECT * FROM jobs WHERE {where_clause} ORDER BY {order_clause} LIMIT ? OFFSET ?', params + [limit, offset]).fetchall()
        conn.close()
        return jsonify({'jobs': rows_to_list(rows), 'total': total, 'agg': agg})
    rows = conn.execute(f'SELECT * FROM jobs WHERE {where_clause} ORDER BY {order_clause}', params).fetchall()
    conn.close()
    return jsonify({'jobs': rows_to_list(rows), 'total': total, 'agg': agg})


@bp.route('/api/jobs/<int:num>')
def get_job(num):
    conn = get_db()
    row = conn.execute('SELECT * FROM jobs WHERE num=?', (num,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Not found'}), 404
    d = dict(row)
    if d.get('company_id'):
        company = conn.execute('SELECT id, name, industry, city, country, logo_url FROM companies WHERE id=?', (d['company_id'],)).fetchone()
        if company:
            d['linked_company'] = dict(company)
    conn.close()
    return jsonify(d)


@bp.route('/api/jobs/<int:num>', methods=['PUT'])
def update_job(num):
    conn = get_db()
    job = conn.execute('SELECT * FROM jobs WHERE num=?', (num,)).fetchone()
    if not job:
        conn.close()
        return jsonify({'error': 'Not found'}), 404
    data = request.get_json(force=True)
    allowed_fields = {'apply_time', 'response_time', 'response_status'}
    updates = {k: v for k, v in data.items() if k in allowed_fields}
    if not updates:
        conn.close()
        return jsonify({'error': 'No valid fields to update'}), 400
    set_clause = ', '.join(f'{k}=?' for k in updates)
    values = list(updates.values()) + [num]
    conn.execute(f'UPDATE jobs SET {set_clause} WHERE num=?', values)
    conn.commit()
    row = conn.execute('SELECT * FROM jobs WHERE num=?', (num,)).fetchone()
    conn.close()
    return jsonify(row_to_dict(row))


@bp.route('/api/jobs/<int:num>', methods=['DELETE'])
def delete_job(num):
    conn = get_db()
    conn.execute('DELETE FROM jobs WHERE num=?', (num,))
    conn.execute('DELETE FROM summaries WHERE num=?', (num,))
    conn.execute("DELETE FROM resumes WHERE id=? OR id=?", (f'pending_{num}', f'rescore_{num}'))
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted', 'num': num})


@bp.route('/api/jobs/<int:num>/requeue', methods=['POST'])
def requeue_job(num):
    conn = get_db()
    job = conn.execute('SELECT * FROM jobs WHERE num=?', (num,)).fetchone()
    if not job:
        conn.close()
        return jsonify({'error': 'Job not found'}), 404
    j = dict(job)
    url = j['url']
    company = j.get('company', '')
    conn.execute('UPDATE jobs SET deleted=1 WHERE num=?', (num,))
    row = conn.execute('SELECT id FROM pending_jobs WHERE url=?', (url,)).fetchone()
    if row:
        pid = dict(row)['id']
        conn.execute('''UPDATE pending_jobs SET status='pending', error=NULL, source='requeue',
            company=?, queue_order=0, step_fetch=0, step_validate=0, step_extract_raw=0, step_extract_struct=0,
            step_analyze=0, step_summary=0, step_db=0, step_done=0,
            workflow_log='[]', updated_at=? WHERE id=?''',
            (company, datetime.now().isoformat(), pid))
    else:
        cur = conn.execute('INSERT INTO pending_jobs (url, source, company, status) VALUES (?, ?, ?, ?)',
            (url, 'requeue', company, 'pending'))
        pid = cur.lastrowid
    conn.commit()
    conn.close()
    get_queue_manager().enqueue(pid)
    return jsonify({'status': 'queued', 'pid': pid, 'num': num, 'company': company})


@bp.route('/api/summaries')
def get_summaries():
    conn = get_db()
    grade_order = "CASE score WHEN 'A++' THEN 7 WHEN 'A+' THEN 6 WHEN 'A' THEN 5 WHEN 'B' THEN 4 WHEN 'C' THEN 3 WHEN 'D' THEN 2 WHEN 'E' THEN 1 ELSE 0 END"
    rows = conn.execute(f'SELECT * FROM summaries ORDER BY {grade_order} DESC').fetchall()
    conn.close()
    return stream_json(rows_to_list(rows))


@bp.route('/api/jobs/<int:num>/rescore', methods=['POST'])
def rescore_job(num):
    conn = get_db()
    job = conn.execute('SELECT * FROM jobs WHERE num=?', (num,)).fetchone()
    if not job:
        conn.close()
        return jsonify({'error': 'Job not found'}), 404
    j = dict(job)
    url = j['url']
    conn.execute('UPDATE jobs SET rescoring=1 WHERE num=?', (num,))
    conn.execute('DELETE FROM pending_jobs WHERE url=?', (url,))
    cur = conn.execute('INSERT INTO pending_jobs (url, source, company, job_num, status) VALUES (?, ?, ?, ?, ?)',
                        (url, 'rescore', j.get('company', ''), num, 'pending'))
    conn.commit()
    pending_id = cur.lastrowid
    conn.close()
    get_queue_manager().enqueue(pending_id)
    return jsonify({'status': 'queued', 'num': num, 'company': j.get('company', ''), 'pending_id': pending_id})


@bp.route('/api/jobs/rescore-all', methods=['POST'])
def rescore_all():
    conn = get_db()
    jobs = conn.execute('SELECT num, url, company FROM jobs WHERE deleted=0 AND rescoring=0').fetchall()
    count = 0
    pending_ids = []
    for job in jobs:
        j = dict(job)
        num = j['num']
        url = j['url']
        conn.execute('UPDATE jobs SET rescoring=1 WHERE num=?', (num,))
        cur = conn.execute('INSERT INTO pending_jobs (url, source, company, job_num, status) VALUES (?, ?, ?, ?, ?)',
                            (url, 'rescore', j.get('company', ''), num, 'pending'))
        pending_ids.append(cur.lastrowid)
        count += 1
    conn.commit()
    conn.close()
    if pending_ids:
        get_queue_manager().enqueue_bulk(pending_ids)
    return jsonify({'status': 'rescoring', 'count': count})


@bp.route('/api/jobs/reprocess-all', methods=['POST'])
def reprocess_all():
    conn = get_db()
    jobs = conn.execute('SELECT num, url, company FROM jobs WHERE deleted=0').fetchall()
    conn.execute('DELETE FROM jobs WHERE deleted=0')
    conn.execute('DELETE FROM summaries')
    conn.execute("DELETE FROM resumes WHERE id != 'original'")
    pending_ids = []
    for job in jobs:
        j = dict(job)
        url = j['url']
        company = j.get('company', '')
        row = conn.execute('SELECT id FROM pending_jobs WHERE url=?', (url,)).fetchone()
        if row:
            pid = dict(row)['id']
            conn.execute('''UPDATE pending_jobs SET status='pending', error=NULL, source='requeue',
                company=?, queue_order=0, step_fetch=0, step_validate=0, step_extract_raw=0, step_extract_struct=0,
                step_analyze=0, step_summary=0, step_db=0, step_done=0,
                workflow_log='[]', updated_at=? WHERE id=?''',
                (company, datetime.now().isoformat(), pid))
            pending_ids.append(pid)
        else:
            cur = conn.execute('INSERT INTO pending_jobs (url, source, company, status) VALUES (?, ?, ?, ?)',
                (url, 'requeue', company, 'pending'))
            pending_ids.append(cur.lastrowid)
    conn.commit()
    conn.close()
    if pending_ids:
        get_queue_manager().enqueue_bulk(pending_ids)
    return jsonify({'status': 'reprocessing', 'count': len(pending_ids)})

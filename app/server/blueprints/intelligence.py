"""Intelligence and analysis routes."""

import json

from flask import Blueprint, jsonify

from database import get_db, rows_to_list
from utils import stream_json

bp = Blueprint('intelligence', __name__)


@bp.route('/api/intelligence', methods=['GET'])
def get_intelligence():
    conn = get_db()
    row = conn.execute(
        'SELECT id, page, created_at, analysis_json FROM analysis_runs WHERE page=? ORDER BY created_at DESC LIMIT 1',
        ('intelligence',)
    ).fetchone()
    if not row:
        row = conn.execute(
            'SELECT id, page, created_at, analysis_json FROM analysis_runs WHERE page=? ORDER BY created_at DESC LIMIT 1',
            ('analysis',)
        ).fetchone()
    conn.close()
    if row:
        r = dict(row)
        r['analysis'] = json.loads(r['analysis_json'])
        del r['analysis_json']
        return jsonify(r)
    return jsonify({'error': 'No intelligence found'}), 404


@bp.route('/api/intelligence/<section>', methods=['GET'])
def get_intelligence_section(section):
    conn = get_db()
    row = conn.execute(
        'SELECT analysis_json FROM analysis_runs WHERE page=? ORDER BY created_at DESC LIMIT 1',
        ('intelligence',)
    ).fetchone()
    if not row:
        row = conn.execute(
            'SELECT analysis_json FROM analysis_runs WHERE page=? ORDER BY created_at DESC LIMIT 1',
            ('analysis',)
        ).fetchone()
    conn.close()
    if row:
        analysis = json.loads(dict(row)['analysis_json'])
        if section in analysis:
            return jsonify(analysis[section])
        return jsonify({'error': f'Section "{section}" not found'}), 404
    return jsonify({'error': 'No intelligence found'}), 404


@bp.route('/api/intelligence/refresh', methods=['POST'])
def refresh_intelligence():
    from services.worker import _update_unified_analysis
    try:
        _update_unified_analysis(0)
        return jsonify({'status': 'updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/intelligence/<section>/refresh', methods=['POST'])
def refresh_intelligence_section(section):
    from services.worker import _update_unified_analysis
    valid_sections = ['market', 'opportunity', 'strategy', 'skills', 'company', 'networking']
    if section not in valid_sections:
        return jsonify({'error': f'Invalid section: {section}'}), 400
    try:
        _update_unified_analysis(0)
        return jsonify({'status': 'updated', 'section': section})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/analysis')
def get_unified_analysis():
    conn = get_db()
    row = conn.execute(
        'SELECT id, page, created_at, analysis_json FROM analysis_runs WHERE page=? ORDER BY created_at DESC LIMIT 1',
        ('analysis',)
    ).fetchone()
    if not row:
        row = conn.execute(
            'SELECT id, page, created_at, analysis_json FROM analysis_runs WHERE page=? ORDER BY created_at DESC LIMIT 1',
            ('dashboard',)
        ).fetchone()
    conn.close()
    if row:
        r = dict(row)
        r['analysis'] = json.loads(r['analysis_json'])
        del r['analysis_json']
        return jsonify(r)
    return jsonify({'error': 'No analysis found'}), 404


@bp.route('/api/analysis/<page>')
def get_analysis(page):
    conn = get_db()
    row = conn.execute(
        'SELECT id, page, created_at, analysis_json FROM analysis_runs WHERE page=? ORDER BY created_at DESC LIMIT 1',
        (page,)
    ).fetchone()
    conn.close()
    if row:
        r = dict(row)
        r['analysis'] = json.loads(r['analysis_json'])
        del r['analysis_json']
        return jsonify(r)
    return jsonify({'error': 'No analysis found', 'page': page}), 404


@bp.route('/api/analysis/<page>/history')
def get_analysis_history(page):
    conn = get_db()
    rows = conn.execute(
        'SELECT id, page, created_at FROM analysis_runs WHERE page=? ORDER BY created_at DESC',
        (page,)
    ).fetchall()
    conn.close()
    return jsonify(rows_to_list(rows))

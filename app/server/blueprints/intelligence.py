"""Intelligence and analysis routes."""

import json

from flask import Blueprint, jsonify

from database import get_db, rows_to_list
from utils import stream_json

bp = Blueprint('intelligence', __name__)

# Section to worker function mapping
SECTION_WORKERS = {
    'market': '_update_market_analysis',
    'opportunity': '_update_opportunity_analysis',
    'strategy': '_update_strategy_analysis',
    'skills': '_update_skills_analysis',
    'networking': '_update_networking_analysis',
}

SECTION_KEYS = {
    'market': ['market', 'searchSummary', 'cities'],
    'opportunity': ['opportunity', 'apply_urgency', 'visa_companies'],
    'strategy': ['overview', 'strategy', 'strengths', 'weaknesses', 'visa_companies', 'apply_urgency', 'goals', 'improvements', 'searchSummary', 'cities'],
    'skills': ['techStack', 'techLearning', 'skillJobFit', 'learningROI'],
    'networking': ['networking'],
}


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


@bp.route('/api/intelligence/timestamps', methods=['GET'])
def get_intelligence_timestamps():
    """Get last updated timestamps for each section."""
    conn = get_db()
    row = conn.execute(
        'SELECT analysis_json FROM analysis_runs WHERE page=? ORDER BY created_at DESC LIMIT 1',
        ('intelligence',)
    ).fetchone()
    conn.close()
    if row:
        analysis = json.loads(dict(row)['analysis_json'])
        metadata = analysis.get('metadata', {})
        last_updated = metadata.get('lastUpdated', {})
        return jsonify(last_updated)
    return jsonify({})


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
    from services.worker import (
        _update_market_analysis, _update_opportunity_analysis,
        _update_strategy_analysis, _update_skills_analysis,
        _update_networking_analysis
    )
    valid_sections = list(SECTION_WORKERS.keys())
    if section not in valid_sections:
        return jsonify({'error': f'Invalid section: {section}'}), 400
    try:
        # Call the specific worker function for this section
        worker_func = globals()[SECTION_WORKERS[section]]
        worker_func(0)
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

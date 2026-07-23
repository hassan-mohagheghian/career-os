"""Career Intelligence API routes."""

import threading

from flask import Blueprint, jsonify, request

bp = Blueprint('career_intel', __name__)

INSIGHT_TYPES = ['overview', 'opportunities', 'companies', 'skills', 'market', 'networking']


@bp.route('/api/career-intelligence', methods=['GET'])
def get_all():
    """Get all latest career intelligence sections."""
    from services.career_intel import get_latest
    data = get_latest()
    return jsonify(data or {})


@bp.route('/api/career-intelligence/<section>', methods=['GET'])
def get_section(section):
    """Get latest career intelligence for a specific section."""
    if section not in INSIGHT_TYPES:
        return jsonify({'error': f'Invalid section: {section}'}), 400
    from services.career_intel import get_latest
    data = get_latest(section)
    if data:
        return jsonify(data)
    return jsonify({'error': f'No {section} intelligence found'}), 404


@bp.route('/api/career-intelligence/runs', methods=['GET'])
def get_runs():
    """Get recent insight generation runs."""
    from services.career_intel import get_runs
    section = request.args.get('section')
    limit = request.args.get('limit', 10, type=int)
    runs = get_runs(section, limit)
    return jsonify(runs)


@bp.route('/api/career-intelligence/progress', methods=['GET'])
def get_progress():
    """Get current analysis progress (real-time status)."""
    from services.career_intel import get_progress as _get_progress
    return jsonify(_get_progress())


@bp.route('/api/career-intelligence/refresh', methods=['POST'])
def refresh_all():
    """Generate all career intelligence sections in background."""
    from services.career_intel import generate_all, is_running
    running, info = is_running()
    if running:
        return jsonify({
            'status': 'already_running',
            'message': f'Analysis already in progress ({info["type"]})',
            'running': info
        }), 409
    def _run():
        generate_all()
    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return jsonify({'status': 'started', 'message': 'Career intelligence generation started'})


@bp.route('/api/career-intelligence/<section>/refresh', methods=['POST'])
def refresh_section(section):
    """Generate a single career intelligence section in background."""
    if section not in INSIGHT_TYPES:
        return jsonify({'error': f'Invalid section: {section}'}), 400
    from services.career_intel import generate_section, is_running
    running, info = is_running()
    if running:
        return jsonify({
            'status': 'already_running',
            'message': f'Analysis already in progress ({info["type"]})',
            'running': info
        }), 409
    def _run():
        generate_section(section)
    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return jsonify({'status': 'started', 'section': section, 'message': f'{section} intelligence generation started'})


@bp.route('/api/career-intelligence/status', methods=['GET'])
def get_status():
    """Get current generation status for all sections."""
    from services.career_intel import get_runs, is_running
    running, run_info = is_running()
    status = {'_running': running, '_currentRun': run_info}
    for section in INSIGHT_TYPES:
        runs = get_runs(section, limit=1)
        if runs:
            latest = runs[0]
            status[section] = {
                'status': latest['status'],
                'lastRun': latest['started_at'],
                'completedAt': latest.get('completed_at'),
                'error': latest.get('error_message')
            }
        else:
            status[section] = {'status': 'never', 'lastRun': None}
    return jsonify(status)


@bp.route('/api/career-intelligence/cancel', methods=['POST'])
def cancel():
    """Cancel the currently running career intelligence analysis."""
    from services.career_intel import cancel_run, is_running
    running, info = is_running()
    if not running:
        return jsonify({'status': 'idle', 'message': 'No analysis running'}), 200
    cancelled = cancel_run()
    if cancelled:
        return jsonify({'status': 'cancelled', 'message': 'Analysis cancelled'})
    return jsonify({'status': 'error', 'message': 'Could not cancel analysis'}), 500

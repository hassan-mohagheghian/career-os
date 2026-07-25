"""Career Intelligence API routes."""

import threading

from flask import Blueprint, jsonify, request

bp = Blueprint('career_intel', __name__)

INSIGHT_TYPES = ['overview', 'opportunities', 'companies', 'skills', 'market', 'networking', 'skills_intel']


@bp.route('/api/career-intelligence', methods=['GET'])
def get_all():
    """Get all latest career intelligence sections.
    ---
    tags: [Insights]
    responses:
      200:
        description: All intelligence sections (overview, opportunities, companies, market, networking, skills_intel)
    """
    from services.career_intel import get_latest
    data = get_latest()
    return jsonify(data or {})


@bp.route('/api/career-intelligence/<section>', methods=['GET'])
def get_section(section):
    """Get latest career intelligence for a specific section.
    ---
    tags: [Insights]
    parameters:
      - name: section
        in: path
        required: true
        type: string
        enum: [overview, opportunities, companies, market, networking, skills_intel]
    responses:
      200:
        description: Section intelligence data
      404:
        description: No intelligence found for this section
    """
    if section not in INSIGHT_TYPES:
        return jsonify({'error': f'Invalid section: {section}'}), 400
    from services.career_intel import get_latest
    data = get_latest(section)
    if data:
        return jsonify(data)
    return jsonify({'error': f'No {section} intelligence found'}), 404


@bp.route('/api/career-intelligence/runs', methods=['GET'])
def get_runs():
    """Get recent insight generation runs with total count for infinite scroll."""
    from services.career_intel import get_runs
    section = request.args.get('section')
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    result = get_runs(section, limit, offset)
    return jsonify(result)


@bp.route('/api/career-intelligence/progress', methods=['GET'])
def get_progress():
    """Get current analysis progress (real-time status)."""
    from services.career_intel import get_progress as _get_progress
    return jsonify(_get_progress())


@bp.route('/api/career-intelligence/refresh', methods=['POST'])
def refresh_all():
    """Generate all career intelligence sections in background.
    ---
    tags: [Insights]
    responses:
      200:
        description: Generation started
      409:
        description: Analysis already running
    """
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
        result = get_runs(section, limit=1)
        items = result.get('items', []) if isinstance(result, dict) else result
        if items:
            latest = items[0]
            status[section] = {
                'status': latest['status'],
                'lastRun': latest['started_at'],
                'completedAt': latest.get('completed_at'),
                'error': latest.get('error_message')
            }
        else:
            status[section] = {'status': 'never', 'lastRun': None}
    return jsonify(status)


@bp.route('/api/career-intelligence/skills-intel', methods=['GET'])
def get_skills_intel():
    """Get the latest Skills Intelligence Report.
    ---
    tags: [Skills]
    responses:
      200:
        description: Skills intelligence data with strengths, gaps, recommendations
      404:
        description: No skills intelligence found
    """
    from services.career_intel import get_latest
    data = get_latest('skills_intel')
    if data:
        return jsonify(data)
    return jsonify({'error': 'No skills intelligence found. Run refresh first.'}), 404


@bp.route('/api/career-intelligence/skills-intel/refresh', methods=['POST'])
def refresh_skills_intel():
    """Generate the Skills Intelligence Report in background."""
    from services.career_intel import generate_skills_intel, is_running
    running, info = is_running()
    if running:
        return jsonify({
            'status': 'already_running',
            'message': f'Analysis already in progress ({info["type"]})',
            'running': info
        }), 409
    def _run():
        generate_skills_intel()
    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return jsonify({'status': 'started', 'message': 'Skills intelligence generation started'})


@bp.route('/api/career-intelligence/cancel', methods=['POST'])
def cancel():
    """Cancel the currently running career intelligence analysis.
    ---
    tags: [Insights]
    responses:
      200:
        description: Analysis cancelled
    """
    from services.career_intel import cancel_run, is_running
    running, info = is_running()
    if not running:
        return jsonify({'status': 'idle', 'message': 'No analysis running'}), 200
    cancelled = cancel_run()
    if cancelled:
        return jsonify({'status': 'cancelled', 'message': 'Analysis cancelled'})
    return jsonify({'status': 'error', 'message': 'Could not cancel analysis'}), 500

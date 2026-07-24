"""Application entry point.

Wires up Flask app, SocketIO, blueprints, queue, and shutdown handlers.
All route logic lives in blueprints/ — this file stays minimal.
"""

from dotenv import load_dotenv
load_dotenv()

import os
import sys
import signal
import atexit

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO, join_room, leave_room

from config import DB_PATH, STATIC_FOLDER
from migrations import ensure_db_schema, run_migrations
from core.queue import init_queue_manager, get_queue_manager
from services.process.logging_config import setup_logging, get_logger

# ── Logging ────────────────────────────────────────────────────────

_server_dir = os.path.dirname(os.path.abspath(__file__))
_log_dir = os.path.join(_server_dir, 'logs')
setup_logging(log_dir=_log_dir, level='INFO')
log = get_logger('app')

# ── Bootstrap ──────────────────────────────────────────────────────

app = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path='')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
CORS(app)

socketio = SocketIO(app, cors_allowed_origins='*', async_mode='threading')

# ── Database ───────────────────────────────────────────────────────

ensure_db_schema()
run_migrations()
log.info("app.database_ready")

# ── Queue ──────────────────────────────────────────────────────────

init_queue_manager(DB_PATH)
log.info("app.queue_started")

# ── Broadcaster wiring ────────────────────────────────────────────

from services.process.broadcaster import Broadcaster
_broadcaster = Broadcaster()
_broadcaster.set_socketio(socketio)

# Wire shared broadcaster used by worker.py and company_worker.py
from services.process_utils import broadcaster as _shared_broadcaster
_shared_broadcaster.set_socketio(socketio)

# ── Register Blueprints ───────────────────────────────────────────

from blueprints.jobs import bp as jobs_bp
from blueprints.resumes import bp as resumes_bp
from blueprints.pending import bp as pending_bp
from blueprints.companies import bp as companies_bp
from blueprints.career_intel import bp as career_intel_bp
from blueprints.rules import bp as rules_bp
from blueprints.dashboard import bp as dashboard_bp, set_socketio as set_dashboard_socketio
from blueprints.static import bp as static_bp, init_static

app.register_blueprint(jobs_bp)
app.register_blueprint(resumes_bp)
app.register_blueprint(pending_bp)
app.register_blueprint(companies_bp)
app.register_blueprint(career_intel_bp)
app.register_blueprint(rules_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(static_bp)

set_dashboard_socketio(socketio)

# Wire SocketIO to career intelligence service for real-time progress
from services.career_intel import set_socketio as set_career_intel_socketio
set_career_intel_socketio(socketio)

init_static(app)

# ── SocketIO Events ───────────────────────────────────────────────

@socketio.on('connect')
def handle_connect():
    log.info("socketio.connect", sid=getattr(__import__('flask_socketio', fromlist=['request']), 'request', None))

@socketio.on('disconnect')
def handle_disconnect():
    log.info("socketio.disconnect")

@socketio.on('watch_pending')
def handle_watch_pending(data):
    pid = data.get('id')
    if pid:
        join_room(f'pending_{pid}')
        log.info("socketio.watch", room=f'pending_{pid}')

@socketio.on('unwatch_pending')
def handle_unwatch_pending(data):
    pid = data.get('id')
    if pid:
        leave_room(f'pending_{pid}')

@socketio.on('watch_company')
def handle_watch_company(data):
    pid = data.get('id')
    if pid:
        join_room(f'company_{pid}')
        log.info("socketio.watch", room=f'company_{pid}')

@socketio.on('unwatch_company')
def handle_unwatch_company(data):
    pid = data.get('id')
    if pid:
        leave_room(f'company_{pid}')

@socketio.on('cancel_job')
def handle_cancel_job(data):
    pid = data.get('id')
    table = data.get('table', 'pending_jobs')
    if pid:
        ok = get_queue_manager().cancel_job(pid, table)
        log.info("socketio.cancel", pid=pid, success=ok)

@socketio.on('reset_job')
def handle_reset_job(data):
    pid = data.get('id')
    table = data.get('table', 'pending_jobs')
    if pid:
        ok = get_queue_manager().reset_job(pid, table)
        log.info("socketio.reset", pid=pid, success=ok)

@socketio.on('watch_skills')
def handle_watch_skills():
    join_room('skills')
    log.info("socketio.watch", room='skills')

@socketio.on('unwatch_skills')
def handle_unwatch_skills():
    leave_room('skills')


@socketio.on('watch_career_intel')
def handle_watch_career_intel():
    join_room('career_intel')
    log.info("socketio.watch", room='career_intel')


@socketio.on('unwatch_career_intel')
def handle_unwatch_career_intel():
    leave_room('career_intel')

# ── Graceful Shutdown ─────────────────────────────────────────────

def _cleanup(signum=None, frame=None):
    log.info("app.shutdown_start")
    # 1. Stop queue (waits for workers, kills processes, cleans temp files)
    try:
        get_queue_manager().stop(timeout=15)
    except Exception as e:
        log.warning("app.queue_stop_error", error=str(e))
    # 2. Cancel career intel runs
    try:
        from services.career_intel import cancel_run
        cancel_run()
    except Exception:
        pass
    # 3. Mark skill roadmap jobs as cancelled
    try:
        from database import get_db
        conn = get_db()
        conn.execute(
            "UPDATE skill_roadmap_jobs SET status='cancelled', error='Server shutting down' WHERE status IN ('running','queued')"
        )
        conn.commit()
        conn.close()
    except Exception:
        pass
    # 4. Stop SocketIO
    try:
        socketio.stop()
    except Exception:
        pass
    log.info("app.shutdown_complete")
    if signum:
        sys.exit(0)

signal.signal(signal.SIGTERM, _cleanup)
signal.signal(signal.SIGINT, _cleanup)
atexit.register(_cleanup)

# ── Run ────────────────────────────────────────────────────────────

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)

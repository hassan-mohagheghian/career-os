"""Application entry point.

Wires up Flask app, registers blueprints, runs migrations, and starts the server.
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

from config import DB_PATH, STATIC_FOLDER
from migrations import ensure_db_schema, run_migrations
from core.queue import init_queue_manager

# ── Bootstrap ──────────────────────────────────────────────────────

app = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path='')
CORS(app)

# ── Database ───────────────────────────────────────────────────────

ensure_db_schema()
run_migrations()

# ── Queue ──────────────────────────────────────────────────────────

init_queue_manager(DB_PATH)

# ── Register Blueprints ───────────────────────────────────────────

from blueprints.jobs import bp as jobs_bp
from blueprints.resumes import bp as resumes_bp
from blueprints.pending import bp as pending_bp
from blueprints.companies import bp as companies_bp
from blueprints.career_intel import bp as career_intel_bp
from blueprints.rules import bp as rules_bp
from blueprints.dashboard import bp as dashboard_bp
from blueprints.static import bp as static_bp, init_static

app.register_blueprint(jobs_bp)
app.register_blueprint(resumes_bp)
app.register_blueprint(pending_bp)
app.register_blueprint(companies_bp)
app.register_blueprint(career_intel_bp)
app.register_blueprint(rules_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(static_bp)

init_static(app)

# ── Graceful Shutdown ─────────────────────────────────────────────

_running_processes = []

def _cleanup_processes(signum=None, frame=None):
    """Terminate all running background processes gracefully."""
    print("\n[app] Shutting down — terminating background processes...")
    for proc in _running_processes:
        if proc and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=5)
                print(f"[app] Terminated process {proc.pid}")
            except Exception:
                try:
                    proc.kill()
                    print(f"[app] Killed process {proc.pid}")
                except Exception:
                    pass
    # Mark any active career intel runs as cancelled
    try:
        from services.career_intel import cancel_run
        cancel_run()
    except Exception:
        pass
    # Mark any active skill roadmap jobs as cancelled
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
    print("[app] Cleanup complete.")
    if signum:
        sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGTERM, _cleanup_processes)
signal.signal(signal.SIGINT, _cleanup_processes)

# Register atexit handler as backup
atexit.register(_cleanup_processes)

def register_process(proc):
    """Register a subprocess for cleanup on shutdown."""
    _running_processes.append(proc)

def unregister_process(proc):
    """Unregister a completed subprocess."""
    try:
        _running_processes.remove(proc)
    except ValueError:
        pass

# ── Run ────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True, port=5000)

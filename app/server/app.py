"""Application entry point.

Wires up Flask app, registers blueprints, runs migrations, and starts the server.
All route logic lives in blueprints/ — this file stays minimal.
"""

from dotenv import load_dotenv
load_dotenv()

import os
import sys

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
from blueprints.intelligence import bp as intelligence_bp
from blueprints.career_intel import bp as career_intel_bp
from blueprints.rules import bp as rules_bp
from blueprints.dashboard import bp as dashboard_bp
from blueprints.static import bp as static_bp, init_static

app.register_blueprint(jobs_bp)
app.register_blueprint(resumes_bp)
app.register_blueprint(pending_bp)
app.register_blueprint(companies_bp)
app.register_blueprint(intelligence_bp)
app.register_blueprint(career_intel_bp)
app.register_blueprint(rules_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(static_bp)

init_static(app)

# ── Run ────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True, port=5000)

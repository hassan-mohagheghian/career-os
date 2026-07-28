"""Application configuration."""

import os
from dotenv import load_dotenv

load_dotenv()

_SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
# From shared/infrastructure/config/ go up 3 levels to app/server/
_SERVER_DIR = os.path.abspath(os.path.join(_SERVER_DIR, '..', '..', '..'))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SERVER_DIR, '..', '..'))

_db_path = os.environ.get('DB_PATH', os.path.join(_SERVER_DIR, 'db', 'jobs.db'))
DB_PATH = _db_path if os.path.isabs(_db_path) else os.path.normpath(os.path.join(_SERVER_DIR, _db_path))

PROJECT_ROOT = _PROJECT_ROOT
STATIC_FOLDER = os.path.join(_SERVER_DIR, '..', 'client', 'dist')

# AI Provider configuration
AI_PROVIDER = os.environ.get('AI_PROVIDER', 'mimo')

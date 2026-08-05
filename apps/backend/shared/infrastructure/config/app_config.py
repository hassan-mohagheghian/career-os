"""Application configuration."""

import os
from dotenv import load_dotenv

load_dotenv()

_SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
_SERVER_DIR = os.path.abspath(os.path.join(_SERVER_DIR, '..', '..', '..'))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SERVER_DIR, '..', '..'))

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is required. "
        "Set it to a PostgreSQL connection string, e.g.:\n"
        "  DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/jobsearch\n"
        "Or use Docker Compose: docker compose up -d postgres"
    )

# Normalize to use psycopg v3 dialect if plain postgresql:// was given
if DATABASE_URL.startswith('postgresql://') and '+psycopg' not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)

PROJECT_ROOT = _PROJECT_ROOT
STATIC_FOLDER = os.path.join(_SERVER_DIR, '..', 'frontend', 'dist')

AI_PROVIDER = os.environ.get('AI_PROVIDER', 'mimo')

# Dev DB backup scheduler
DB_BACKUP_INTERVAL_MINUTES = int(os.environ.get('DB_BACKUP_INTERVAL_MINUTES', '10'))
DB_BACKUP_KEEP_COUNT = int(os.environ.get('DB_BACKUP_KEEP_COUNT', '3'))
_DB_BACKUP_DIR = os.environ.get('DB_BACKUP_DIR', os.path.join(_PROJECT_ROOT, 'backups'))
DB_BACKUP_DIR = os.path.abspath(_DB_BACKUP_DIR) if os.path.isabs(_DB_BACKUP_DIR) else os.path.join(_PROJECT_ROOT, _DB_BACKUP_DIR)
DB_BACKUP_CONTAINER = os.environ.get('DB_BACKUP_CONTAINER', 'job-search-postgres-1')
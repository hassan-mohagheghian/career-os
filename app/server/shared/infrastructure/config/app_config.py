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
STATIC_FOLDER = os.path.join(_SERVER_DIR, '..', 'client', 'dist')

AI_PROVIDER = os.environ.get('AI_PROVIDER', 'mimo')
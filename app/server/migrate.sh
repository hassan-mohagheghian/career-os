#!/bin/sh
# Database migration helper for the Job Search app.
#
# Usage:
#   ./migrate.sh new "add feature X"    # Create a new migration
#   ./migrate.sh upgrade                 # Apply all pending migrations
#   ./migrate.sh downgrade               # Rollback last migration
#   ./migrate.sh history                 # Show migration history
#   ./migrate.sh current                 # Show current revision
#
# To create a new migration:
#   1. Run: ./migrate.sh new "description of change"
#   2. Edit the generated file in migrations/versions/
#   3. Run: ./migrate.sh upgrade
#
# Migration file naming: NNN_description.py (e.g., 002_add_new_field.py)
# Always implement both upgrade() and downgrade() functions.

set -e
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

case "${1:-help}" in
    new)
        if [ -z "$2" ]; then
            echo "Usage: $0 new \"description\""
            exit 1
        fi
        # Generate revision
        uv run alembic revision --autogenerate -m "$2"
        echo ""
        echo "Generated migration file. Edit it in app/server/migrations/versions/"
        echo "Then run: $0 upgrade"
        ;;
    upgrade)
        uv run alembic upgrade head
        echo "Migrations applied successfully."
        ;;
    downgrade)
        uv run alembic downgrade -1
        echo "Rolled back one migration."
        ;;
    history)
        uv run alembic history --verbose
        ;;
    current)
        uv run alembic current
        ;;
    *)
        echo "Database Migration Helper"
        echo ""
        echo "Usage: $0 <command> [args]"
        echo ""
        echo "Commands:"
        echo "  new \"description\"   Create a new migration (autogenerate)"
        echo "  upgrade             Apply all pending migrations"
        echo "  downgrade           Rollback last migration"
        echo "  history             Show migration history"
        echo "  current             Show current revision"
        ;;
esac

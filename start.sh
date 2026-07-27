#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# Job Search Application — Start Script
# ─────────────────────────────────────────────────────────────────
#
# Usage:
#   ./start.sh              Start FastAPI backend + frontend
#   ./start.sh backend      Start FastAPI backend only
#   ./start.sh frontend     Start only frontend dev server
#   ./start.sh stop         Stop all running processes
#   ./start.sh status       Show running processes
#
# ─────────────────────────────────────────────────────────────────

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVER_DIR="$SCRIPT_DIR/app/server"
CLIENT_DIR="$SCRIPT_DIR/app/client"
PID_FILE="$SCRIPT_DIR/.server.pid"
CLIENT_PID_FILE="$SCRIPT_DIR/.client.pid"
VENV_DIR="$SCRIPT_DIR/.venv"

# Use venv python if available, otherwise system python
if [ -f "$VENV_DIR/bin/python" ]; then
    PYTHON="$VENV_DIR/bin/python"
else
    PYTHON="$(command -v python3 || command -v python)"
fi

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[job-search]${NC} $1"; }
warn() { echo -e "${YELLOW}[job-search]${NC} $1"; }
err() { echo -e "${RED}[job-search]${NC} $1"; }
ok() { echo -e "${GREEN}[job-search]${NC} $1"; }

# ── Cleanup handler ───────────────────────────────────────────────

cleanup() {
    log "Shutting down..."
    # Stop backend
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            log "Stopping backend (PID: $PID)..."
            kill -TERM "$PID" 2>/dev/null || true
            wait "$PID" 2>/dev/null || true
        fi
        rm -f "$PID_FILE"
    fi
    # Stop frontend
    if [ -f "$CLIENT_PID_FILE" ]; then
        PID=$(cat "$CLIENT_PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            log "Stopping frontend (PID: $PID)..."
            kill -TERM "$PID" 2>/dev/null || true
            wait "$PID" 2>/dev/null || true
        fi
        rm -f "$CLIENT_PID_FILE"
    fi
    # Kill any remaining mimo processes
    pkill -f "mimo run" 2>/dev/null || true
    ok "All processes stopped."
}

trap cleanup EXIT INT TERM

# ── Commands ──────────────────────────────────────────────────────

start_backend() {
    log "Starting backend server..."
    log "Using Python: $PYTHON"
    cd "$SERVER_DIR"

    # Run Alembic migrations before starting
    if [ -f "$SCRIPT_DIR/.venv/bin/alembic" ]; then
        log "Running database migrations..."
        cd "$SCRIPT_DIR"
        .venv/bin/alembic upgrade head 2>&1 || warn "Alembic migration warning (non-fatal)"
        cd "$SERVER_DIR"
    fi

    $PYTHON -m uvicorn main:app --host 0.0.0.0 --port 5000 --reload &
    echo $! > "$PID_FILE"
    ok "Backend started (PID: $(cat $PID_FILE)) on http://localhost:5000"
}

start_frontend() {
    log "Starting frontend dev server..."
    cd "$CLIENT_DIR"
    npm run dev &
    echo $! > "$CLIENT_PID_FILE"
    ok "Frontend started (PID: $(cat $CLIENT_PID_FILE)) on http://localhost:5173"
}

stop_all() {
    log "Stopping all processes..."
    cleanup
}

show_status() {
    echo ""
    echo -e "${BLUE}═══ Job Search App Status ═══${NC}"
    echo ""

    # Backend
    if [ -f "$PID_FILE" ] && kill -0 "$(cat $PID_FILE)" 2>/dev/null; then
        ok "Backend:  Running (PID: $(cat $PID_FILE)) — http://localhost:5000"
    else
        warn "Backend:  Not running"
    fi

    # Frontend
    if [ -f "$CLIENT_PID_FILE" ] && kill -0 "$(cat $CLIENT_PID_FILE)" 2>/dev/null; then
        ok "Frontend: Running (PID: $(cat $CLIENT_PID_FILE)) — http://localhost:5173"
    else
        warn "Frontend: Not running"
    fi

    # Mimo processes
    MIMO_COUNT=$(pgrep -f "mimo run" 2>/dev/null | wc -l)
    if [ "$MIMO_COUNT" -gt 0 ]; then
        warn "Mimo AI:  $MIMO_COUNT process(es) running"
        pgrep -af "mimo run" 2>/dev/null | head -5
    else
        ok "Mimo AI:  No processes running"
    fi

    # AI Provider config
    if [ -f "$SCRIPT_DIR/.env" ]; then
        AI_PROVIDER=$(grep -E "^AI_PROVIDER=" "$SCRIPT_DIR/.env" 2>/dev/null | cut -d= -f2 || echo "mimo")
        ok "AI Provider: ${AI_PROVIDER:-mimo}"
    fi

    echo ""
}

# ── Main ──────────────────────────────────────────────────────────

case "${1:-all}" in
    backend)
        start_backend
        ;;
    frontend)
        start_frontend
        ;;
    stop)
        stop_all
        ;;
    status)
        show_status
        ;;
    all)
        start_backend
        sleep 2
        start_frontend
        echo ""
        ok "All services started!"
        echo ""
        echo "  Backend:  http://localhost:5000"
        echo "  Frontend: http://localhost:5173"
        echo ""
        echo "  Press Ctrl+C to stop all services"
        echo ""
        wait
        ;;
    *)
        echo "Usage: $0 {all|backend|frontend|stop|status}"
        exit 1
        ;;
esac

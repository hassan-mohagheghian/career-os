#!/bin/sh
# Start the Job Search App — all services with auto-reload

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== Starting Flask API on port 5000 (auto-reload enabled) ==="
cd "$SCRIPT_DIR/server"
uv run python app.py &
FLASK_PID=$!

echo "=== Starting WebSocket stream server on port 8765 ==="
uv run python stream_server.py &
WS_PID=$!

echo "=== Starting React dev server (HMR enabled) ==="
cd "$SCRIPT_DIR/client"
npm run dev &
REACT_PID=$!

echo ""
echo "Flask API:  http://localhost:5000  (auto-reloads on .py changes)"
echo "WebSocket:  ws://localhost:8765"
echo "React Dev:  http://localhost:5173  (HMR on .jsx/.css changes)"
echo ""
echo "Press Ctrl+C to stop all services"

trap 'kill $FLASK_PID $WS_PID $REACT_PID 2>/dev/null; exit' INT TERM
wait

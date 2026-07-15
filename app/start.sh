#!/bin/bash
# Start the Job Search App — all services

echo "=== Initializing database ==="
cd "$(dirname "$0")/server"
uv run python db.py

cleanup() {
    echo ""
    echo "Stopping all services..."
    kill -- -$$ 2>/dev/null || true
    wait 2>/dev/null || true
    echo "All services stopped."
}
trap cleanup EXIT INT TERM

echo "=== Starting Flask API on port 5000 ==="
uv run python app.py &
FLASK_PID=$!

echo "=== Starting WebSocket stream server on port 8765 ==="
uv run python stream_server.py &
STREAM_PID=$!

echo "=== Starting React dev server ==="
cd ../client
npm run dev &
REACT_PID=$!

echo ""
echo "Flask API:  http://localhost:5000"
echo "WebSocket:  ws://localhost:8765"
echo "React Dev:  http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop all services"

wait

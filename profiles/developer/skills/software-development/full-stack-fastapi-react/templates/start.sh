#!/bin/bash
# Start both backend (FastAPI) and frontend (Vite) dev servers
# Run from project root: ./start.sh

set -e
cd "$(dirname "$0")"

echo "Starting backend (port 8000)..."
source venv/bin/activate
uvicorn backend.main:app --port 8000 --reload &
BACKEND_PID=$!

echo "Starting frontend (port 5173)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "Press Ctrl+C to stop."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait

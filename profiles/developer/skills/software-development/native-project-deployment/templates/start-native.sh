#!/usr/bin/env bash
# =========================================
# {{PROJECT_NAME}} — native startup script
# =========================================
# Template: copy to project root, fill in {{PLACEHOLDERS}}, chmod +x
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
echo ">>> {{PROJECT_NAME}} — starting from $ROOT"

# --- PostgreSQL ---
echo -n ">>> PostgreSQL... "
if pg_isready -h 127.0.0.1 -p {{DB_PORT}} -q 2>/dev/null; then
  echo "OK"
else
  echo "NOT RUNNING! Start with: pg_ctl -D {{PG_DATA_DIR}} start"
  exit 1
fi

# --- Backend ---
echo -n ">>> Backend... "
lsof -ti:{{BACKEND_PORT}} | xargs kill 2>/dev/null || true
cd "$ROOT/{{BACKEND_DIR}}"
{{BACKEND_ENV_VARS}} \
  nohup python3 -m uvicorn main:app --host 0.0.0.0 --port {{BACKEND_PORT}} \
  > /tmp/{{PROJECT_SLUG}}-backend.log 2>&1 &
echo "pid $! (port {{BACKEND_PORT}})"

# --- Mock API (if present) ---
{{#HAS_MOCK}}
echo -n ">>> Mock API... "
lsof -ti:{{MOCK_PORT}} | xargs kill 2>/dev/null || true
cd "$ROOT/{{MOCK_DIR}}"
nohup python3 {{MOCK_SCRIPT}} > /tmp/{{PROJECT_SLUG}}-mock.log 2>&1 &
echo "pid $! (port {{MOCK_PORT}})"
{{/HAS_MOCK}}

# --- Frontend ---
echo -n ">>> Frontend... "
lsof -ti:{{FRONTEND_PORT}} | xargs kill 2>/dev/null || true
cd "$ROOT/{{FRONTEND_DIR}}"
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
{{FRONTEND_ENV_VARS}} \
  nohup npx vite --host 0.0.0.0 --port {{FRONTEND_PORT}} \
  > /tmp/{{PROJECT_SLUG}}-frontend.log 2>&1 &
echo "pid $! (port {{FRONTEND_PORT}})"

# --- Health checks ---
echo ""
echo ">>> Waiting..."
sleep 3
echo -n "  Backend  : " && curl -s -o /dev/null -w "%{http_code}" http://localhost:{{BACKEND_PORT}}/health && echo " OK"
echo -n "  Frontend : " && curl -s -o /dev/null -w "%{http_code}" http://localhost:{{FRONTEND_PORT}} && echo " OK"

echo ""
echo "================ READY ================"
echo "  Frontend : http://localhost:{{FRONTEND_PORT}}"
echo "  Backend  : http://localhost:{{BACKEND_PORT}}/docs"
echo "  DB       : psql -h 127.0.0.1 -U {{DB_USER}} -d {{DB_NAME}}"
echo "========================================"

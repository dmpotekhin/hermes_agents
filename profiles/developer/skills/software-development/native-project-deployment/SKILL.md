---
name: native-project-deployment
description: Deploy multi-service projects natively (without Docker) — PostgreSQL, Python/FastAPI, Node.js/Vite, mock servers. Use when Docker is unavailable or the user explicitly asks for a non-Docker run.
---

# Native Project Deployment

## Trigger
- Docker daemon won't start (macOS vmnetd issues, permission errors)
- `docker compose`/`docker-compose` fails or is absent
- User says "запусти без Docker" or "Docker не работает"
- Project has docker-compose.yml but containers won't come up

## Process

### 1. Diagnose Docker (quick)
```bash
docker info 2>&1 | head -5
docker ps 2>&1
```
If daemon unreachable and restart doesn't help within 30s — pivot to native.

### 2. Inventory what's already installed
```bash
which psql python3 node npm
pg_isready
node --version
python3 --version
```
Don't install anything yet — work with what's there.

### 3. PostgreSQL — set up directly
- **Find the running instance**: `ps aux | grep postgres | grep -v grep`. Multiple versions may coexist (Homebrew + EnterpriseDB installer). The process line shows the binary path and data directory: `/Library/PostgreSQL/16/bin/postgres -D /Library/PostgreSQL/16/data`.
- **Find pg_hba.conf**: from the data dir above, or `find / -name pg_hba.conf 2>/dev/null`. If it's `scram-sha-256`, temporarily switch to `trust`:
  ```bash
  sudo sed -i '' 's/scram-sha-256/trust/g' /path/to/pg_hba.conf
  sudo -u postgres /path/to/pg_ctl reload -D /path/to/data
  ```
- **Create DB and user** from docker-compose.yml env vars:
  ```bash
  psql -h 127.0.0.1 -U postgres -d postgres \
    -c "CREATE USER <user> WITH PASSWORD '<pass>';" \
    -c "CREATE DATABASE <db> OWNER <user>;"
  ```
- **Run schema and seeds**:
  ```bash
  psql -h 127.0.0.1 -U <user> -d <db> -f db/01_schema.sql
  psql -h 127.0.0.1 -U <user> -d <db> -f db/02_seed.sql
  ```
- **Grant schema permissions** if tables are in non-public schemas:
  ```sql
  GRANT USAGE ON SCHEMA ecommerce, banking TO <user>;
  GRANT SELECT ON ALL TABLES IN SCHEMA ecommerce, banking TO <user>;
  ```

### 4. Backend (Python/FastAPI)
```bash
cd backend
pip3 install -r requirements.txt
# Override DB_HOST from "postgres" (Docker service name) to "localhost":
DB_HOST=localhost DB_PORT=5432 DB_NAME=<db> DB_USER=<user> DB_PASSWORD=<pass> \
  python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 &
```

### 5. Frontend (Node.js/Vite/React)
```bash
cd frontend
npm install --prefer-offline     # may take 2-4 min; add --prefer-offline to avoid hangs
VITE_API_URL=http://localhost:8000 VITE_MOCK_URL=http://localhost:8080 \
  npx vite --host 0.0.0.0 --port 3000 &
```
If `node` isn't found in non-interactive shell, source nvm first:
```bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
```

### 6. Mock API — replace WireMock/Java with Python
Don't fight with Java/WireMock. Write a minimal FastAPI server:
```python
from fastapi import FastAPI, Request
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)

@app.post("/api/v1/transfers/internal")
async def handler(request: Request):
    body = await request.json()
    return {"status": "COMPLETED", "data": {...}}
```
Run: `python3 mock_server.py &` on the mock's port (e.g. 8080).

### 7. Verify
```bash
curl -s http://localhost:8000/health   # → {"status":"ok","db":"up"}
curl -s http://localhost:3000/         # → 200 HTML
curl -s -X POST http://localhost:8080/...  # mock responds
```

### 8. Create a startup script
After verifying everything works, create a `start.sh` that captures the full launch sequence — port cleanup, env vars, nvm sourcing, background processes, health checks. This lets the user restart with one command. Use the template at `templates/start-native.sh` — copy it to the project root, fill in the {{PLACEHOLDERS}}, and `chmod +x`.

## Common pitfalls

- **Wrong DB_HOST**: docker-compose uses service names (`postgres`), native needs `localhost` or `127.0.0.1`.
- **Schema search_path**: tables in `ecommerce`/`banking` schemas need `SET search_path TO ecommerce, banking, public` before queries.
- **JSON key mismatches**: docker-compose projects often have data files with keys that differ from what the code expects. Check ALL JSONs for actual top-level keys vs what `load_json`/`bank.get("questions", [])` expects.
- **Frontend field name mismatches**: React components may reference `data.live_coding` when JSON has `livecoding_tasks`, or `t.question` when JSON has `t.task`. Check both data AND component code.
- **npm install silently hanging**: kill and retry with `--prefer-offline` if it stalls for >2 min.
- **pg_hba.conf revert**: after setup, restore the backup: `sudo cp pg_hba.conf.bak pg_hba.conf && reload`.
- **Password masking in patch strings**: terminal password masking can corrupt strings containing `***`. Use distinct non-masked placeholders like `demo-token` in patch/old_string/new_string. Always `read_file` after patching to verify the actual content.
- **git merge unrelated histories**: GitHub auto-creates a default branch (e.g. `master`) with an initial commit. Merging a separately-initialized branch requires `git merge main --allow-unrelated-histories`. Conflicts in auto-generated files (README.md, .gitignore) should be resolved with `git checkout --theirs <file>` to keep the project version.
- **Node.js version in non-interactive shells**: background/non-login shells may pick up system Node instead of nvm. Symptom: `SyntaxError: Unexpected token '??='`. Always source nvm before npm/node commands: `export NVM_DIR="$HOME/.nvm"; [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"`.

## Screenshot-driven verification (OCR)

When the user provides reference screenshots of expected UI/schema/API format:

1. Check if `tesseract` is available: `which tesseract`
2. Serve images for browser access: `python3 -m http.server 9999 &`
3. OCR with Russian+English: `tesseract image.jpg stdout -l rus+eng`
4. Compare extracted structure (table names, columns, field names, flow steps) against actual code
5. Screenshots are the spec — fix mismatches, don't argue

## When Docker IS available later
The docker-compose.yml is still the canonical deployment. Native is a fallback. Don't delete docker files.

## References
- `references/qa-trainer-session-fixes.md` — concrete fix transcript from a multi-service QA interview trainer project: backend JSON key mismatches, schema search_path, frontend field name corrections, SQL trainer enrichment patterns.
- `references/vite-kuromoji-integration.md` — Vite + CJS npm dependency integration pattern: kuromoji/kuroshiro setup, custom middleware for binary assets, polyfills, type declarations, singleton hook pattern, MyMemory API gotcha.

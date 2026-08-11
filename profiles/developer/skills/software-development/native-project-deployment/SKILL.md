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
- **Homebrew node shadows nvm node (this user's Mac)**: `which node` can resolve to `/usr/local/opt/node@14/bin/node` even when nvm has a newer Node installed (e.g. v20.20.0), if the Homebrew node path precedes nvm on `$PATH`. Current Vite needs Node ≥18, so `npm create vite@latest` / `npm run dev` will fail or silently scaffold under the wrong version. **Reliable fix — prepend the explicit nvm node bin dir to PATH for that command** rather than relying on source-order guessing:
  ```bash
  export PATH="$HOME/.nvm/versions/node/v20.20.0/bin:$PATH" && node --version  # confirm, then run npm/vite
  ```
  Do this per npm command unless you've confirmed the export persists for the session. Check `which -a node npm` to see every candidate and pick `~/.nvm/versions/node/<ver>/bin` (the nvm path is always a valid full Node install without needing `nvm.sh` loaded).
- **Package-style FastAPI app fails with `No module named 'backend'`**. If `main.py` does `from backend.database import ...` / `from backend.routers import ...`, the app is package-style and step 4's `cd backend && uvicorn main:app` **fails** with `ModuleNotFoundError: No module named 'backend'` (the `backend` package isn't on `sys.path`). Launch from the repo root with the package-qualified module path instead:
  ```bash
  cd ~/proj && ./venv/bin/uvicorn backend.main:app --port 8000
  ```
  Check the top of `main.py` for a `from backend.` import to decide which form to use before `kill %1`-style attempts.
- **Port-holder that won't respond**: `lsof -ti:<port>` returning a PID while `curl` still gets `000`/`ECONNREFUSED` means the listener is wedged, not "up". There may be multiple competing supervisor wrappers (`pgrep -fl uvicorn` shows several `zsh -lic "… uvicorn …"` processes fighting to bind). Before debugging a frontend against a "ready" backend, confirm the API actually answers; and only kill processes you started — a supervisor wrapper that predates your session belongs to the user, so work around it (use a free port / different backend) rather than killing it.
- **Foreground `trap 'kill $P1 $P2; exit' INT TERM` + `wait` silently orphaning servers**: In a foreground-style launch script that backgrounds both servers then does a `trap`-on-INT/TERM + `wait`, SIGINT sent **only to the script PID** does NOT kill the children — bash defers the trap handler until the blocking `wait` returns, and `wait` never returns because the servers don't exit on their own. Net effect: Ctrl+C does nothing and backend+frontend are orphaned. This is NOT a daily-user bug because a real terminal Ctrl+C delivers SIGINT to the whole foreground **process group**, so uvicorn/vite get it directly and shut down (verified: servers log clean shutdown and ports are released). It only bites when something signals just the leader PID (some supervisors/Docker stop). Mitigations: (1) prefer the `nohup … &` exit-and-leave-running pattern (see `templates/start-native.sh`) when the script should hand control back; (2) if you keep trap+wait, rename the wrapper trait in comments: real Ctrl+C works, so just document it; (3) to make single-PID SIGINT also work you can `kill` from a `wait $PID` loop but that fights bash semantics — don't over-engineer.
- **Verifying a launch script's Ctrl+C / kill behavior — simulate the process group, NOT single-PID**: To prove a `start.sh` stops its servers, send SIGINT/SIGTERM to the whole process **group**, which is what a real terminal does — otherwise you'll get a false "script is broken" negative. On macOS `setsid` is NOT on PATH by default, so drive it from Python instead:
  ```python
  import os, signal, time, subprocess
  pid = os.fork()
  if pid == 0:
      os.setsid()                      # child becomes new session/group leader
      os.execv("/bin/bash", ["/bin/bash", "/abs/path/start.sh"])
  else:
      time.sleep(12)                   # let both servers boot
      # probe health + http 200 first
      os.killpg(pid, signal.SIGINT)    # real Ctrl+C == SIGINT to the group
      time.sleep(4)
      os.system("lsof -ti:8000; lsof -ti:5173")  # should print nothing => ports freed
  ```
  Expect the bash wrapper itself to still be alive a few seconds after group-SIGINT (it's blocked in `wait`); what matters is that children are gone and ports are freed. Probe ports with `lsof -ti:<port>` after the kill, and always clean up any orphaned PIDs you created.

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

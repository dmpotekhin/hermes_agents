# Task 11 — Kids Learn frontend pages (HomePage.jsx, LessonPage.jsx)

Part of the incremental-SDD Kids Learn build (FastAPI + Vite React). Task 11 creates two
page components that wire together the components/api built in tasks 8-10. Code was
verbatim-clean (no bugs this time) — the real work was behavioral verification and
teasing apart backend-infra noise from frontend defects.

## What "verify the pages render" actually required

`npm run build` passing is NOT proof the pages render. Static import-existence checks
(resolve every `../x` import, confirm each component/.js export exists) prove the module
graph, not runtime behavior. To prove the pages render against real API data:

1. Build: `npm run build` (must pass clean — exit 0).
2. Fetch raw HTML/route: `curl http://localhost:4173/lesson/lesson_math_basics` etc.
   (SPA fallback returns index.html regardless — shallow).
3. **Real render gate** — serve the built app and drive a browser:
   ```bash
   # Node 20 (nvm) + preview server (serves dist/ AND applies vite server.proxy)
   export PATH="$HOME/.nvm/versions/node/v20.20.0/bin:$PATH"
   cd frontend && npm run preview -- --port 4173   # tracked background process
   ```
   Then either the playwright MCP tools or a Playwright script to:
   - assert `.lesson-card` count > 0 from live `/api/lessons`
   - assert conditional logic: `completed_count>0 ? 'Продолжить' : 'Начать'` renders the
     right label per lesson
   - click a card → assert `.task-question`, `.task-number "Задание 1 из N"`, hint btn,
     answer input, disabled "✅ Проверить" until answer typed.

## Vite preview proxy + CORS nuance

- `vite preview` (4173) **does apply the `server.proxy` block** from `vite.config` — so
  the SPA's `/api` requests are proxied same-origin to the backend. This means a backend
  CORS allow-list that only names the dev origin (`localhost:5173`) is NOT a blocker when
  verifying via preview:4173 — same-origin requests bypass CORS entirely.
- Verify the proxy chain directly first (no browser needed):
  `curl :4173/api/lessons` vs `curl :8000/api/lessons` → identical body proves forwarding.

## Backend module import path (this repo / package-style FastAPI)

`backend/main.py` does `from backend.database import init_db` and `from backend.routers import ...` —
it is **package-style**, not single-module. Running `uvicorn main:app` from inside `backend/`
fails with:
```
ModuleNotFoundError: No module named 'backend'
```
Correct invocations (must use the project root as cwd + package module path):
```bash
cd ~/projects/kids-learn && ./venv/bin/uvicorn backend.main:app --port 8000
```

## Distinguishing backend-infra noise from a frontend defect

Symptom: the page renders correctly, but the live verify is flaky — intermittent
`curl` `000` (conn refused), `ECONNREFUSED` from the vite proxy, `address already in use`
on backend start, and console `Failed to load resource ... 500` on `/api/stats`.

Diagnosis before blaming the frontend:
```bash
lsof -ti:8000                 # who holds the port (may be EMPTY while calls still fail)
pgrep -fl uvicorn             # competing wrapper processes (`zsh -lic` supervisors)
```
On this machine multiple `zsh -lic "… source venv/bin/activate && uvicorn …"` supervisor
wrappers fight over port 8000; port hold + proc list drift between calls. A `lsof` that
returns a PID while curl still gets `000` means the listener holds the port but is
unresponsive. One pre-existing backend bug surfaced as a symptom: `/api/stats` threw
`sqlite3.OperationalError: no such table: user_stats` (in `progress_service`), which
crashed the endpoint (500 in-browser) — unrelated to the two page files (they call
`getLessons`/`getLesson`/`checkTask`, not `getStats`).

**Rule:** when a page verify fails, isolate WHICH api call failed and whether the backend
served it. If the failing call is one the page never makes, the failure is infra/backend,
not the frontend — verify the page's own calls (`/lessons`, `/lessons/:id`,
`/tasks/:id/check`) directly and report the frontend as conditionally-verified.

## Verbatim-code verdict

The brief's two files were clean — no bugs found this task (unlike tasks 4/6/10). Imported
functions (`getLessons`, `getLesson`, `checkTask`) existed with correct signatures. Verdict:
copy as-is. The task's only friction was the verification environment, which is the
takeaway above.

## Cleanup note
- Start preview/backend as **tracked background processes** (readiness watch patterns);
  `kill` them via the process tool when done — don't leave orphans. They show back up on
  `pgrep -fl` and fight the next session for the port.
- Kill only processes YOU started. Supervisor/`zsh -lic` uvicorn that predates the session
  belongs to the user — leave it and work around it (or ask).

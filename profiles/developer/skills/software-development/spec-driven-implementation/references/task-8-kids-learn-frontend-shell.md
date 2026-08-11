# Task 8: Kids Learn frontend shell — Vite 8 proxy + build-vs-dev Node nuance

Concrete example from the Kids Learn spec-driven project (`frontend/`): the brief specified Vite proxy
config, a fetch-wrapper API layer (`src/api.js`), a React Router `App.jsx` shell, `main.jsx` (React 19),
and boilerplate cleanup. "Follow brief code verbatim" — and here the brief code was correct and applied
verbatim, but the **verification** surfaced durable procedural learnings.

## Brief output (all matched verbatim; no brief bugs)
- `vite.config.js` — `server.port: 5173` + `proxy: { '/api': 'http://localhost:8000' }`.
- `src/api.js` — `BASE='/api'`, generic `request()`, `getLessons/getLesson(id)/checkTask(taskId,answer)/getStats()`.
- `src/App.jsx` — `BrowserRouter` + `Routes`: `/` → `HomePage`, `/lesson/:lessonId` → `LessonPage`; imports `./styles/index.css`.
- `src/main.jsx` — React 19 `createRoot` + `StrictMode`.
- Removed `App.css` and `index.css`; created empty `src/styles/index.css` + empty `src/pages/`, `src/components/`, `src/styles/` dirs.
- Committed `feat: add frontend shell with API layer and routing`.

Note: `App.jsx` imports `HomePage`/`LessonPage` which do **not exist yet** (built in later tasks). This
is expected and fine — see "Expected-vs-real" below.

## Learning 1 — the brief's `npm run dev & ... curl ... kill %1` form is blocked
The brief's single-command verify (`npm run dev & sleep 3; curl; kill %1`) is rejected by the runtime's
long-lived-process guard (a foreground command that stays alive). Correct approach for Vite/FastAPI dev
servers: start each as a **tracked background process** (need `background=true`, ideally
`watch_patterns` so you get the "ready"/"Uvicorn running" signal), `process wait`/poll until the
readiness line appears, `curl` to verify, then `kill`. Do not smuggle `&`/`nohup`/`disown` into a
foreground command just to dodge the guard.

## Learning 2 — `vite build` vs `npm run dev` under old Node (sharper than the generic Node pitfall)
On this Mac the default shell `node` is **v14.21.3**, and nvm has **v20.20.0**. Vite 8:
- **`npm run dev` (dev server) works under Node 14** — the Vite dev server pre-transform/ESBuild handles
  modern syntax in-browser, so it starts and serves fine. Good enough to curl the root and transform `App.jsx`.
- **`npm run build` (production) crashes under Node 14** — rolldown parses in-process and dies with
  `SyntaxError: Unexpected token '??='`. Exit 1.
So **a green dev server is NOT proof the build works.** The build gate must run under Node ≥20.19:
```bash
export PATH="$HOME/.nvm/versions/node/v20.20.0/bin:$PATH" && node -v   # then npm run build
```
This is a sharper case than the existing native-project-deployment Node pitfall (which is about
`npm create vite` / `npm run dev` failing under old Node): here dev tolerates old Node and only the
build gate requires Node 20. Verify `node --version` before any `vite build`.

## Learning 3 — verify the Vite `/api` proxy end-to-end (not just that the server starts)
Serving the HTML proves Vite is up, not that the proxy works. To prove the proxy:
1. Start backend on 8000 (tracked background: `uvicorn backend.main:app --port 8000` from project root).
2. Start `npm run dev` (5173) as above.
3. `curl -s http://localhost:5173/api/lessons` and compare to `curl -s http://localhost:8000/api/lessons`
   (identical body) plus `curl -s http://localhost:5173/api/health` → `{"status":"ok"}`.
4. Backend log shows the proxied requests as `GET /api/lessons 200 OK` — confirms forwarding, not a
   direct-8000 hit from the browser.

Reminder: also cross-check the api.js route strings (`/lessons`, `/lessons/${id}`, `/tasks/${taskId}/check`,
`/stats`) against the FastAPI router `prefix=`+decorators, so the wrappers and backend agree.

## Learning 4 — "Expected-vs-real" verification discipline for incremental SDD
When a task's App shell imports modules owned by *later* tasks, the build's failure is **expected, not a
defect**. In the temp verification script, assert:
- `exit code == 1` (expected — pages not built yet),
- **exactly** the 2 unresolved imports are `./pages/HomePage` + `./pages/LessonPage`,
- no other resolve/syntax/config errors (filter rolldown's aggregate banners like
  `error during build:` / `Build failed with N errors:` out of the "unexpected errors" count — they wrap
  the page errors and don't name the module).
Report the pass as "intended pending-import state", not "build green". Same discipline in the report file:
say explicitly this is ad-hoc verification (`vite build` + `oxlint` are the available gates — no unit-test
target), not a canonical suite green.

## Verified gates
- `oxlint` clean on `api.js`, `App.jsx`, `main.jsx`, `vite.config.js`.
- `vite build` (Node 20) fails only on the two page imports; Dev server + proxy verified via curl.

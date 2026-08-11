# FastAPI backend verification — evidence-first checks

Session-specific detail captured from verifying a FastAPI `backend/` project (Kids Learn, FastAPI 0.141.1, non-installed backend dir).

## Ground truth: route wiring

In FastAPI 0.141.1, `app.include_router(...)` registers the router as an `_IncludedRouter` object (a nested mount), NOT flattened `APIRoute` instances. Consequences:

```python
paths = [getattr(r, "path", None) for r in app.routes]
# -> ['/openapi.json', '/docs', '/docs/oauth2-redirect', '/redoc', None, None, '/api/health']
#    ^^ wait those two Nones are the two include_router'd routers
```

So you CANNOT assert wiring via `any(r.path == "/api/x" for r in app.routes)` — even correct code shows `None` there. `_IncludedRouter` exposes no `routes`/`subroutes`/`router`/`_routes` attr to recurse into either (dir() inspection comes up empty).

**Authoritative check — run the full app:**
```python
from fastapi.testclient import TestClient
from backend.main import app
with TestClient(app) as client:   # context manager triggers lifespan -> init_db()
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/lessons/lesson_python_basics").status_code == 200
    # no-answer-leak check: assert "correct_answer" not in json
    r = client.post("/api/tasks/py_task_1/check", json={"answer": "1"})
    assert r.status_code == 200 and r.json()["correct"] is True
```
This exercises routing through the `_IncludedRouter` mounts, runs the lifespan handler, and returns real response bodies — better than any route-inspection heuristic.

TestClient emits `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` — ignore; judge by assertions/exit code, not stderr noise.

## Launch-command gotcha

```
cd backend && uvicorn main:app          # FAILS: ModuleNotFoundError: No module named 'backend'
```
`backend/` is a plain directory, not an installed package, so from cwd=backend the `backend.*` imports (e.g. `from backend.database import init_db`) can't resolve. Durable fix (project root is the import root):
```
cd <project-root> && ./venv/bin/uvicorn backend.main:app --app-dir <project-root> --port 8000
```
Or `PYTHONPATH=<project-root>`. If a brief/doc specifies the broken short form, treat the code as fine and note the corrected launch path in the report — don't "fix" the code.

## Progress/DB side-effect note

`init_db()` (called by lifespan) creates `backend/.kids_learn.db`. `TestClient` and live checks that hit `/check` or `/stats` mutate this DB (award points, advance streak). For repeatable evidence prefer a throwaway DB path (override `settings.db_path`) or reset the DB between runs.

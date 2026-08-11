---
name: fullstack-fastapi-react
description: Scaffold and develop fullstack web apps with FastAPI backend + React/Vite frontend + SQLite. Use when starting a new web project with this stack.
---

# Fullstack FastAPI + React + Vite + SQLite

Project template and pitfalls for greenfield fullstack apps with Python backend and React frontend.

## When to Use

- Starting a new web app with FastAPI (Python) + React (Vite) + SQLite
- Adding a frontend to an existing FastAPI service
- The user asks for a "web app" or "fullstack app" with these technologies

## Project Structure

```
project/
├── backend/
│   ├── main.py              # FastAPI app, CORS, lifespan
│   ├── config.py            # dotenv, settings dataclass
│   ├── database.py          # SQLite: init_db, get_db context manager
│   ├── models.py            # Pydantic request/response models
│   ├── services/            # Business logic
│   ├── routers/             # API route handlers
│   └── lessons/             # Static data (JSON/YAML)
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # BrowserRouter + Routes
│   │   ├── api.js           # fetch wrappers to /api/*
│   │   ├── pages/           # Route-level components
│   │   ├── components/      # Reusable UI components
│   │   └── styles/          # Global CSS
│   └── vite.config.js       # Proxy /api → localhost:8000
├── .env                     # DEEPSEEK_API_KEY, etc.
├── .env.example             # Template without secrets
├── .gitignore               # .env, venv/, node_modules/, dist/, *.db
├── requirements.txt         # Python deps
├── start.sh                 # Launch both servers
└── venv/                    # Python virtualenv at project root
```

## Scaffolding Commands

```bash
# Backend
mkdir -p backend/{services,routers}
python3 -m venv venv && source venv/bin/activate
pip install fastapi uvicorn openai python-dotenv

# Frontend (requires Node ≥18, prefer 20+)
npm create vite@latest frontend -- --template react
cd frontend && npm install
npm install react-router-dom @codemirror/view @codemirror/state @codemirror/lang-python @codemirror/theme-one-dark
```

## Critical Pitfalls

### 1. Node version
macOS default `node` is often v14 — too old for Vite ≥5. Use nvm:
```bash
export NVM_DIR="$HOME/.nvm" && . "$NVM_DIR/nvm.sh" && nvm use 20
```
Vite 8+ requires Node 20.19+ or 22.12+.

### 2. uvicorn startup path
Run from project root, NOT from `backend/`:
```bash
uvicorn backend.main:app --port 8000    # ✓ correct
cd backend && uvicorn main:app --port 8000  # ✗ ModuleNotFoundError: No module named 'backend'
```

### 3. Vite proxy config
```js
// frontend/vite.config.js
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': 'http://localhost:8000' },
  },
})
```

### 4. CORS
FastAPI must allow the Vite dev server origin:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 5. .gitignore must include
```
.env
venv/
__pycache__/
*.pyc
node_modules/
dist/
*.db
```

### 6. React version drift
`npm create vite@latest -- --template react` scaffolds the latest React (19+ as of 2026). If the plan says "React 18", the scaffolded version wins — adapt, don't fight it. The breaking changes are minimal for typical app patterns.

### 7. codemirror meta-package
`import { basicSetup } from 'codemirror'` requires the `codemirror` meta-package — installing `@codemirror/view`, `@codemirror/state`, etc. is NOT enough. Add:
```bash
npm install codemirror
```
The `@codemirror/*` sub-packages provide individual modules, but `basicSetup` is a convenience export only in the meta-package.

### 7b. Backend pytest + async fixtures (pytest-asyncio 0.24+)
When testing a FastAPI app with httpx `ASGITransport`, an `async def` test fixture MUST be decorated with `@pytest_asyncio.fixture`, NOT `@pytest.fixture`. Using plain `@pytest.fixture` on an async fixture fails at test time with:
```
AttributeError: 'async_generator' object has no attribute 'get'
```
(pytest-asyncio ≥0.24 treats it as a sync generator and hands back the un-awaited async_generator). Correct pattern:
```python
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from server import app

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
```
Add `pytest.ini` to silence `PytestDeprecationWarning(_DEFAULT_FIXTURE_LOOP_SCOPE_UNSET)` and future-proof:
```ini
[pytest]
asyncio_default_fixture_loop_scope = function
```
This is a real trap in plan-transcribed test code — a "known-good" snippet in a plan frequently ships `@pytest.fixture` on an async fixture and fails out of the box. Run the test before trusting it.

### 7c. FastAPI StaticFiles mount requires the dir to exist
`app.mount("/", StaticFiles(directory="static", html=True), name="static")` raises at **import time** (starlette) if `static/` doesn't exist — so `import server` and the whole app fail to load. When a plan's server skeleton mounts static files but never instructs creating the directory, add at least a placeholder `static/index.html`, or the app won't start.

### 8. React header refresh pattern
A static `Component._refresh` hack with dynamic `import()` does NOT work across component boundaries (returns fresh module reference). Use a `refreshTrigger` prop:
```jsx
// Parent: increment trigger after state change
const [trigger, setTrigger] = useState(0);
return <Header refreshTrigger={trigger} />;

// Header: re-fetch on trigger change
export default function Header({ refreshTrigger = 0 }) {
  useEffect(() => { fetchStats(); }, [refreshTrigger]);
}
```

### 7. start.sh pattern
```bash
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
uvicorn backend.main:app --port 8000 --reload &
cd frontend && npm run dev &
cd ..
trap "kill 0" INT TERM
wait
```

## Admin Panel Pattern

For content-managed apps (courses, lessons, tasks), add an admin panel at `/admin`:

**Backend (`routers/admin.py`):**
- CRUD on JSON/YAML lesson files in `backend/lessons/`
- `POST /api/admin/generate-hint` — AI-generated hints (DeepSeek/OpenAI)
- Separate from public API — admin endpoints return `correct_answer`, public ones strip it

**Frontend:**
- `AdminPage.jsx` — list lessons with edit/delete buttons
- `LessonEditor.jsx` — full editor with task CRUD, type-specific fields, hint generation button
- Hidden link in homepage footer (no auth for MVP)

**Lesson editor key features:**
- Task type selector (choice/number/text/code) with dynamic fields
- Choice: options list + radio for correct answer
- Code: expected_output + correct_answer textarea
- Hint: text field + "🤖 Generate" button calling admin API
- Points per task
- Save → PUT to backend, redirect to admin list

Use a context manager with WAL mode:
```python
def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

## Verification

After scaffolding, verify:
```bash
# Backend health
curl http://localhost:8000/api/health  # → {"status":"ok"}

# Frontend dev server
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173  # → 200

# Full build
cd frontend && npm run build  # must exit 0
```

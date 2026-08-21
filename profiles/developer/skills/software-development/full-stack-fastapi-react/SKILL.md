---
name: full-stack-fastapi-react
description: "Greenfield full-stack web app with FastAPI backend, Vite React frontend, and SQLite"
---

# Full-Stack FastAPI + React (Vite)

Scaffold, build, and verify a full-stack web application with FastAPI backend, Vite React frontend, and SQLite database.

## When to Use

- Starting a new web project with Python backend + React frontend
- Building a monolith-style app with separate backend/frontend directories
- Need SQLite for local-first data storage
- Quick prototyping with a known-good project structure

## Project Structure

```
project/
├── backend/                # FastAPI
│   ├── main.py             # App entry, CORS, lifespan
│   ├── config.py           # Settings (env vars, DB path)
│   ├── database.py         # SQLite init + connection
│   ├── models.py           # Pydantic models
│   ├── routers/            # API route modules
│   ├── services/           # Business logic
│   └── data/               # Static data files (JSON, etc.)
├── frontend/               # Vite + React
│   ├── vite.config.js      # Dev proxy → backend
│   └── src/
│       ├── api.js          # Fetch wrappers
│       ├── App.jsx         # Router
│       ├── pages/          # Route pages
│       ├── components/     # Reusable components
│       └── styles/         # CSS
├── .env.example            # Template for env vars
├── requirements.txt
└── start.sh                # Launch both servers
```

## Scaffolding Steps

### 1. Backend

```bash
mkdir -p backend/{routers,services,data}
touch backend/__init__.py backend/routers/__init__.py backend/services/__init__.py
python3 -m venv venv && source venv/bin/activate
pip install fastapi uvicorn openai python-dotenv
pip freeze > requirements.txt
```

### 2. Frontend

```bash
npm create vite@latest frontend -- --template react
cd frontend && npm install
npm install react-router-dom @codemirror/view @codemirror/state @codemirror/lang-python @codemirror/theme-one-dark
```

### 3. Vite proxy config

```javascript
// vite.config.js
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': 'http://localhost:8000' },
  },
});
```

### 4. CORS setup

```python
# backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 5. Start script

```bash
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
uvicorn backend.main:app --port 8000 --reload &
cd frontend && npm run dev &
wait
```

## Pitfalls

- **uvicorn path:** Run `uvicorn backend.main:app` from project root, NOT `cd backend && uvicorn main:app`. The latter breaks relative imports.
- **Prefer plain `uvicorn` over `uvicorn[standard]`:** the `[standard]` extra pulls uvloop/httptools/watchfiles (C/Rust builds) which fail on machines without Xcode CLT. Plain uvicorn (asyncio + h11) is enough for local apps and installs from wheels with no native builds.
- **Node version:** Vite 6+ requires Node ≥18. Default macOS `node` may be v14. Use nvm: `export PATH=~/.nvm/versions/node/v20.x.x/bin:$PATH`.
- **Frontend build errors:** Missing page imports (from later tasks) are expected during incremental development. Build will pass once all pages exist.
- **Port conflicts:** `lsof -ti:8000 | xargs kill` to free the port before restarting.

## Ad-Hoc Verification

Prefer a committed `tests/` suite run with `python -m pytest` — it is the
canonical, repeatable verification and covers API end-to-end via `TestClient`.
Inline `python -c` and arbitrary-path temp scripts can hit a terminal consent
prompt that stalls without a user reply, while `python -m pytest` and
`python -m <module>` run clean. Use the temp-script pattern below only for
projects with no test suite:

```python
import tempfile, os, subprocess

code = r'''
import sys
ok = fail = 0
def check(name, cond):
    global ok, fail
    if cond: ok += 1; print(f"PASS {name}")
    else: fail += 1; print(f"FAIL {name}")

# ... verification checks ...

print(f"\n{ok}/{ok+fail} PASSED")
sys.exit(0 if fail == 0 else 1)
'''

fd, path = tempfile.mkstemp(prefix="hermes-verify-", suffix=".py")
with os.fdopen(fd, 'w') as f: f.write(code)
result = subprocess.run(["python3", path], capture_output=True, text=True, timeout=30)
print(result.stdout)
os.unlink(path)
```

**Conventions:**
- Prefix: `hermes-verify-*.py`
- Output: `PASS/FAIL <name>` per line, final `N/M PASSED` summary
- Exit 0 on all-pass, 1 on any failure
- Always `os.unlink()` after run

## API Patterns

### Public endpoints (no auth)
```python
router = APIRouter(prefix="/api/...", tags=["..."])
@router.get("/items")
async def list_items(): ...
```

### Admin endpoints (with answers)
```python
router = APIRouter(prefix="/api/admin", tags=["admin"])
@router.get("/items")       # Full data
@router.post("/items")      # Create
@router.put("/items/{id}")  # Update
@router.delete("/items/{id}")  # Delete
```

### Response models
Separate public models (no secrets) from admin models (full data):
```python
class ItemPublic(BaseModel):     # No correct_answer
class ItemAdmin(BaseModel):      # Includes correct_answer
```

## Bundled Files

- `references/ad-hoc-verification.md` — Temp-script verification pattern for testless projects + late delegate handling in SDD
- `templates/start.sh` — Launch script for backend + frontend dev servers

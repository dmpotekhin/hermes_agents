# Full-Stack Project Template (FastAPI + Vite + SQLite)

Reference architecture from a completed 13-task SDD run (Kids Learn app).
Use when scaffolding similar fullstack projects.

## Directory Layout

```
project/
├── backend/
│   ├── main.py              # FastAPI app, CORS, lifespan
│   ├── config.py            # Settings dataclass, dotenv
│   ├── database.py          # SQLite: init_db, get_db contextmanager
│   ├── models.py            # Pydantic request/response models
│   ├── services/            # Business logic
│   │   ├── lesson_service.py
│   │   ├── check_service.py
│   │   ├── sandbox_service.py
│   │   ├── ai_service.py
│   │   └── progress_service.py
│   ├── routers/             # API route handlers
│   │   ├── lessons.py       # Public: GET /api/lessons
│   │   ├── tasks.py         # Public: POST /api/tasks/{id}/check
│   │   └── admin.py         # Admin: CRUD lessons + AI hints
│   └── lessons/             # JSON seed data (editable)
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # BrowserRouter with all routes
│   │   ├── api.js           # fetch wrappers (/api/*)
│   │   ├── main.jsx
│   │   ├── pages/           # HomePage, LessonPage, AdminPage, LessonEditor
│   │   ├── components/      # Header, task types, ResultPanel, ProgressBar
│   │   └── styles/
│   │       └── index.css    # Single-file design system (CSS variables)
│   └── vite.config.js       # proxy /api → localhost:8000
├── .env.example             # API keys (never commit .env)
├── .gitignore               # .env venv/ node_modules/ dist/ .kids_learn.db
├── requirements.txt         # pip freeze output
├── start.sh                 # Launch backend + frontend
└── README.md
```

## Key Decisions

| Choice | Rationale |
|--------|-----------|
| `uvicorn backend.main:app` from project root | Python package imports (`from backend.database import ...`) |
| Vite proxy instead of CORS-only for dev | Double safety — proxy + CORS whitelist |
| SQLite for MVP | Zero setup, single file, sufficient for single-user |
| JSON lesson files | Editable without code changes, easy to add courses |
| `execute_code` for integration tests | Avoids `curl \| python3` security blocks |
| Single CSS file with CSS variables | Simpler than CSS modules for <20 components |
| Admin panel at `/admin` route | No auth needed for MVP; hidden link in footer |

## Common Gotchas

1. **uvicorn must run from project root** — not `cd backend/`
2. **`.env` and `venv/` in `.gitignore`** — Vite's `create-vite` doesn't add venv
3. **Node 20 via nvm** — system Node often v14, too old for Vite 7+
4. **`pip freeze` for requirements.txt** — fast, reproducible, but pins transitive deps
5. **`codemirror` meta-package** — `basicSetup` import needs `codemirror`, not just `@codemirror/*`
6. **API answer leak** — public lesson endpoint MUST strip `correct_answer` and `expected_output`
7. **Header refresh** — use `refreshTrigger` prop + `useEffect` dependency, NOT static `_refresh` hack

## Task Plan Template

For a 13-task SDD run on a similar project:

| # | Task | Files |
|---|------|-------|
| 1 | Scaffolding | `backend/`, `frontend/` (vite), venv, deps |
| 2 | Config + DB | `config.py`, `database.py`, `models.py` |
| 3 | Seed data | `lessons/*.json`, `lesson_service.py` |
| 4 | Business logic | `check_service.py`, `sandbox_service.py` |
| 5 | AI integration | `ai_service.py` (DeepSeek/OpenAI) |
| 6 | Progress | `progress_service.py` |
| 7 | Routers + main | `routers/`, update `main.py` |
| 8 | Frontend shell | `vite.config.js`, `api.js`, `App.jsx` |
| 9 | Styles | `index.css` |
| 10 | Components | `Header`, task types, `ResultPanel` |
| 11 | Pages | `HomePage`, `LessonPage` |
| 12 | Polish | `start.sh`, `README.md`, integration tests |
| 13 | Verify | Full endpoint verification |

# SQLAlchemy Async Pitfalls

Patterns from Travel Content Factory development. FastAPI + SQLAlchemy 2.0 async + aiosqlite.

---

## DetachedInstanceError on lazy relationships

**Symptom:** `Internal Server Error` when returning Project objects via API. Traceback points to `_project_to_dict → p.clips → lazy load → session closed`.

**Root cause:** FastAPI `Depends(get_db)` yields a session, the route returns a dict, but `_project_to_dict` accesses lazy-loaded relationships AFTER the async context manager closes the session.

**Fix — eager loading:**
```python
from sqlalchemy.orm import selectinload

q = select(Project).options(
    selectinload(Project.clips).selectinload(ProjectClip.media)
).where(Project.id == project_id)
```

**Anti-pattern — refresh doesn't help:**
```python
await db.refresh(p)  # does NOT load relationships eagerly
return _project_to_dict(p)  # still fails
```

**Correct pattern — re-query after mutation:**
```python
await db.commit()
# Re-query with eager loading — don't reuse the stale object
q = select(Project).options(
    selectinload(Project.clips).selectinload(ProjectClip.media)
).where(Project.id == p.id)
result = await db.execute(q)
p = result.scalar_one()
return _project_to_dict(p)
```

---

## SQLite path resolution

**Symptom:** `sqlite3.OperationalError: unable to open database file`

**Root cause:** `DATABASE_URL=sqlite+aiosqlite:///./data/travel_factory.db` — `./data/` resolves relative to CWD (where uvicorn runs, typically `backend/`), not project root.

**Fix — compute absolute path from `__file__`:**
```python
import pathlib
_default_db = str(pathlib.Path(__file__).parent.parent / "data" / "travel_factory.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{_default_db}")
```

Don't set `DATABASE_URL` in `.env` unless using an absolute path. The auto-computed default is preferred.

---

## FastAPI: static mount shadows routes

**Symptom:** `GET /api/health` → 404, but `GET /api/media/list` works fine.

**Root cause:** In FastAPI, `app.mount("/", StaticFiles(...))` shadows any routes defined AFTER it.

**Fix — order matters:**
```python
# 1. All API routers FIRST
app.include_router(media.router)
app.include_router(projects.router)
app.include_router(ai.router)

# 2. Health check BEFORE mount
@app.get("/api/health")
async def health():
    return {"status": "ok"}

# 3. Static mount LAST
app.mount("/", StaticFiles(directory=frontend_dir, html=True))
```

---

## expire_on_commit and async sessions

Setting `expire_on_commit=False` on the session factory prevents SQLAlchemy from expiring attributes after commit, but it does NOT keep lazy relationships loaded. Always use `selectinload()` for any relationship that will be serialized.

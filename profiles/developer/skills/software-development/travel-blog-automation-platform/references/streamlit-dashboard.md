# Streamlit dashboard + browser photo ingest (travel-blog-app)

The UI is `ui/dashboard.py` (Streamlit), a thin shell over the SAME modules the CLI
uses. It is NOT behind the FastAPI app (`app.py`) — it calls `modules/*` directly.

## Launch: project-root import must be bootstrapped

`streamlit run ui/dashboard.py` puts `ui/` on sys.path, NOT the project root. Without a
bootstrap, `from core.config import Config` raises ModuleNotFoundError even when launched
from the project root. Add at the TOP of `ui/dashboard.py`, before any project import:

```python
import os, sys
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
```

## Per-rerun fresh DB (aiosqlite)

Streamlit re-runs the whole script on every interaction. Open a fresh `Database()` per
rerun and close it in `finally` (`asyncio.run(...)`) — NEVER at module scope (dead loop /
aiosqlite loop leakage). Reusable wrappers:

```python
async def _run(action, *args, **kwargs):
    db = Database(); await db.connect()
    try:
        return await action(db, Config(), *args, **kwargs)
    finally:
        await db.close()

def _call(action, *args, **kwargs):          # sync wrapper for st.button
    try:
        return asyncio.run(_run(action, *args, **kwargs))
    except Exception as exc:
        st.error(f"Action failed: {exc}"); return None
```

## Action wiring

Each pipeline stage = one `st.tabs` tab + a button calling the SAME module function as the
CLI, then `st.rerun()` so the UI reflects the DB change:

```python
if st.button("Plan"):
    st.write(_call(_plan)); st.rerun()
```

One code path (modules) — DRY. `app.py` stays read-mostly; no need to add `approve`/`plan`
endpoints unless an API consumer actually needs them.

## Browser photo ingest — `modules/ingest.py`

Framework-agnostic; Streamlit passes `[(f.name, f.getvalue()) for f in st.file_uploader(...)]`.

- Validate with Pillow: `Image.open(BytesIO(data)).verify()` → reject non-images.
- Dedupe by `sha256` (look up the hash in the DB before insert).
- **Name files by hash prefix** `f"{city}_{year}_{sha[:16]}{ext}"`, NOT an `idx` counter —
  a per-call counter resets and collides on `UNIQUE(path)` on re-ingest. Hash-prefixed
  names are globally unique and collision-proof across batch calls.
- City upsert: `get_city_by_name(name, year)`; create with status QUEUED if missing; mark
  each photo `scan_status=SCANNED` so the content stage can process it.

## Verification

- Boot: `streamlit run ui/dashboard.py --server.port 8510 --server.headless true` → curl 200.
- Import smoke: a script that puts ONLY `ui/` on sys.path then `import dashboard` (simulates
  the launcher's sys.path — catches the import bug that `python -c` from root hides).
- Keep the full pytest suite green after any UI change.

## Pitfalls

- Don't verify launch via `python ui/dashboard.py` from the project root — sys.path differs
  from streamlit, so an import can pass in one launcher and fail in the other. Test under the
  real launcher.
- Long actions (content gen, scan) block the UI; acceptable locally, move to a background
  thread/queue if it becomes a problem.
- No auth in the dashboard — bind streamlit to localhost only.
- Upload form: `st.form(clear_on_submit=True)` + `st.file_uploader(accept_multiple_files=True)`;
  `st.expander("📤 Upload photos", expanded=True)` to surface it.

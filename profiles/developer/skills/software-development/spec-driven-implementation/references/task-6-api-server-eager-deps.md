# Task 6 — RAG-assistant API server: eager heavy deps at import + the stale-`app` fixture trap

FastAPI server task in the RAG-assistant project (ChromaDB vector store, DeepSeek LLM parser,
APScheduler). The brief's `server.py` was correct on routes but built every heavy dependency at
module load. That single choice produced two failures the tests exposed.

## The bug: eager construction at module import

The brief's reference code did, at the top of `server.py`:

```python
db = LinkDB(config)                 # SentenceTransformer model load (~20s+)
parser = CommandParser(config)      # requires DEEPSEEK_API_KEY
sched = ScheduleManager(config, db, "schedules.json")  # apscheduler BackgroundScheduler
```

Consequences observed:

1. **The /api/health test hung.** Importing the module blocked on the in-process
   `SentenceTransformer(...)` model load (torch). test_db.py (which builds `LinkDB` alone) took
   ~104s/5 → ~20s each, yet the module import with the same model load stalled well past 120-300s.
   Deferring only `ScheduleManager`/`parser` did NOT help — the culprit is the eager `LinkDB` model
   load at import. Every endpoint (not just ones that use `db`) pays for it because import is
   the gate.
2. **All tests broke when DEEPSEEK_API_KEY was unset.** `CommandParser(config)` calls
   `get_api_key()` which raises `RuntimeError` at module load → `import server` fails → pytest
   collection fails for the whole file, including tests that never touch chat. The brief claimed
   "other endpoints test fine without it," which is impossible under eager construction.

### The durable fix: per-route lazy singletons

```python
_db = _parser = _sched = None

def _get_db():
    global _db
    if _db is None:
        from db import LinkDB
        _db = LinkDB(config)
    return _db

def _get_parser():   # same pattern; CommandParser
def _get_sched():    # same pattern; ScheduleManager

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.text.strip():
        return ChatResponse(reply="Пустой запрос", action="unknown")
    try:
        parser = _get_parser()
        cmd = parser.parse(req.text)
    except Exception:
        return ChatResponse(reply="Не понял команду", action="unknown")
    return dispatch(cmd, _get_db(), config)
```

- Importing the module is now fast and never raises on a missing key.
- `/api/health` and the link/folder routes work regardless of LLM availability.
- `/api/chat` degrades to `"unknown"` gracefully when the key is missing or the LLM is down.
- Move the heavy module imports INSIDE the getter too, so even importing `scheduler` (→ apscheduler)
  is deferred.

## The stale-`app` fixture trap (pytest + FastAPI + importlib.reload)

The provided test file binds the app once at module import:

```python
from server import app          # binds the OBJECT at collection time

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.fixture
def api_context():
    os.environ["RAG_CHROMA_PATH"] = "./test_api_chroma_db"
    import importlib, server
    importlib.reload(server)    # creates a NEW app + NEW LinkDB against the test path
    yield
    ...
```

**`importlib.reload(server)` does not affect `client`.** `from server import app` bound the OLD
FastAPI instance into the test module's namespace; reload re-executes `server.py` into a NEW module
state and assigns a NEW `app`, but the test module's `app` name still references the old instance.
So requests through `client` hit the ORIGINAL app (default config → the REAL `./chroma_db`), and
the `RAG_CHROMA_PATH` override is silently ignored.

Consequences when the tests aren't trivially isolated:

- Count-based assertions (`len(resp.json()) == 1`) become unreliable because the real store retains
  links added by earlier tests (an "add" test leaves 1, the next "list" test adds on top → 2, fails).
- Browsing the real store is a side effect the fixture is supposed to prevent.

Robust alternatives:
- Make `client` resolve `app` from the module at request time: `ASGITransport(app=getattr(server, "app"))`,
  or build `client` AFTER `api_context` and pull the reloaded app via `server.app`.
- Drop the reload entirely and inject the DB path through the app's own config/lifespan in each test.
- At minimum, flag the fixture as-is (stale-app reload) in the report rather than trusting it provides
  isolation.

## Report-worthy deviations

This task deliberately deviated from the brief's literal server.py (lazy construction) for the
reasons above. State the deviation explicitly in the task report, with the "why" — the brief's eager
construction cannot satisfy its own claim that non-chat endpoints run without the API key.

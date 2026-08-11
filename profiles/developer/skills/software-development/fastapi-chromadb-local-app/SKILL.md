---
name: fastapi-chromadb-local-app
description: Build local macOS FastAPI apps with ChromaDB vector storage and sentence-transformers embeddings — scaffolding, lazy loading, test patterns, and pitfalls.
category: software-development
---

# FastAPI + ChromaDB Local App

Pattern for building macOS-local FastAPI applications with ChromaDB vector storage and sentence-transformers embeddings.

## When to Use

- Local RAG/vector-search apps on macOS
- FastAPI servers embedding ChromaDB and ML models
- Any app where heavy deps (ChromaDB, SentenceTransformer) should not block startup

## Architecture Pattern

```python
# server.py — LAZY LOADING for heavy dependencies

_db = None
_parser = None

def _get_db():
    global _db
    if _db is None:
        from db import LinkDB          # import INSIDE function
        _db = LinkDB(config)
    return _db

def _get_parser():
    global _parser
    if _parser is None:
        from commands import Parser    # import INSIDE function
        _parser = Parser(config)
    return _parser

# Use in routes:
@app.get("/api/data")
async def get_data():
    db = _get_db()   # lazy — first call triggers ChromaDB + model load
    return db.list_items()
```

**Why lazy:** ChromaDB loads SentenceTransformer on init (~20-90s). If done at module level, `import server` hangs and kills test runners and ASGI servers. Lazy loading defers this to first request.

## ChromaDB Embedding Function

The embedding callable passed to ChromaDB MUST be a class with `__call__(self, input)` — the parameter name is enforced:

```python
# CORRECT — class with input param
class EmbeddingFn:
    def __init__(self, model):
        self.model = model
    def __call__(self, input):           # MUST be named 'input'
        return self.model.encode(input).tolist()

# WRONG — plain function OR parameter named 'texts'
def embed(texts):  # chromadb rejects this
    return model.encode(texts).tolist()
```

## sentence-transformers Setup

```yaml
# config.yaml
embedding:
  provider: "sentence-transformers"
  model: "all-MiniLM-L6-v2"   # ~90MB, 384-dim, CPU-friendly
  endpoint: ""
```

```txt
# requirements.txt
sentence-transformers==3.3.1
```

No server process needed — the model loads as a Python object.

## Test Isolation for ChromaDB

Chromadb holds SQLite file handles. Reusing the same directory across tests causes `OperationalError: attempt to write a readonly database`. Fix: unique directory per test:

```python
import uuid, shutil, os

@pytest.fixture
def db():
    path = f"./test_chroma_{uuid.uuid4().hex[:8]}"
    os.makedirs(path, exist_ok=True)
    client = chromadb.PersistentClient(path=path)
    yield client
    shutil.rmtree(path, ignore_errors=True)
```

**Diagnosing the same error when tests DON'T use this fixture:** if API tests drive the app's real DB (`LinkDB`/`PersistentClient` against a shared path) instead of the fixture, they fail **only when run together** (`sqlite3.OperationalError: attempt to write a readonly database`) while each **passes in isolation** (`pytest tests/test_api.py::test_x -q`). That fail-together/pass-individually signature IS the shared-sqlite-lock interference — your change didn't cause it. Prove it with a parent-commit A/B (`git checkout HEAD~1 -- <file>` → run → `git checkout HEAD -- <file>`; identical failure set = pre-existing) and report the isolation-pass evidence.

**Test runs mutate tracked artifacts:** ChromaDB suites delete `test_*_db/chroma.sqlite3` and rewrite test-data JSONs (`test_schedules.json`). After any suite run, restore them so the tree stays clean:
```bash
git checkout -- test_*_db test_schedules.json
```
See `agent-workflow-pitfalls` #17/#18 for the full verification-under-approval and pre-existing-failure playbook.

**Even with rmtree + module reload, a FIXED per-suite path still trips the readonly lock.** API suites that drive the app's real DB through `importlib.reload(server)` plus one shared `./test_api_chroma_db` dir (removed/recreated per test) fail with `attempt to write a readonly database` when run together — because the previous test's `PersistentClient` stays alive (cached in `server._db` until the next reload) holding the sqlite file open while the fixture rmtree's it. Signature: fails together / passes individually (order-dependent), reproduces on the pristine parent commit. **Validated fix (rag-assistant, commit 85d0aea): change the fixture to a unique per-test path** — `db_path = f"./test_api_chroma_db_{uuid.uuid4().hex[:8]}"` — and the whole `tests/test_api.py` suite went from 3 failed / 3 passed to **8/8 passed**. The same pattern applies to any fixture that recreates a ChromaDB path per test. Apply the fix rather than reporting the flake; the diagnostic signature above is how you recognize it in other repos.

**Config-override tests need env var set BEFORE `importlib.reload(server)`.** A test that sets `os.environ["RAG_CHROMA_PATH"]` inside the test body but skips the reload silently writes to the stale config path (config is read at import time) — the brief's literal snippet had exactly this bug. Correct sequence: set env vars → `importlib.reload(server)` → exercise endpoints → `try/finally` cleanup (rmtree DB dir, pop env vars). Subtlety that makes this work: reload re-executes in the SAME module dict, so the OLD `app` object the `client` fixture holds keeps working — route handlers' `__globals__` lookups see the new `config`/`_db` after reload. No need to re-import the app.

**Testing LLM-driven chat intents deterministically:** to test a chat endpoint whose flow is LLM-parse → dispatch → network, monkeypatch the lazy accessor instead of the LLM client: `monkeypatch.setattr(server, "_get_parser", lambda: FakeParser())` returning a canned `Command(intent=..., params=...)`, plus `monkeypatch.setattr("dispatcher._fetch_wiki", lambda q: (...))` for the network step. Assert `action`, reply contents, and `urls`. Full recipe in `references/api-endpoint-smoke-test.md`.

## API Key Pattern

Never hardcode API keys. Use env vars, fail explicitly:

```python
def get_api_key() -> str:
    key = os.environ.get("PROVIDER_API_KEY")
    if not key:
        raise RuntimeError("PROVIDER_API_KEY environment variable not set")
    return key
```

Add `.env` to `.gitignore`.

## Project Scaffolding

```
project/
  server.py           # FastAPI app with lazy deps
  config.py           # Config dataclass + load_config + get_api_key
  config.yaml         # User configuration (NO secrets)
  db.py               # ChromaDB adapter
  models.py           # Pydantic request/response models
  static/             # Web UI (if needed)
  requirements.txt    # Pinned versions
  start.sh            # Launch script
  .gitignore          # .venv/, chroma_db/, __pycache__/, .env
```

## Dual-Provider Pattern (LLM + Embeddings)

When using separate providers for LLM and embeddings (e.g., DeepSeek API for chat + sentence-transformers locally), keep config split so each can be swapped independently:

```yaml
# config.yaml
llm:
  provider: "deepseek"        # LLM for intent parsing / summarization
  model: "deepseek-flash"
  endpoint: "https://api.deepseek.com/v1"
  # api_key from env var

embedding:
  provider: "sentence-transformers"  # local embeddings (no API key)
  model: "all-MiniLM-L6-v2"
  endpoint: ""
```

**Pattern:** LLM provider can be switched without affecting embeddings. The `config.py` loads both sections into separate fields. `commands.py` uses `config.llm_*`, `db.py` uses `config.embedding_*`.

## LLM Summarization on Ingestion

When saving content to the vector DB, use the LLM to generate a concise summary for the description field:

```python
def _summarize(content: str, url: str, config: Config) -> str:
    if not content or len(content) < 100:
        return ""  # too short, skip
    try:
        from openai import OpenAI
        client = OpenAI(base_url=config.llm_endpoint, api_key=get_api_key())
        response = client.chat.completions.create(
            model=config.llm_model,
            messages=[{
                "role": "system",
                "content": "Summarize this page in one sentence in Russian."
            }, {
                "role": "user", "content": f"URL: {url}\n\n{content[:3000]}"
            }],
            temperature=0.3, max_tokens=200,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return ""
```

Call in the save flow: `summary = _summarize(content, url, config)` → use as description. Falls back to user-provided description if LLM call fails.

## Quick-Save Bookmarklet Endpoint

Add a `GET /save` endpoint for one-click browser bookmarklets:

```python
@app.get("/save")
async def quick_save(url: str, title: str = "", folder: str = ""):
    from dispatcher import _fetch_page_content, _summarize
    content = _fetch_page_content(url)
    summary = _summarize(content or title, url, config)
    _get_db().add_link(url, summary or title, folder or None, content)
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)
```

Bookmarklet JS:
```
javascript:(function(){location.href='http://localhost:8765/save?url='+encodeURIComponent(location.href)+'&title='+encodeURIComponent(document.title)})()
```

## Pitfalls

- **ChromaDB metadata**: `None` values are rejected — use empty string `""` and normalize on read
- **APScheduler + ChromaDB at import**: BackgroundScheduler in module scope hangs FastAPI startup — put in `@app.on_event("startup")` or lazy function
- **Test sandbox**: `execute_code` sandbox may timeout loading ML models (sentence-transformers ~20-90s). Run heavy tests on host. Use `execute_code` + `subprocess.run([venv_python, ...])` pattern to escape sandbox Python.
- **Numpy + torch compatibility**: sentence-transformers 3.3.1 + torch 2.2.x may need numpy<2. Pin `numpy==1.26.4` if `RuntimeError: numpy is not available`.
- **async fixtures**: pytest-asyncio 0.24+ requires `@pytest_asyncio.fixture` for async fixtures, not `@pytest.fixture`
- **Plan changes mid-execution**: when switching providers or config during subagent-driven development, task briefs become stale. Re-generate task briefs or add explicit context to dispatchers. Reviewers will flag spec-vs-brief conflicts. See `references/provider-switch-mid-project.md` for the full step-by-step recipe.
- **`python server.py` does NOT start the server — no `__main__` block**: task briefs for these apps routinely say `python server.py &`, but `server.py` is a uvicorn target, not a script (importing it just builds the app and exits). Launch via the venv the same way `start.sh` does: `.venv/bin/python -m uvicorn server:app --host 127.0.0.1 --port 8765` (background), then health-check `curl -s http://localhost:8765/api/health` → `{"status":"ok"}` before exercising endpoints. Verify the launch command against `start.sh` before writing integration-test steps into a report.
- **Live-server chat tests depend on the real LLM + network, and degrade silently**: `/api/chat` on a live server calls the actual LLM parser — if the parse throws (no key, API down), `CommandParser.parse` catches and returns `Command(intent="unknown")`, so the response is `action="unknown"` with NO error surfaced. A curl test expecting `action="wiki"` will fail confusingly. Either use the monkeypatch recipe (below) or document the live-LLM dependency explicitly in the report. Same for `_fetch_wiki`: it needs network to ru.wikipedia.org.
- **Venv vs system python**: always use `.venv/bin/python` for tests — system python may lack dependencies. Inside `execute_code`, use `subprocess.run([venv_python, "-m", "pytest", ...])`.
- **Subagent commit denials**: subagents working under approval gates may be denied `git add`/`git commit`. When this happens, the parent commits manually — `git add <file> && git commit -m "..."`. This is not a task failure; the code is on disk, verified by the subagent's test report.
- **New DB class must reuse the lazy-init cache, NOT create fresh instances per request**: when adding a second ChromaDB collection (e.g., PromptDB alongside LinkDB), dispatch handlers that call `PromptDB(config)` on every chat command reload the SentenceTransformer model (~1s+) per request. Fix: add a module-level `_prompt_db = None` + `_get_prompt_db(config)` cache in the dispatcher (or pass the cached instance into `dispatch()` like LinkDB). Same pattern as `_get_db()` in server.py.
- **Recursive network helpers need a depth guard**: if a helper function calls itself on network responses (e.g., 404 → search → retry), add a `_depth=0` parameter and return early before the recursive call when `_depth >= 1`. Without this, a search loop can hit Python's recursion limit (~2000 HTTP calls) before the `except` swallows the `RecursionError`.
- **Git tracks test DB artifacts**: ChromaDB test runs create `chroma.sqlite3` files. Add `chroma_db/` and `test_*_db/` to `.gitignore`. If already committed, use `git rm --cached`.
- **`git add -A` commits .venv and test artifacts to git**: always check `git status` before `git add -A`. Prefer `git add <specific files>`. Ensure `.gitignore` covers `.venv/`, `chroma_db/`, `test_*_db/`, `__pycache__/`, `*.pyc`, and `.env` BEFORE the first commit.
- **Adding a new UI tab**: the vanilla JS web UI follows a consistent pattern (nav button + tab div + 3 JS functions). See `references/adding-ui-tab.md` for the step-by-step recipe.

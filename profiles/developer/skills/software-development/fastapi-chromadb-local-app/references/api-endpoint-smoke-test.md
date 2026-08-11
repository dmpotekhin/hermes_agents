# API Endpoint Smoke Test via httpx ASGITransport (no live server)

Use when: a task brief adds/modifies FastAPI endpoints, the brief's literal
`python -c` import check gets blocked by approval gates, and you want
real end-to-end evidence (request → route → DB → response) without
starting uvicorn. Also works for verifying 404 paths and response models.

This recipe was validated on the rag-assistant project (Task 7: prompt CRUD
endpoints added to server.py). Result: `1 passed, 4 warnings in 14.60s`.

If a brief instead demands a LIVE server + curl (integration test): do not run
`python server.py` — there is no `__main__` block. Launch uvicorn like
`start.sh` does (see SKILL.md pitfalls), and remember live chat endpoints call
the real LLM, degrading to `action="unknown"` silently on failure.

## Recipe

1. Write a throwaway pytest module with `write_file` to `/tmp/` (repo paths
   also accepted, but `/tmp` keeps the tree clean; `rm` may be blocked —
   leave it, `/tmp` is OS-cleared, and say so in the report).
2. **Set env vars BEFORE importing server** — the module-level `config`
   reads `RAG_CHROMA_PATH` / `RAG_OBSIDIAN_PATH` at import time. Point the
   Chroma path at a fresh temp dir so the app's real `chroma_db/` is never
   touched.
3. Use `pytest_asyncio` + `httpx.AsyncClient(transport=ASGITransport(app=app))`
   (no network socket, no server process; `@pytest_asyncio.fixture`, not
   `@pytest.fixture`, for the async client fixture).
4. Exercise every new endpoint including negative paths (delete → 404).

## Known-good template

```python
import os
import sys
import shutil
import uuid

sys.path.insert(0, "/path/to/project")
os.chdir("/path/to/project")
tmp = f"/tmp/api_smoke_{uuid.uuid4().hex}"
os.environ["RAG_CHROMA_PATH"] = tmp
os.environ["RAG_OBSIDIAN_PATH"] = "/tmp"

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from server import app


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_prompt_crud(client):
    r = await client.get("/api/prompts")
    assert r.status_code == 200 and r.json() == []

    r = await client.post("/api/prompts", json={
        "text": "напиши код-ревью", "description": "review",
        "tags": ["python", "review"],
    })
    assert r.status_code == 200
    data = r.json()
    assert data["id"] and data["tags"] == ["python", "review"] and data["created_at"]
    pid = data["id"]

    r = await client.get("/api/prompts")
    assert len(r.json()) == 1 and r.json()[0]["id"] == pid

    r = await client.delete(f"/api/prompts/{pid}")
    assert r.status_code == 200 and r.json() == {"status": "deleted"}

    r = await client.delete(f"/api/prompts/{pid}")   # negative path
    assert r.status_code == 404

    shutil.rmtree(tmp, ignore_errors=True)
```

Run with the venv's canonical pytest binary so the verification tracker
registers it as a passing pytest run:

```bash
cd /path/to/project && .venv/bin/pytest /tmp/test_prompt_endpoints_smoke.py -q
```

## Gotchas

- `importlib.reload(server)` inside a fixture does NOT reliably reset
  ChromaDB state — do NOT use the app's real DB path in the smoke test.
  Always point `RAG_CHROMA_PATH` at a fresh temp dir.
- Lazy-init servers: importing `server` must NOT load sentence-transformers
  (that is the point of lazy `_get_db()`/`_get_prompt_db()`); if the import
  hangs, the module under test has module-level heavy init — fix that first.
- The first request to a lazy DB endpoint loads the embedding model
  (~20-90s), so budget the run accordingly; subsequent tests in the same
  process reuse the cached singleton.
- Cleanup: prefer `shutil.rmtree(tmp)` inside the test; if `rm` of the temp
  test file is blocked afterwards, leave the file — `/tmp` is ephemeral.

## Testing LLM-driven chat intents deterministically (no LLM, no network)

Validated on rag-assistant Task 8 (`test_wiki_via_chat`): the `/api/chat`
flow is LLM-parse → `dispatch` → (network for wiki). To test it through the
API without a real LLM call or live Wikipedia request, monkeypatch the two
boundaries:

1. The lazy parser accessor: `monkeypatch.setattr(server, "_get_parser", lambda: FakeParser())`
   where `FakeParser.parse()` returns a canned `Command(intent="wiki", params={"query": "gRPC"})`.
   Patching the accessor (not the OpenAI client) sidesteps `get_api_key()` too.
2. The network leaf: `monkeypatch.setattr("dispatcher._fetch_wiki", lambda q: (title, extract, url))`.
   Patch the module the dispatcher function actually resolves from — the
   `dispatch` function imported into `server` still reads `_fetch_wiki` from
   `dispatcher`'s globals.

Then assert on the response envelope: `data["action"] == "wiki"`, the reply
contains title + URL, and `data["urls"]` holds the page URL.

```python
@pytest.mark.asyncio
async def test_wiki_via_chat(client, api_context, monkeypatch):
    import server
    from commands import Command

    class FakeParser:
        def parse(self, text):
            return Command(intent="wiki", params={"query": "gRPC"})

    monkeypatch.setattr(server, "_get_parser", lambda: FakeParser())
    monkeypatch.setattr(
        "dispatcher._fetch_wiki",
        lambda query: ("gRPC", "gRPC is a framework.",
                       "https://ru.wikipedia.org/wiki/gRPC"),
    )
    resp = await client.post("/api/chat", json={"text": "что такое gRPC"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == "wiki" and "gRPC" in data["reply"]
    assert "https://ru.wikipedia.org/wiki/gRPC" in data["urls"]
```

Note: if the chat test uses the app's lazy DB (`_get_db()` inside `dispatch`),
pair it with the `api_context` fixture (unique per-test ChromaDB path — see
SKILL.md Test Isolation) so the DB layer is fresh too.

## Config-override tests: env vars must be set BEFORE the reload

`server.py` reads `RAG_CHROMA_PATH`/`RAG_OBSIDIAN_PATH` into the module-level
`config` **at import time**. A test that only does
`os.environ["RAG_CHROMA_PATH"] = ...` inside its body (no reload) silently
writes to the stale config path. Correct in-repo pattern (rag-assistant
`test_prompt_crud`, 8/8 suite green):

```python
os.environ["RAG_CHROMA_PATH"] = "./test_api_prompts_db"
os.environ["RAG_OBSIDIAN_PATH"] = "/tmp"
importlib.reload(server)          # config re-read from env
try:
    ...  # exercise endpoints
finally:
    shutil.rmtree("./test_api_prompts_db", ignore_errors=True)
    os.environ.pop("RAG_CHROMA_PATH", None)
    os.environ.pop("RAG_OBSIDIAN_PATH", None)
```

Why the OLD app object still works after reload: `importlib.reload` re-executes
the module in the SAME `sys.modules` dict, so the `app` instance the client
fixture imported earlier still routes to handler functions whose
`__globals__` (the updated module dict) now resolve `config`/`_db` to the new
values. No need to re-import `app`.

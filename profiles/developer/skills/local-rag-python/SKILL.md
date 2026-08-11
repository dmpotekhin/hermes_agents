---
name: local-rag-python
description: Build local RAG applications in Python — ChromaDB + sentence-transformers + FastAPI. Use when the user wants to build a knowledge base, link manager, document search, or any local vector-search app on macOS/Linux.
---

# Local RAG in Python

End-to-end pattern for building a local RAG (Retrieval-Augmented Generation) system in Python with zero external services.

## When to Use

- Building a personal knowledge base or link manager
- Adding semantic search to an existing Python app
- Replacing cloud vector DBs (Pinecone, Weaviate) with a local alternative
- Any app that needs to "search by meaning" over documents, links, or notes

## Stack (recommended defaults)

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Vector DB | ChromaDB | Python-native, file-based, no server |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) | Local, no API calls, 384-dim, ~90MB |
| LLM (optional) | DeepSeek / OpenAI-compatible API | For intent parsing, summarization |
| Server | FastAPI + uvicorn | Async, static files, easy endpoints |
| Scheduler | APScheduler | In-process cron |

## Setup Steps

### 1. Dependencies

```
chromadb>=0.5.0
sentence-transformers>=3.0
fastapi>=0.115
uvicorn[standard]
```

### 2. Embedding Function for ChromaDB

Critical: ChromaDB inspects the embedding function signature. The callable must accept a parameter named `input` (not `texts`, not `documents`):

```python
from sentence_transformers import SentenceTransformer

class EmbeddingFn:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def __call__(self, input):   # MUST be named "input" for ChromaDB
        return self.model.encode(input).tolist()
```

Pitfall: a plain function `def embed(texts)` will fail with `TypeError` because chromadb calls it with `input=` keyword.

### 3. numpy Version Conflict

`sentence-transformers` pulls `torch` which may conflict with newer numpy. If you get `A module that was compiled using NumPy 1.x cannot be run in NumPy 2.x`:

```bash
pip install numpy==1.26.4
```

This is compatible with chromadb, scipy, scikit-learn, and torch.

### 4. Lazy Initialization in FastAPI

ML models load ~90MB and take 20-40 seconds on first import. To keep server startup fast and tests running:

```python
_db = None

def _get_db():
    global _db
    if _db is None:
        from db import LinkDB
        _db = LinkDB(config)
    return _db

# In route handlers: db = _get_db()
```

This pattern:
- Keeps module imports instant (no ML at import time)
- Allows tests to import server without loading ChromaDB
- First request triggers one-time load, subsequent requests instant

### 5. Testing with ChromaDB

Tests that create ChromaDB collections must use unique paths per test or module-scoped fixtures. Reusing a single path causes `sqlite3 operationalerror`.

```python
import tempfile, shutil

@pytest.fixture(scope="module")
def db():
    path = tempfile.mkdtemp()
    db = LinkDB(config_with_path(path))
    yield db
    shutil.rmtree(path)
```

### 6. Bookmarklet Pattern for Browser Integration

One-click "save current page" from browser:

```python
@app.get("/save")
async def quick_save(url: str, title: str = ""):
    # save to DB...
    return RedirectResponse(url="/", status_code=303)
```

Bookmarklet (paste as browser bookmark URL):
```
javascript:(function(){location.href='http://localhost:8765/save?url='+encodeURIComponent(location.href)+'&title='+encodeURIComponent(document.title)})()
```

No CORS — navigates current tab to localhost.

## Common Pitfalls

1. **Embedding function param name** — must be `input`, not `texts`
2. **numpy 2.x incompatibility** — downgrade to 1.26.4
3. **ChromaDB rejects None metadata** — store empty string, normalize on read
4. **First model load hangs tests** — use lazy init + module-scoped fixtures
5. **Duplicate URL handling** — check `collection.get(where={"url": url})` before adding
6. **Dispatcher recreates DB per request** — if a DB class is used in a chat dispatcher AND REST endpoints, cache it in BOTH places. See `references/dispatcher-caching-pitfall.md`.
7. **Wikipedia OpenSearch recursion** — `_fetch_wiki` fallback retries can recurse unboundedly. Always add a depth guard. See `references/wikipedia-recursion-pitfall.md`.
8. **Static file caching in FastAPI** — when updating HTML/JS served via `StaticFiles`, the browser may serve a cached copy. `sendChat is not defined` on a new function means the old JS is cached. Fix: add a version query string to the script tag (e.g., `<script src="app.js?v=2">`). Hard-refresh (Cmd+Shift+R) also works during development.
9. **DeepSeek model name silently changes** — the DeepSeek API may rename models (e.g., `deepseek-flash` → `deepseek-v4-flash`) and return 400 Bad Request. If your parser swallows exceptions without logging, the symptom is every command returning "unknown" with no visible error. Always check server logs when an LLM parser suddenly stops working. The exact model names are in the API error message body. See `references/deepseek-model-rename.md`.
10. **LLM parser swallows exceptions** — `try: ... except Exception: return Command(intent="unknown")` hides API errors, JSON parse failures, and auth problems. Always log the traceback before falling back to unknown. See `references/deepseek-model-rename.md` for the exact pattern.
11. **Web Speech API for voice input** — browser-native speech-to-text (`SpeechRecognition` / `webkitSpeechRecognition`, `lang='ru-RU'`) with zero dependencies. Lazy-init on first mic click, auto-send after recognition. See `references/web-speech-api.md`.

## LLM Summarization on Ingestion

When saving content, use an LLM to generate a concise description for the metadata:

```python
def _summarize(content: str, url: str, config) -> str:
    if not content or len(content) < 100:
        return ""
    try:
        from openai import OpenAI
        from config import get_api_key
        client = OpenAI(base_url=config.llm_endpoint, api_key=get_api_key())
        resp = client.chat.completions.create(
            model=config.llm_model,
            messages=[{
                "role": "system",
                "content": "Summarize this page in one sentence."
            }, {"role": "user", "content": f"URL: {url}\n\n{content[:3000]}"}],
            temperature=0.3, max_tokens=200,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return ""
```

Call in the save flow: `summary = _summarize(content, url, config)` → use as description. Falls back to user text if LLM fails.

## Related Patterns

For more detailed production patterns (dual-provider LLM+embeddings config, APScheduler integration, `.env` API key handling, full API endpoint design, test isolation with unique ChromaDB paths per test), see the `fastapi-chromadb-local-app` skill — it covers the complete scaffolding.

- `references/wikipedia-agent.md` — Wikipedia REST API with OpenSearch fallback, integrated into RAG chat pipeline
- `references/wikipedia-recursion-pitfall.md` — Unbounded recursion in OpenSearch fallback; always add depth guard
- `references/second-collection.md` — Adding a second ChromaDB collection (e.g., prompts) alongside an existing links collection
- `references/dispatcher-caching-pitfall.md` — DB class recreated per request in dispatcher path; cache everywhere
- `references/deepseek-model-rename.md` — DeepSeek silently renamed models; how to detect and fix
- `references/web-speech-api.md` — Browser-native voice input via Web Speech API

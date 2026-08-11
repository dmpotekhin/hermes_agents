# Dispatcher Caching Pitfall

## The Problem

When adding a second ChromaDB collection (e.g., PromptDB alongside LinkDB), the lazy-init pattern is typically applied only in `server.py` for REST endpoints:

```python
# server.py — works for route handlers
_prompt_db = None
def _get_prompt_db():
    global _prompt_db
    if _prompt_db is None:
        _prompt_db = PromptDB(config)
    return _prompt_db
```

But if the same DB class is used in a **dispatcher function** (chat pipeline), it gets recreated on every request:

```python
# dispatcher.py — BUG: new PromptDB per chat command
elif intent == "save_prompt":
    prompt_db = PromptDB(config)  # loads SentenceTransformer (~90MB) every time!
    pid = prompt_db.add_prompt(...)
```

Each `PromptDB(config)` call loads the SentenceTransformer model from disk AND opens a new ChromaDB PersistentClient. Cost: ~1s+ per chat command, plus concurrent-request SQLite risks.

This was caught during code review of the RAG Assistant (2026-08-10).

## The Fix

Cache at the module level in the dispatcher too — same pattern as server.py:

```python
# dispatcher.py
_prompt_db = None

def _get_prompt_db(config):
    global _prompt_db
    if _prompt_db is None:
        _prompt_db = PromptDB(config)
    return _prompt_db

# In dispatch handlers:
prompt_db = _get_prompt_db(config)
```

Or pass the cached instance from server.py into dispatch() as a parameter (like LinkDB is already passed).

## Rule of Thumb

**Every code path that constructs a DB class with an ML model must cache it.** The "Lazy Init in FastAPI" pattern from SKILL.md applies to ALL consumers — route handlers, dispatchers, background tasks — not just the first one you write.

# Wikipedia Agent: Recursion Pitfall

## The Problem

The OpenSearch fallback in `_fetch_wiki` calls itself recursively. If opensearch returns a title that also produces a 404 on the summary endpoint, the function recurses to Python's recursion limit — up to ~2000 HTTP calls before crashing.

This was caught during code review of the RAG Assistant (2026-08-10).

## The Fix

Add a depth parameter with a guard at the recursion entry point:

```python
def _fetch_wiki(query: str, lang: str = "ru", _depth: int = 0) -> tuple[str, str, str]:
    # ...
    if resp.status_code == 404:
        if _depth >= 1:          # max 1 hop: search → retry → stop
            return ("", "", "")
        # ... opensearch ...
        return _fetch_wiki(data[1][0], lang, _depth=_depth + 1)
```

One hop is sufficient: the OpenSearch API almost always returns a valid title on the first attempt. If the retry also fails, something is fundamentally wrong (network, API change) and stopping is the right behavior.

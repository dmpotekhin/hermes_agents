# Wikipedia Search Agent for RAG Apps

Reusable pattern for adding Wikipedia lookup to a FastAPI RAG chat endpoint.

## API Pattern

Use Wikipedia REST API (`/api/rest_v1/page/summary/{title}`) with OpenSearch fallback:

```python
import httpx
import urllib.parse

def _fetch_wiki(query: str, lang: str = "ru") -> tuple[str, str, str]:
    """Returns (title, extract, page_url). Empty strings on failure."""
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{encoded}"
        resp = httpx.get(url, timeout=5, headers={
            "User-Agent": "RAG-Assistant/1.0 (your-email@example.com)"
        })
        if resp.status_code == 404:
            # Fallback: OpenSearch → first result → retry
            search_url = f"https://{lang}.wikipedia.org/w/api.php?action=opensearch&search={encoded}&limit=1&format=json"
            search_resp = httpx.get(search_url, timeout=5)
            if search_resp.status_code == 200:
                data = search_resp.json()
                if len(data) >= 2 and len(data[1]) > 0:
                    return _fetch_wiki(data[1][0], lang)
            return ("", "", "")
        resp.raise_for_status()
        data = resp.json()
        return (
            data.get("title", query),
            data.get("extract", ""),
            data.get("content_urls", {}).get("desktop", {}).get("page", ""),
        )
    except Exception:
        return ("", "", "")
```

## Integration into Chat Pipeline

Add a `wiki` intent to the command parser, then handle in dispatcher:

```python
elif intent == "wiki":
    query = params.get("query", "")
    if not query.strip():
        return ChatResponse(reply="Уточни, что найти в Wikipedia", action="wiki")
    title, extract, page_url = _fetch_wiki(query)
    if not extract:
        return ChatResponse(
            reply=f"«{query}» не найдено в Wikipedia.",
            action="wiki",
        )
    return ChatResponse(
        reply=f"**{title}**\n{extract[:800]}\n\n{page_url}",
        action="wiki",
        urls=[page_url],
    )
```

## Key Decisions

- **Timeout**: 5 seconds — Wikipedia is fast but not instant
- **Language**: Configurable via `lang` parameter (default `"ru"`)
- **Extract truncation**: 800 chars — fits in a chat response without overwhelming
- **Fallback**: OpenSearch on 404 handles typos and alternative titles
- **Recursive retry**: First OpenSearch hit is re-fetched via the same function
- **Error return**: Empty tuple on any exception — caller handles gracefully

## Testing

Mock `httpx.get` with `unittest.mock.patch`:

```python
from unittest.mock import patch, MagicMock

def test_fetch_wiki_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "title": "gRPC",
        "extract": "gRPC is a cross-platform open source RPC framework.",
        "content_urls": {"desktop": {"page": "https://ru.wikipedia.org/wiki/gRPC"}},
    }
    with patch("dispatcher.httpx.get", return_value=mock_response):
        title, extract, url = _fetch_wiki("gRPC")
        assert title == "gRPC"
        assert "RPC" in extract
```

Also test: 404 → search fallback, timeout → empty tuple, empty query → graceful.

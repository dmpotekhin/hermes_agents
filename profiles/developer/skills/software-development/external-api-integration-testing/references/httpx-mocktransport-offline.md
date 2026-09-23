# Offline HTTP testing with `httpx.MockTransport` — worked example

Case: a source-resolver layer that fetches a web article (HTML) plus GitHub REST and
GraphQL endpoints, then turns them into a structured `SourceContext`. The whole resolver
suite (68 tests) must run with no network so CI and offline sessions behave the same.

## Shape of the code under test

```python
class BaseSourceResolver(ABC):
    def __init__(self, *, client: httpx.AsyncClient | None = None):
        self._client = client
        self._owns_client = client is None

    async def aclose(self) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
```

Dependency injection is what makes the test cheap: the resolver never constructs its own
transport when one is handed in, and it never closes a client it did not create (closing an
injected client breaks the next test with "client has been closed").

## The transport handler

```python
def make_handler(calls: list[tuple[str, str]]):
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, request.url.path))
        key = (request.method, request.url.path)
        if key == ("GET", "/repos/acme/tool"):
            return httpx.Response(200, json=REPO_PAYLOAD, request=request)
        if key == ("GET", "/repos/acme/tool/issues/7"):
            return httpx.Response(200, json=ISSUE_PAYLOAD, request=request)
        if key == ("POST", "/graphql"):
            assert "Authorization" in request.headers          # token really sent
            return httpx.Response(200, json={"data": GRAPHQL_DATA}, request=request)
        return httpx.Response(404, json={"message": "Not Found"}, request=request)
    return handler


def client_for(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler),
                            base_url="https://api.github.com")
```

Notes that matter:

- `httpx.Response(..., request=request)` — pass the request through, or `raise_for_status()`
  and relative-URL handling behave differently from production.
- Keep the recording list (`calls`) when a test must prove *what was requested* (e.g. the
  resolver did not silently fall back to a second endpoint).
- Trim real payloads but keep the fields the parser reads **and** the surrounding noise
  (extra keys, `null`s) — the double must not be cleaner than the provider.
- Assert the auth header on the authenticated branch; a resolver that forgets the token
  otherwise passes green and 401s in production.

## Hermetic tests that are worth writing

1. Happy path per source type (repo / issue / PR / release / discussion) — assert the parsed
   fields and the resulting `confidence`.
2. **Missing token path**: GraphQL discussion without a token → warning recorded, confidence 0,
   no fabricated text (`sources/mock.py` returns an empty context *with* a warning — "honest by
   construction").
3. **404 / unreadable source** → `SourceResolutionError` propagates and the caller marks the job
   FAILED; never let a failure turn into empty-but-successful content.
4. **Metrics only from the API body** — a test that removes a metric from the payload and asserts
   the output has none.
5. Non-ASCII content (Cyrillic article) through the HTML path, to catch encoding assumptions.

Pure parsing of local HTML uses the same idea with no HTTP at all: feed the stdlib
`HTMLParser` subclass a string and assert the extracted headings/quotes/code/canonical URL.

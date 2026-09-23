---
name: external-api-integration-testing
description: Use when stubbing HTTP APIs to mirror the real response.
---

# External API Integration Testing

## Goal

When your code calls an external HTTP provider (Telegram Bot API, Facebook Graph, OpenAI-compatible endpoints, Maps, etc.), the #1 reason a **unit test passes while production crashes** is that the *test double models the response shape too generously*. Fakes must mirror the REAL provider payload — not the happy path you assumed.

## Core principle: fake/mock to the REAL response shape

- Read the provider's actual response schema, not the shape you guessed.
- If one endpoint returns different shapes depending on the call (single object vs list), make the fake **configurable** (`result=` arg) and test BOTH.
- Assert on the field your code actually consumes (e.g. `external_id`), not just "a request was sent".
- A green suite that never exercises the real response shape is a false sense of safety.

## Pitfall: array-vs-object responses

Many APIs return a single object for one action and a LIST for a batch:

- Telegram `sendMessage` / `sendPhoto` -> `{"result": {"message_id": N}}` (object)
- Telegram `sendMediaGroup` -> `{"result": [Message, Message, ...]}` (**array**)
- If code does `msg = resp.json()["result"]` then `msg.get("message_id", "")` and `result` is a list -> `AttributeError: 'list' object has no attribute 'get'` — *after* the request already succeeded in prod. The post goes out, then the app crashes.

Normalize both shapes before reading a field:
```python
res = r.json().get("result", {})
if isinstance(res, list):          # batch endpoint (e.g. sendMediaGroup)
    first = res[0] if res else {}
else:                              # single-object endpoint
    first = res if isinstance(res, dict) else {}
external_id = str(first.get("message_id", ""))
```

## When a reviewer (or a missed bug) surfaces

A reviewer working from **manual trace — even without running tests** — can catch bugs your green suite missed. Root cause is usually the same: the double returns an over-simple shape. Fix all three together, then re-run the full suite:

1. **Code**: normalize the response shape (handle object AND list).
2. **Double**: make the fake return the REAL shape (configurable result arg), and give it a realistic value (e.g. the batch returns a list of dicts).
3. **Test**: assert on the consumed field (e.g. `external_id == "7"` taken from `result[0]`), and add a regression test that exercises the failing band (not just a trivially-short happy path).

## Offline HTTP: `httpx.MockTransport` + an injected client

For an `httpx`-based client, the cheapest way to get a realistic double is to keep the real
client and swap only the transport — response shapes, status codes and headers all stay
real, nothing touches the network:

```python
def handler(request: httpx.Request) -> httpx.Response:
    key = (request.method, request.url.path)
    if key == ("GET", "/repos/acme/tool/issues/7"):
        assert request.headers["Authorization"] == "Bearer test-token"   # assert what prod sends
        return httpx.Response(200, json=ISSUE_PAYLOAD, request=request)
    if key == ("POST", "/graphql"):
        return httpx.Response(200, json={"data": {"repository": {"discussion": DISCOURSE}}}, request=request)
    return httpx.Response(404, json={"message": "Not Found"}, request=request)   # real 404 body

client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://api.github.com")
resolver = GitHubResolver(client=client)        # DI: the resolver uses the client it is given
```

Rules that make this pay off:

- **Make the client injectable** (`client: httpx.AsyncClient | None = None`) and only build your
own inside the resolver when none was passed; the resolver must close only a client it created.
- Drive one handler per test from **real captured payloads** (trimmed), and include a `404`/`403`
  branch — the error path is where invented content sneaks in.
- Cover the auth-missing path explicitly: no token → warning + `confidence 0`, not a guess.
- Keep the whole suite hermetic: no network, no sleeps, deterministic bytes. Three resolver
  modules (URL/HTML, GitHub REST, GitHub GraphQL) with 68 tests ran in ~1s this way.

See `references/httpx-mocktransport-offline.md` for the worked resolver example.

## When the code grows, the double must grow

A stub client is written against the calls the code made WHEN THE STUB WAS WRITTEN. Add one new call
and a whole shard goes red with errors that look like code bugs:

- **Stub without the method**: the project's `conftest.py` replaces `httpx.AsyncClient` with a minimal
  stub exposing only what the old code used. New code that calls `await client.aclose()` raises
  `AttributeError` in every test that reaches the new path. Fix on the CODE side by guarding optional
  client methods — `aclose = getattr(client, "aclose", None); if aclose and client_is_ours: await aclose()` —
  so an injected/stub client stays valid; extend the stub only for methods the code cannot guard.
- **Make the double the no-network enforcement.** A stub that has no transport at all is a feature:
  the suite proves "no test touches the network" by passing with it in place. Keep it, don't upgrade
  it to a real client.
- **Async tests without `pytest-asyncio` installed**: add a `pytest_pyfunc_call` hook to
  `conftest.py` that drives coroutine test functions with `asyncio.run` (check `inspect.iscoroutinefunction`
  on `pytest_pyfunc_call`'s function arg). Write tests as plain `async def test_...`; do not add the
  plugin just to run them, and do not convert them to sync wrappers around `asyncio.run` in each test.
- **A red shard after wiring new deps is a triage exercise, not a bulk edit.** Read each failure and
  decide code-vs-expectation: a limit that is never reached because the code clamps with `max(5, n)`,
  a result object missing an attribute the caller reads, a scheduler that recorded real `now()` instead
  of the injected moment, an expectation you wrote from the wrong provider shape. Fix code where the
  code is wrong and the test where YOUR expectation was wrong — never blanket-adjust one side.

## Rules

- Never make a fake return a shape the real provider never returns.
- Default a fake to the most common shape, but let the test override it for the batch/edge case.
- Re-run the real suite after each fix; verify no regressions.
- Capture the concrete provider quirk in `references/` so the next session doesn't re-derive it.

See `references/telegram-media-group-array.md` for the worked case (the exact bug, the realistic double, and the failing-band regression test).

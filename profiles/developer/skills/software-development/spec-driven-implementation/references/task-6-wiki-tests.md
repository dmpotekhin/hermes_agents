# Task 6 — RAG-assistant wiki tests: the brief's test code hit the live network

Wiki-fetch handler test task (`tests/test_wiki.py` for `dispatcher._fetch_wiki`). The brief handed
over a 4-test file with mocked `httpx` — except ONE test silently made a real network call.

## The bug in the brief's TEST code (not its implementation code)

The brief's `test_fetch_wiki_empty_query` called `_fetch_wiki("")` with **no `patch`**:

```python
def test_fetch_wiki_empty_query():
    title, extract, url = _fetch_wiki("")   # real HTTP to ru.wikipedia.org!
    assert isinstance(title, str)
    ...
```

Consequences:
- Every run hits `https://ru.wikipedia.org/api/rest_v1/page/summary/` live — nondeterministic,
  network-dependent, up to 5s of timeout latency, flaky offline (though the handler's
  `except Exception → ("", "", "")` mask means it usually still passes — which is exactly why it's
  a trap: green-but-slow and green-by-luck look identical in CI).
- The brief's own Interfaces section said "test coverage for wiki fetch (**mocked httpx**)" — so the
  literal code contradicted the brief's declared intent.

## The fix (a deliberate, report-worthy deviation)

Patch the empty-query call the same way as the sibling tests — `patch("dispatcher.httpx.get",
return_value=mock)` with a 200/empty-shaped response — keep the three `isinstance` assertions
byte-identical, note the deviation in the task report. The mock is an *alignment* with the brief's
declared mocking intent, not a contradiction of it.

Wider rule: **briefs' test code is as untrustworthy as briefs' implementation code.** Grep the
brief's tests for un-patched network/IO calls before transcribing verbatim. Any test that would
touch the network, filesystem, clock, or an env-var-dependent service should be deterministic.

## Rest of the task went by the book

- `test_fetch_wiki_success` — 200 summary → title/extract/url (single mock).
- `test_fetch_wiki_not_found_with_search` — 404 → opensearch → recursive `_fetch_wiki(first_hit)`:
  three-mock `side_effect=[not_found, search_result, search_mock]`; the recursion consumes the
  third mock — an easy spot to get the side_effect length wrong.
- `test_fetch_wiki_timeout` — `side_effect=httpx.TimeoutException(...)` → `("", "", "")`.
- Result: 4 passed in ~1.5s, deterministic.
- Full suite was red on pre-existing `test_scheduler.py` apscheduler errors — proven pre-existing
  via the stash-A/B and artifact-restore procedure (see `agent-workflow-pitfalls` #18), restored
  `test_*_db/*.sqlite3` + `test_schedules.json` churn, committed only `tests/test_wiki.py`
  (`git add <file>`, never `-A`).
- The `_fetch_wiki` shape itself (REST summary + opensearch fallback + recursive retry + empty
  tuple on any exception) is the reusable wiki-lookup pattern already noted in
  `agent-workflow-pitfalls` #17.

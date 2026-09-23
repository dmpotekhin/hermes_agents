# P8–P11 session lessons (publishers / scheduler / dashboard / tests)

Hard-won bugs and the fixes that got P8–P11 green (`pytest tests/` → 31 passed in
~59s, including the `test_e2e_pipeline.py` scan→publish run).

## 1. Async/sync override-consistency bug (base `async` contract broken by a sync subclass)

- `modules/publishers/base.py` declares `async def publish(draft, media_paths) -> PublishResult`.
- `modules/publishers/mock.py` (the dry_run/mock publisher) was implemented as a plain
  (sync) `def publish`. The service then did `await publisher.publish(...)` on it.
- Symptom: `test_auto...` *passed* (the sync mock returned a value that `await` silently
  treated as a non-awaitable coroutine object was NOT the case — actually `await` on a
  non-awaitable raises) — in practice the auto test passed and `test_manual_platform`
  FAILED with `AttributeError`; isolated single-test runs even HUNG (exit 124).

  **Root cause:** the base contract is `async`, the Mock override must be `async` too.
  The first "fix" (removing `await` from the service) was WRONG — it broke the real
  (async) manual publishers. The correct fix: make `MockPublisher.publish` `async def`,
  and KEEP `await publisher.publish(...)` in the service. One async interface for
  auto / mock / manual.

  **Lesson:** when a base ABC declares `async def`, EVERY override must be `async def`.
  A sync override silently produces an `await` on a non-coroutine (or a value used as a
  coroutine) that breaks depending on which subclass the registry returns. Always match
  the abstract signature exactly.

## 2. pytest verbose-async + Loguru output → piping stalls, single tests hang

- Loguru (daily rotation, correlation ids) + `asyncio_mode=auto` makes pytest output
  huge. Piping pytest output through `grep`/`tail` can STALL (blocked pipe), and running
  a single test in isolation can HANG (exit 124 from the terminal watchdog).
- **Fix (reliable):** run the WHOLE file/suite with output redirected to a file, not a pipe:
  `cd ~/projects/travel-blog-app && .venv/bin/python -m pytest tests/ -p no:cacheprovider > /tmp/x.log 2>&1; echo EXIT=$?; tail -c 900 /tmp/x.log`
  Then read the log with the file tools. Don't pipe deep/verbose async output through
  grep; don't trust single-test runs — the full batch is what actually passes.

## 3. Enum value mismatches (AssertionError/AttributeError at test time)

Hard-coded status values in tests/heuristics must match the actual enums — always grep
the enum definition before asserting a member:

- `CityStatus` has NO `SCANNED`. The scanner writes `CityStatus.QUEUED`.
  Members: `QUEUED, PROCESSING, DRAFTED, APPROVED, PUBLISHING, PUBLISHED, ERROR`.
- `DraftStatus` has NO `ERROR`. Members: `PENDING, APPROVED, REJECTED, PUBLISHED`.
  To represent an error-producing draft, rely on a FAILED `Publication` instead.
- `ScanStatus` uses `"scanned"` (NOT `"complete"`).
- `Platform` is `"vk"` (NOT `"vkontakte"`).
- Symptom: `AttributeError: type object 'CityStatus' has no attribute 'SCANNED'`
  (or DraftStatus.ERROR / ScanStatus "complete"). Fix the test to a real member.

## 4. Publication UPSERT semantics (scheduler pre-creates a row)

- `save_published` is idempotent via `UNIQUE(city_id, platform)` but RETURNS the
  existing row and DOES NOT update it. So when the scheduler PRE-CREATES a `scheduled`
  Publication and the publisher later succeeds, the row was never promoted to
  `published` — a silent no-op.
- **Fix:** the publisher service UPDATES the existing (city, platform) row instead of
  short-circuiting on a match (upsert through `update_publication`). Keep the
  `get_due_publications` / `get_publications_by_status` DB helpers the scheduler needs.
- **Lesson:** before relying on an idempotent insert to "just work", check whether it
  updates an existing unique row or only returns it. For a state machine that advances a
  pre-created row, you need real upsert semantics.

## 5. aiosqlite + Streamlit: fresh connection per rerun

- aiosqlite binds its connection to the event loop that created it. Caching a Database
  handle across Streamlit reruns (different loops) breaks it.
- **Fix:** in `ui/dashboard.py`, open a FRESH connection inside a single
  `asyncio.run(_collect())` per rerun and close it — never cache the aiosqlite
  connection across loops. Read-only dashboard, low frequency → fine.

## P12 runtime entrypoints — now built (ADR-101)

`app.py` (FastAPI admin API :8000) and `cli.py` (via `./run.sh --cli <cmd>`) now exist and
wired their config through a single `load_config_file()`-based entrypoint (`_load_config`).
See `references/adr-101-105-publish-hardening.md`. If the venv still lacks `fastapi` at
runtime, install it (background) before wiring P12 — treat that as an env check, not a
constraint.

# ADR-101..105 (P12) — publish-path hardening + cleanup-pass lessons

Closed the platform-reality gaps with a review-driven cleanup cycle. Baseline after
ADR-101..105 was **80 passed**; the simplify-code + code-review pass took it to **81**.
These are the durable, non-obvious gotchas that surfaced.

## The review-driven cleanup cycle (generic)

Feature-sized diff → dispatch **4 parallel simplify-code reviewers** (reuse / quality /
efficiency / altitude) → they return findings in `file:line → problem → cost → fix |
confidence | risk: SAFE/CAREFUL/RISKY` → consume as: **SAFE/CAREFUL = apply with a test
run after each file; RISKY = flag for the user, don't auto-apply** (parallelism in the
publish loop, a stringly-typed → enum migration, changing generation semantics are all
RISKY). Then run **requesting-code-review** (one read-only reviewer over the whole
diff) BEFORE merging. Then full suite + credential-scan + commit.

## Chesterton's fence applies to TESTS too, not just code

When a reviewer flags a `_load_config`/helper-wrapping function as a "duplicate dead
wrapper", check whether a test **monkeypatches the deferred import inside it** before
deleting. In this repo `test_config_entrypoints.py` patches `core.config.load_config_file`
and relies on `_load_config` doing `from core.config import load_config_file` inside the
body (lazy/deferred import re-reads the patched module attr at call time). Moving the
call to a top-level `from core.config import load_config_file` would FROZE the binding at
import and break the guard. Verdict: the wrapper is an intentional test boundary — keep
it, don't chase the duplication. `push back on the reviewer with reasoning` is the right
move here, not the removal.

## F9 `getattr(r, 'success')` lives in MORE than one place

`app.py` (publish-due) was fixed to filter `PublicationStatus.PUBLISHED`, but **the same
bug stayed in `cli.py`'s `publish` command**. `getattr(r, 'success', False)` on a
`Publication`/`PublishResult`-like object is always empty → the published list was always
`[]`. **Lesson: when you fix an identical misused-attr bug pattern in one entrypoint,
grep the sibling entrypoints for the same literal before committing.** Both are now
`r.status == m.PublicationStatus.PUBLISHED` (enum compare, not the string `"published"`).

## Publishers / media / degraded

- **Telegram `sendMediaGroup` silently dropped the caption** — the album went out with
  NO text, the exact "silent drop" ADR-104 exists to prevent. Fix: put the caption on the
  first media item (`media_items[0]["caption"] = ...`). Always regression-test this.
- **Per-branch limits:** media-branch caption limit = `CAPTION_LIMIT` (1024 for TG),
  text-only `sendMessage` limit = `TEXT_LIMIT` (4096). Compute degradation per branch,
  not from the media limit alone — otherwise a long text-only post is falsely flagged
  `degraded`. Use class constants once, not the literal repeated in the slice.
- **`PublishResult.degraded_reason: str = ""`** — the `plan_media` `_note` was thrown away
  by both publishers; the service logged `result.error or result.status_hint`, which for a
  successful degraded post was the dead `"published"` → `"degraded ... : published"`. Add a
  reason field, thread `_note` from the publisher into the result, log `result.degraded_reason
  or result.error or result.status_hint`.
- `_platform_enabled` must **not fail-open** (`except: return True`). Log the exception and
  fall back to the literal `publishing.<platform>` flag so a config/import break is never
  treated as "platform is enabled" (which would auto-publish against a broken config).

## State machine / DB

- **`_PUBLICATION_TRANSITIONS` and `claim_publication` are TWO authorities on legality.**
  `claim_publication`'s CAS does `UPDATE ... SET status=processing WHERE status IN
  ('scheduled','pending')`, but the table only allowed `PENDING→PROCESSING` — so
  `SCHEDULED→PROCESSING` was happening at runtime while the machine denied it. Keep them
  in sync: `SCHEDULED: {PROCESSING, PUBLISHED, FAILED}`.
- **`update_publication_status` was a redundant wrapper** — it did its own `get_published`
  + `check_transition`, then delegated to `update_publication`, which does BOTH again.
  Every status write did 2 SELECTs + 2 machine checks. Delegate straight through
  (`return await self.update_publication(publication_id, status=status)`) — `update_publication`
  already raises `NotFoundError` + runs `check_transition`.

## Full-suite hygiene

- After every cleanup file, run the WHOLE suite, not just the touched test file:
  `cd ~/projects/travel-blog-app && .venv/bin/python -m pytest -q` (fast; the async suite
  can hang when piped through grep — redirect to a file instead).
- `git add -A && python3 ~/.hermes/profiles/developer/tools/scan_credentials.py --staged`
  before EVERY commit (must be silent/exit 0). Security spot-check on the staged diff:
  `grep -nE "BEGIN (RSA|OPENSSH|PRIVATE)|sk-|password=|eval\\(|exec\\("` — `self.secrets.*`
  accesses are FINE (values come from `.env`), not hardcoded secrets.

# Task 5 Review: dispatcher.py handlers (RAG-assistant)

Review session (delegated subagent): read brief + implementer's report + diff (`1ea73a9..2440959`),
verify against live code, deliver spec-compliance verdict. Commit: `2440959 feat(dispatcher): add
save_prompt, search_prompts, wiki handlers` (+75/-1, dispatcher.py only).

## Verdict format that worked

Begin with the verdict line (`SPEC-COMPLIANT (4/4 constraints met)`), then:
1. Per-constraint compliance checked against LIVE source (not just diff) — cite the exact
   signature/line in the dependency module (`db.py:154` add_prompt, `db.py:170` search).
2. Quality findings (minor/non-blocking), each with severity + recommendation.
3. Verification performed (what was actually run).
4. Recommendation (approve; optional follow-ups).

## Concrete checks that found real things

- **Format-join safety check** — handler did `", ".join(r["tags"])`. Correct ONLY if the DB's
  result formatter parses the stored comma-joined `tags` string back into a list. Read
  `_make_item` (db.py:203-210): `[t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []`
  → list, join is safe. If the producer returned the raw string, `join` would char-split it.
  This is the review-side twin of the implementer-side "verify every dependency's actual signatures".
- **Report-vs-reality via git state** — report claimed the `_fetch_wiki` smoke test was "temporary,
  removed after", but `git status --short` showed `?? tests/test_wiki.py` (4 real mocked tests,
  incl. 404→opensearch fallback) still untracked, and `git log --follow` showed it was never
  committed. Finding: commit it (recommended) or delete it so the report matches reality. Also
  `git diff <base> <head> --stat` confirmed the +75/-1 scope claim.
- **No committed test coverage for new dispatch branches** — `git ls-files tests/` showed
  test_dispatcher.py unmodified; only the untracked _fetch_wiki tests existed. Flag as quality gap.
- **Re-ran tests independently** — `.venv/bin/python -m pytest tests/test_wiki.py tests/test_dispatcher.py`
  → 8 passed. Brief's `python -c` line fails (`python` not on PATH); `.venv/bin/python` works.
  Report's "4 passed" claim was for test_dispatcher.py only — independent run gave the fuller picture.
- **Signature verification against live source** — `PromptDB(config)` ctor takes config; `add_prompt(text,
  description, tags)` and `search(query, n_results=5)` match call sites exactly; `ChatResponse` has
  reply/action/urls fields; `_make_item` returns `id/text/description/tags/created_at` keys the
  handler reads. No drift.
- **Pre-existing-failure triage** — report claimed `test_api.py` readonly-ChromaDB and
  `test_scheduler.py` shutdown errors pre-existed; independently confirmed the tracked test-artifact
  dirtiness (`D test_api_chroma_db/chroma.sqlite3` etc. in git status) matches the report's concern #2.

## Findings worth repeating in future reviews

- Minor: `pid` from add_prompt unused; `search_prompts` has no empty-query guard (wiki/save_prompt
  do) and no try/except → malformed query could propagate out of `dispatch()`; `_fetch_wiki`
  recursion theoretically unbounded (practically 1 level); empty-extract existing pages report
  "не найдено". All spec-compliant (brief specified the exact code) — quality notes, not spec fails.
- `read_file` misdetected the report .md as binary — see the SKILL.md pitfall (long-line
  misdetection; `file`/`xxd`/`cat` workaround).

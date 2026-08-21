---
name: hermes-token-analytics
description: "Analyze Hermes token usage from state.db; optimize spend."
---

# Hermes Token Analytics & Cost Optimization

Use when the user asks about token spend / cost analytics ("сколько потрачено токенов",
"аналитика по токенам", cost reports) or wants to optimize Hermes costs. Also used to
compare before/after after config changes (the two-week A/B check).

## Data source

Every Hermes profile keeps its session store in `state.db` (SQLite, FTS5):
- default profile: `~/.hermes/state.db`
- named profile: `~/.hermes/profiles/<name>/state.db` (also `$HERMES_HOME` if set)
- A profile dir WITHOUT state.db = zero sessions ever ran there (e.g. fresh profiles
  created but never used). Report that, don't guess numbers.

Key tables (schema via `sqlite3 db ".schema sessions"`):
- `sessions` — one row per session: `input_tokens, output_tokens, cache_read_tokens,
  cache_write_tokens, reasoning_tokens, estimated_cost_usd, actual_cost_usd,
  api_call_count, tool_call_count, message_count, started_at, ended_at, source
  (cli/cron/subagent/telegram), model, title`
- `session_model_usage` — per-model breakdown (PK includes billing_provider)
- `messages` — per message; `token_count` is usually NULL, so estimate size via
  `LENGTH(content)/4`

## Workflow

1. `python3 scripts/aggregate_profiles.py` — totals per profile, by model, by month.
2. `python3 scripts/session_deep_dive.py <session_id>` — one session: role/tool
   distribution, heaviest messages, duplicates, timeline.
3. Diagnose with the mental model: **cost ≈ context size × API call count**.
   Each API call re-sends the whole growing context (that's the cache_read flood);
   shrinking either factor cuts cost directly.

## Interpretation patterns (measured 07-08.2026, deepseek provider)

- cache_read is usually ~98% of billed tokens; input+output are the small part.
- Sessions with 100+ messages cost ~86% of the total. 200+ tool calls = 6x the
  cost of 0-50 calls.
- `subagent` source is ~15x cheaper per session than interactive `cli` — delegate
  exploration/routine work instead of doing it interactively.
- Heaviest context bloaters, in order: playwright browser snapshots (up to 68K
  chars for one full-page snapshot!), skill_view of a whole skill (52K chars when
  references are included), patch diffs accumulating (43 patches ≈ 66K), read_file
  of whole big files, terminal tracebacks.
- `actual_cost_usd` stays 0 (provider doesn't report billing); `estimated_cost_usd`
  comes from internal pricing tables — state that caveat in the report.

## Optimization levers (via `hermes config set` — never hand-edit config.yaml)

- `compression.threshold_tokens 80000` — absolute token cap; compression triggers
  at the lower of ratio threshold and this value.
- `compression.proactive_prune_tokens 48000` — deterministic prune of old tool
  results (snapshots, big outputs) BEFORE they ride every turn. Biggest single win;
  the real fix for snapshot bloat.
- `compression.threshold 0.5` — ratio trigger; NOTE it's floored (raise-only) at
  0.75 for models with context < 512K, so on small-window models ratio alone may
  never fire — that's why threshold_tokens/prune matter.
- `compression.target_ratio`, `protect_last_n`, `micro_compact` (opt-in, breaks
  prompt-cache prefix every turn — measure before enabling).
- `model.default deepseek-v4-flash` — ~40x cheaper than deepseek-v4-pro; keep pro
  only for explicit architectural requests.
- Playwright MCP runs with `--headless`; `full:false` is a per-call param, so it
  must be encoded as a behavioral rule (see below), not server config.

## Behavioral rules → SOUL.md, not config

Per-call discipline can't be configured; put it in the profile's SOUL.md (system
prompt, auto-injected). The section used 17.08.2026 ("Экономия токенов"):
- browser snapshots: `full=false`; use `browser_find`/element snapshots
- skill_view: pass `file_path` for one reference, don't load whole SKILL.md
- after successful patch/write_file: don't re-read the file or quote the diff
- read_file: use offset/limit ranges, not whole files
- batch independent tool calls in one message (cuts API rounds 2-3x)
- at ~200 messages propose a NEW session with handoff; >1h propose /compact
- default flash; pro only on explicit request

## Category / work-type attribution (verified 2026-08-21, 180 sessions)

When the user asks «сколько потрачено на архитектуру / спеки / разработку /
тестирование»: classify sessions by `title` (+ `repo` when present) with keyword
regexes, then sum tokens per bucket. Working recipe (scripts live in /tmp during
the session; re-derive from `.schema sessions` before trusting column names):

- Categories used: Архитектура (architecture/ADR/GSD-Core), Спеки/планирование
  (spec/plan/README/doc), Разработка (feature work by repo), Тестирование
  (tests/QA/verification), Прочее.
- **Unnamed subagent sessions**: `title` is NULL for spawned subagents — bind them
  to their parent via `parent_session_id` before classifying, or they all fall
  into «Прочее» and skew the breakdown.
- **No `reasoning_tokens` column exists** in `sessions` (schema varies by version)
  — SELECT the alias you need, or check `.schema` first; earlier scripts crashed
  on `r['reasoning_tokens']`.
- Report TWO views: totals (input+output+cache_read) AND new-token totals
  (input+output only). Cache-read dominates (~98%) and drowns the comparison.
- **Cost attribution**: trust ONLY deepseek-provider sessions for USD estimates.
  HF-router `estimated_cost_usd` rows are garbage (single session showed $74.3K;
  whole-period total read $81.8K vs ~$12.4 real when computed on deepseek rows
  only). Present deepseek-only numbers, label the rest as unreliable.

## Pitfalls

- `messages.token_count` is NULL for essentially all rows in older DBs — the
  message-size breakdown must use `LENGTH(COALESCE(content,''))`.
- Config changes apply to the NEXT session, never mid-conversation (prompt
  caching invariant).
- Profile-safe: resolve paths via `$HERMES_HOME`, don't hardcode `~/.hermes`.
- `hermes config check` validates after changes (exit 0 = OK).

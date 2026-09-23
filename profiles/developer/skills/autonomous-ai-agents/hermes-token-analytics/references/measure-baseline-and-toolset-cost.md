# Measuring baseline context & toolset schema cost (measured 2026-09, developer profile)

Profile: `~/.hermes/profiles/developer/state.db` (252 sessions, ~1.1B tokens, 19.07–03.09).
Default profile DB is tiny/empty — always check the named profile.

## Key reality: system_prompt column is empty

`sessions.system_prompt` is NULL for essentially all rows. You CANNOT read the prompt
text out of the DB. Baseline must be inferred from token counts, not by reading the prompt.

## Recipe: estimate the baseline (system prompt + tool schemas) value

`input_tokens` on a fresh session == system prompt + first message. Pick sessions with
a small number of API calls and few messages:

```sql
SELECT model, source, input_tokens, api_call_count, message_count
FROM sessions
WHERE api_call_count BETWEEN 1 AND 2 AND input_tokens > 0
ORDER BY input_tokens ASC;
```

On the developer profile the realistic baseline cluster was **~22–23k tokens** for
1-call `cli` sessions (deepseek). A naive "50k for tool descriptions" guess was ~2x high.

PITFALL: ignore the tiny min-input outliers (e.g. 63, 773 tokens). Those are truncated /
crashed sessions and do not represent a real baseline. Take the cluster, not the min.

## Constant tools vs deferred toolsets (the dominant insight)

Only **non-deferred (constant)** tools are injected into the system prompt on EVERY call.
Deferred toolsets (mcp-github 26 tools, mcp-obsidian-brain 14 tools) live in a `tool_search`
catalog and are loaded **on demand** — they are NOT in the per-call constant context.

Therefore: `/tools disable mcp-github mcp-obsidian-brain` saves almost nothing. Only
constant toolsets matter for per-call savings. People overestimate the win by disabling
MCP sets they think are loaded; they aren't.

Config plumbing (profile config.yaml):
- `toolsets:` (top, list) — which toolset loads, e.g. `[hermes-cli]`
- `agent.disabled_toolsets: []` — what `/tools disable` writes to
- `platform_toolsets.cli:` — canonical toolset names (browser, clarify, code_execution,
  computer_use, cronjob, delegation, file, image_gen, memory, session_search, skills,
  terminal, todo, tts, vision, web)
- `delegation.inherit_mcp_toolsets: true` — whether MCP toolsets are inherited

## Measured per-toolset schema weight (approx, constant tools)

| Toolset | ~tokens of schema |
|---|---|
| cronjob | ~1200 (huge schema) |
| delegation (delegate_task) | ~1100 |
| browser (browser_exec) | ~900 |
| code_execution (execute_code) | ~900 |
| tts (text_to_speech) | ~700 |
| session_search | ~700 |
| vision (vision_analyze) | ~500 |
| **7 disabling constant sets** | **~6000 tokens/call** |

Minimal dev set `--tools file,terminal,skills,web,memory,clarify,todo` = 12 constant tools,
roughly ~8k/call vs the full ~21 constant tools.

## What actually drives the spend (the real lever, not tools)

Measured on this profile:
- avg `cache_read_tokens` per API call: **~108,651**
- avg API calls per session: **39**
- avg `cache_read_tokens` per session: **~4,311,582** (≈98% of all billed tokens)
- total: ~1.1B across 252 sessions

Tool trimming saves ~6–8k/call → ~5% of a session. The other ~100k/call is accumulated
history (snapshots, diffs, tracebacks). The real win is `compression.proactive_prune_tokens`
(~48000) + discipline of SHORT sessions (`/compact` or new session + handoff past ~200
messages) — those are an order of magnitude bigger than tool trimming.

Aggregate script: same dir, `scripts/aggregate_profiles.py`; report cache_read dominance
and label deepseek-only USD as reliable, HF-router `estimated_cost_usd` as garbage.

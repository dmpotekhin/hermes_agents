---
name: obsidian-brain
description: AI-native memory layer in Obsidian — signals, dream engine, preferences, dev journaling. Use brain_feedback to record user preferences, brain_dream to process, brain_devlog during development sessions, brain_create_note for session summaries.
platforms: [macos]
---

# Obsidian Brain MCP

AI-native memory inside Obsidian vault at `Brain/`. 14 MCP tools for signals, preferences, dev journaling, search, health checks.

## Quick reference

| Tool | When |
|------|------|
| `brain_feedback` | User expresses a preference or correction |
| `brain_dream` | Process inbox signals into preferences (after ≥3 on one topic) |
| `brain_context` | Load active preferences at session start — also returns `recent_activity` (last journal entries from `journal/`, handoff «где остановились»; `getRecentJournalEntries` in `src/core/journal.ts`) |
| `brain_devlog` | Log actions DURING development (incremental) |
| `brain_create_note` | Write structured notes, session summaries (auto-fills `entities` frontmatter — top-10 frequency keywords, ai-memory style, unless provided explicitly) |
| `brain_status` | Check counts, last dream |
| `brain_health` | Diagnostic scan |

## Dev journaling workflow

MANDATORY after every development session:

1. **During session**: use `brain_devlog` incrementally
   ```
   brain_devlog(entry="Created Gradle files", project="qa-trainer")
   ```
2. **End of session**: use `brain_create_note` for structured summary
   - Path: `journal/YYYY-MM-DD.md`
   - Include: timestamped timeline, decisions, files created, bugs fixed

Dev journals live at `Brain/journal/` — readable in Obsidian.

## Vault layout

```
Brain/
├── _brain.yaml              # Config: thresholds, TTL
├── active.md                # Auto-generated preferences summary
├── inbox/                   # Pending signals
├── preferences/             # Active rules (unconfirmed/confirmed/quarantine)
├── retired/                 # Expired/rebutted rules
├── notes/                   # Agent notes
├── journal/                 # Dev journals: YYYY-MM-DD.md
├── obligations/             # Recurring tasks
├── log/                     # Decision log
└── .snapshots/              # Pre-dream backups
```

## Preference lifecycle

```
inbox → dream → unconfirmed → confirmed → quarantine → retired
                        ↑ recovered ↑
```

- `candidate_threshold: 3` — signals needed to create preference
- `unconfirmed_ttl_days: 30` — expire without evidence
- `stale_evidence_days: 90` — retire without recent use

## MCP server

- Code: `/Users/dmitrypotekhin/brain/` (TypeScript, bun, 135 tests)
- Config: `~/.hermes/profiles/developer/config.yaml` under `mcp_servers.obsidian-brain`
- Vault env: `BRAIN_VAULT=/Users/dmitrypotekhin/Odsidian/obsidians/Obsidian Vault`
- Restart after code changes: `hermes gateway restart`
- GitHub: https://github.com/dmpotekhin/obsidian-brain

## Testing pitfall: vaultRoot cache leaks across test files

`vaultRoot()` (`src/core/vault.ts`) caches `BRAIN_VAULT` in a module global (`vaultRootCache`) on FIRST call. bun:test does NOT reset module state between test FILES, so a test that sets `BRAIN_VAULT` but never resets the cache makes all later files silently read/write the FIRST file's vault. Symptoms: tests pass in isolation (`bun test tests/x.test.ts`), fail in full run; files that assert on their own `TEST_VAULT` path (e.g. `log.test.ts`) break after any file with `tempVault()` (which deletes its vault in afterEach).

MANDATORY pattern: every test file that sets `BRAIN_VAULT` must call `resetVaultRoot()` (exported from `src/core/vault.ts`) immediately BEFORE assigning the env var — in `tempVault()` helpers and `beforeAll` blocks alike. Done once for all 20 test files (commit 4730ba0). If you add a new test file touching the vault, include `resetVaultRoot()` or the whole suite order becomes load-bearing.

See `references/testing-vault-root-cache.md` for the full root-cause walkthrough.

## Search (FTS5) pitfalls

- `brain_search` uses SQLite FTS5 (`SearchIndex` in `src/core/search.ts`). FTS5 parses `a-b` in MATCH as `a NOT b` — searching `docker-compose` silently excludes the very file containing it. Fix is in place: bare hyphenated queries are wrapped in double quotes (phrase match).
- Entities are appended to the indexed content, so a page is found by an entity word even if it never appears in the body (recall aid, ai-memory style).
- When tokenizing for entities (`src/core/entities.ts`), the markdown-strip regex must NOT include `-` in its character class — `[*_>~|+-]` destroys hyphenated terms like `docker-compose`. Kept as `[*_>~|+]`.
- Toolchain is GREEN (fixed 2026-08-20): `bun run typecheck`, `bun run lint`, `bun test` all pass. Two pre-existing failures were repaired: (1) `obligations.ts` TS errors — `noUncheckedIndexedAccess` makes `match[1]` / `.split()[0]` `string | undefined`; (2) oxlint 1.75 shim dies on system Node 14 (`ERR_UNKNOWN_FILE_EXTENSION`) — lint now runs oxlint via bun. Never re-introduce `.oxlintrc.json` in the old invalid format (`rules: {"typescript": "recommended"}`). See `references/typecheck-lint-toolchain.md` for root causes, config formats, and the surgical unused-import lesson.

See `references/search-fts5.md` for the entities design and the exact fix.

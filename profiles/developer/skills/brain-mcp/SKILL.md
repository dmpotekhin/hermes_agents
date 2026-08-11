---
name: brain-mcp
description: Work with the Brain MCP server — a custom memory layer for AI agents using Obsidian vaults. Record signals, run the dream rule engine, manage preferences, and maintain dev journals.
---

# Brain MCP

Custom MCP server that adds AI-native memory to Hermes via an Obsidian vault. Records user feedback as signals, runs a deterministic rule engine (Dream) to form preferences, and tracks evidence to keep rules grounded.

**Repo:** `/Users/dmitrypotekhin/brain/` (GitHub: dmpotekhin/obsidian-brain)
**Vault:** `/Users/dmitrypotekhin/Odsidian/obsidians/Obsidian Vault/Brain/`
**MCP config:** `~/.hermes/profiles/developer/config.yaml` → `obsidian-brain`

## Architecture

```
Brain/ (inside Obsidian vault)
├── _brain.yaml          # Config: candidate_threshold, stale_evidence_days
├── _BRAIN.md            # Operating manual for agents
├── active.md            # Auto-generated summary of active preferences
├── inbox/               # Raw signals from user interactions
│   └── processed/       # Signals already processed by dream
├── preferences/         # Active rules (pref-*.md)
├── retired/             # Retired/obsolete rules
├── notes/               # Free-form agent notes
├── journal/             # Dev journal (daily .md files)
├── obligations/         # Recurring tasks with cadences
├── log/                 # Daily event log (YYYY-MM-DD.md)
└── .snapshots/          # Pre-dream backups (.tar.zst)
```

## Preference lifecycle

```
inbox (signals) → dream → unconfirmed → confirmed → quarantine → retired
                          ↑_____________↑____________│
                              (recover)               │
                                                      ↓
                                                   retired
```

Dream is deterministic — no LLM inside. It runs on `candidate_threshold` (default 3 signals per topic).

## MCP tools (14 total)

| Tool | Category | Purpose |
|------|----------|---------|
| `brain_feedback` | Writer | Record a taste signal (positive/negative) |
| `brain_apply_evidence` | Writer | Record preference applied/violated/outdated |
| `brain_create_note` | Writer | Create markdown note in Brain/notes/ |
| `brain_devlog` | Writer | Append timestamped entry to dev journal |
| `brain_dream` | Lifecycle | Run the rule engine (supports dry_run) |
| `brain_context` | Reader | Read active confirmed + quarantined preferences |
| `brain_context_pack` | Reader | Budgeted context slice within token limit |
| `brain_search` | Search | FTS5 full-text search over vault |
| `brain_status` | Admin | Vault path, counts, last dream |
| `brain_audit` | Admin | Log history for a specific preference |
| `brain_rollback` | Admin | Restore most recent snapshot |
| `brain_health` | Health | Verdict + domain diagnostics |
| `brain_hygiene` | Health | Near-duplicate prefs + stale signals scan |
| `brain_obligation` | Tasks | Manage recurring obligations |

## Dev journaling workflow

Two tools for documenting development sessions:

### `brain_devlog` — incremental (use DURING work)

```
brain_devlog(entry="Created Gradle build files", project="qa-trainer")
brain_devlog(entry="Wrote BasicsFragment with ViewBinding", project="qa-trainer")
```

Writes to `Brain/journal/YYYY-MM-DD.md`:
```
14:05 | project:qa-trainer | Created Gradle build files
14:10 | project:qa-trainer | Wrote BasicsFragment with ViewBinding
```

Call frequently during coding — one line per meaningful action.

### `brain_create_note` — summary (use at END of session)

```
brain_create_note(
  path="journal/2026-07-25.md",
  content="# Dev Journal — 2026-07-25\n\n## Project X\n\n### 14:05 — Setup\n- ..."
)
```

Writes a full narrative summary with context and decisions.

### Pattern

1. During work → `brain_devlog` for timestamped log entries
2. End of session → `brain_create_note` for the full narrative summary
3. After journal → **auto-generate 5 blog post topics** via content-factory

### Post-devlog: auto-generate topics for Telegram blog

After writing dev journal entries, generate 5 post topics from recent work:

```
python3 -c "
from modules.devlog_scanner import scan_recent_events, format_events_for_llm
from modules.topic_suggester import build_suggestion_prompt
e = scan_recent_events(days=7)
print(build_suggestion_prompt(format_events_for_llm(e), max_topics=5))
"
```

Then the LLM (Hermes) generates 5 topics and saves them to:
`Brain/notes/content/YYYY-MM-DD-topics.md`

Use `brain_create_note` with path `content/YYYY-MM-DD-topics.md` for the save.

Контент-фэктори: `/Users/dmitrypotekhin/content-factory/`
Default: 5 topics, LLM-based preferred (rule-based is fallback).

## Setup / restart

After pushing code changes to the brain repo:

```bash
hermes gateway restart
```

This reloads the MCP server process with updated code. Without restart, the old server keeps running with stale code.

## Pre-push checklist

Before pushing brain repo to public GitHub, scan for secrets:

```bash
cd /Users/dmitrypotekhin/brain

# Personal paths in source
grep -rn '/Users/' src/ --include='*.ts'

# Hardcoded paths in scripts
grep -rn '/Users/' bin/

# Tracked IDE/config files
git ls-files .idea/ .superpowers/ .env
```

Common issues: hardcoded vault paths in `bin/o2b-mcp`, `.idea/` tracked by git, `.superpowers/` task briefs with real paths.

→ See `references/pre-push-secrets-scan.md` for the full checklist.

## Testing

```bash
cd /Users/dmitrypotekhin/brain
bun test                    # Full suite (121 tests)
bun run typecheck           # TypeScript check
bun run validate            # typecheck + lint + test
```

## Key files

| File | Purpose |
|------|---------|
| `src/mcp/server.ts` | JSON-RPC 2.0 stdio MCP server |
| `src/mcp/tools.ts` | Tool registry (buildToolTable) |
| `src/mcp/tools/writer.ts` | brain_feedback, brain_apply_evidence, brain_create_note, brain_devlog |
| `src/mcp/tools/lifecycle.ts` | brain_dream |
| `src/mcp/tools/reader.ts` | brain_context, brain_context_pack |
| `src/core/dream.ts` | Deterministic rule engine |
| `src/core/vault.ts` | vaultRoot(), brainDir(), atomicWrite() |
| `src/core/preference.ts` | CRUD for preferences |
| `src/core/signal.ts` | Signal writer |
| `src/core/log.ts` | Daily event log |
| `src/core/search.ts` | FTS5 index |
| `bin/o2b-mcp` | MCP server launcher script |

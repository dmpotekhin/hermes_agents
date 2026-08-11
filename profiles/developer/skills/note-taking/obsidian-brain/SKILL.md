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
| `brain_context` | Load active preferences at session start |
| `brain_devlog` | Log actions DURING development (incremental) |
| `brain_create_note` | Write structured notes, session summaries |
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

- Code: `/Users/dmitrypotekhin/brain/` (TypeScript, bun, 121 tests)
- Config: `~/.hermes/profiles/developer/config.yaml` under `mcp_servers.obsidian-brain`
- Vault env: `BRAIN_VAULT=/Users/dmitrypotekhin/Odsidian/obsidians/Obsidian Vault`
- Restart after code changes: `hermes gateway restart`
- GitHub: https://github.com/dmpotekhin/obsidian-brain

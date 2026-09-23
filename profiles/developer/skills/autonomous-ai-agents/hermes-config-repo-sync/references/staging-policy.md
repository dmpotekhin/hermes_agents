# Staging policy for the ~/.hermes config repo

## Junk map — paths that must never be committed

Measured in this repo (sizes give the order of magnitude, they grow over time):

| Path | Size | What it is |
|------|-----:|-----------|
| `profiles/developer/state.db.bak-<ts>` | ~440 MB | pre-update DB backup |
| `profiles/*/state-snapshots/` | ~420 MB | per-profile DB snapshots taken before updates |
| `backups/pre-update-<ts>.zip` | ~310 MB | whole-tree zip from the updater |
| `profiles/developer/node/` | ~190 MB | embedded Node runtime |
| `profiles/*/skills/.hub/index-cache/` | ~46 MB | skills-hub cache |
| `profiles/*/skills/.curator_backups/**` | MBs each | curator blobs (some already tracked in history — do not add more) |
| `profiles/*/pending/` | ~400 KB | pending memory writes (personal, transient) |
| `profiles/*/terminal-sessions/`, `spawn-ledger.json`, `shared-state.db` | small | live runtime state |
| `**/__pycache__/`, `*.pyc`, `*.zip`, `*.db.bak*`, `state.db*` | — | build/db residue |
| `kanban.db-shm`, `kanban.db-wal`, `profiles/*/verification_evidence.db-shm\|-wal` | 32 KB / 0 B | SQLite sidecars — gitignore covers `kanban.db` and `verification_evidence.db` but NOT their `-shm`/`-wal` twins |

Rule of thumb: if a path is a **database, a backup/snapshot, a vendored runtime, or a cache**,
it is not config and does not belong in git.

## Recommended .gitignore block (append only with user approval)

```gitignore
# Backups & DB snapshots (hundreds of MB)
backups/
**/backups/
**/state-snapshots/
state.db.bak*
*.db.bak*
*.zip

# Embedded Node runtime + Python caches
node/
**/node/
**/__pycache__/
*.pyc

# Skills hub caches and curator blobs
**/skills/.hub/*-cache/
**/skills/.curator_backups/

# Live runtime state
**/pending/
**/terminal-sessions/
spawn-ledger.json
shared-state.db

# SQLite sidecars (the .db itself is already listed)
*.db-shm
*.db-wal
```

`.gitignore` in `~/.hermes` is a protected file: prepare the block, ask once, apply only with
the user's answer. Until it is applied, 300+ junk paths stay untracked and every future sync
must stage by explicit paths (which `scripts/stage_config_changes.sh` does).

## README fact-gathering checklist

```bash
git remote -v                                              # repo URL / badges
ls -d profiles/*/                                          # profile list
git ls-files 'profiles/<p>/**/SKILL.md' | wc -l             # skills per profile
git ls-files '*SKILL.md' | wc -l                            # all skills, all profiles
search_files 'config.yaml' target=files path=~/.hermes/profiles  # which profiles have own config
sed -n '/^model:/,/^providers:/p' profiles/<p>/config.yaml  # model + provider
```

- Profiles without their own `config.yaml` inherit the global one — say so in the README
  instead of inventing a model per profile.
- MCP servers: the keys directly under `mcp_servers:` in the profile config.
- Confirm a data section (e.g. `jp_rag_data`) is unchanged before keeping its description:
  `git show --stat <sync-commit> -- jp_rag_data` (empty = untouched).
- Never re-describe the previous README — it lags reality (models change, profiles are added).

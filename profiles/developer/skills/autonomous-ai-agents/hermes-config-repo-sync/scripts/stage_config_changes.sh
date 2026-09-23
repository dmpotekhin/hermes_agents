#!/usr/bin/env bash
# Stage meaningful changes in the ~/.hermes config repo, keeping runtime state out of git.
# Usage: bash stage_config_changes.sh [repo_dir]
# Prints: untracked/candidate counts, largest staged blobs, SQLite sidecar warnings, totals.
# Never commits, never pushes.
set -uo pipefail

REPO="${1:-$HOME/.hermes}"
cd "$REPO" || exit 2

# 1. tracked modifications (and deletions)
git add -u || exit 2

# 2. untracked -> candidate list, minus junk
git status --porcelain | sed -n 's/^?? //p' > /tmp/hermes_untracked.txt

JUNK_DIRS='(^|/)(state-snapshots|backups|node|node_modules|__pycache__|\.curator_backups|index-cache|scan-cache|pending|terminal-sessions|sessions|logs|audio_cache|image_cache|\.backup-[^/]*)(/|$)'
JUNK_FILES='(\.pyc|\.zip|\.db\.bak|\.tmp)$|^state\.db|^kanban\.db|spawn-ledger\.json|shared-state\.db|\.npm_lock_hash|install_id$'

# grep -Ev can match nothing; no set -e so the script keeps going
grep -Ev "$JUNK_DIRS" /tmp/hermes_untracked.txt | grep -Ev "$JUNK_FILES" > /tmp/hermes_add.txt || true

printf 'untracked: %s   candidates: %s\n' "$(wc -l < /tmp/hermes_untracked.txt | tr -d ' ')" "$(wc -l < /tmp/hermes_add.txt | tr -d ' ')"

# 3. NUL-delimited input survives spaces; BSD xargs has no -a
tr '\n' '\0' < /tmp/hermes_add.txt | xargs -0 git add -- || exit 2

echo '--- unstage these SQLite sidecars (gitignore misses -shm/-wal) ---'
git diff --cached --name-only | grep -E '\.db-(shm|wal)$' || echo 'none'

echo '--- largest staged files (KB, >500KB) ---'
git diff --cached --name-only | while IFS= read -r f; do
  [ -f "$f" ] || continue
  s=$(stat -f%z "$f" 2>/dev/null || stat -c%s "$f" 2>/dev/null) || continue
  [ "${s:-0}" -gt 500000 ] && printf '%s %s\n' "$((s / 1024))" "$f"
done | sort -rn | head

echo '--- staged totals ---'
git diff --cached --stat | tail -1
echo '--- next: credential scan, commit, push, verify (see SKILL.md) ---'

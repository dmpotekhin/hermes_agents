# Hermes Config Backup → GitHub Private Repo

Push all Hermes profiles, skills, and config to a private GitHub repo as a backup.

## Overview

Backs up `~/.hermes/` — profiles (`japanese-tutor`, `travel-agent`, etc.), shared skills, config.yaml, cron jobs, plugins — while excluding secrets, session data, caches, and temp files.

## Step-by-Step

### 1. Prepare `.gitignore`

Write to `~/.hermes/.gitignore`. Core exclusion patterns:

```gitignore
# Sensitive / secrets
.env
auth.json
nous_auth.json
channel_directory.json
gateway_state.json
gateway.lock

# Embedded git repos (hermes source code, plugins)
hermes-agent/
plugins/*/

# Large cache / DB
models_dev_cache.json
state.db
state.db-shm
state.db-wal
kanban.db

# Session history & logs
sessions/
logs/
*.log
*.history

# Caches
cache/
audio_cache/
image_cache/
sandboxes/
*.skills_prompt_snapshot.json
*models_cache.json
*_cache.json

# Personal memories
memories/

# Binaries
bin/

# Lock & temp files
*.lock
.clean_shutdown
.install_method
.update_check
*.pid
processes.json

# Config backups
config.yaml.bak*

# Pairing / pairing info
pairing/

# Pastes cache
pastes/

# Skills internal state
skills/.bundled_manifest
skills/.curator_*
skills/.usage.json

# Cron output (generated content)
**/cron/output/

# SOUL backups
SOUL.md.save

# Node / deps
node_modules/
```

### 2. Init & Remote

```bash
cd ~/.hermes
git init
git branch -m main
git remote add origin git@github.com:<user>/<repo>.git
```

### 3. Auth — SSH Fallback (when `gh` CLI is absent)

If `gh auth status` fails and no `GITHUB_TOKEN` is configured:

```bash
# Check for existing SSH key
ls ~/.ssh/id_ed25519.pub  # or id_rsa.pub

# If missing, generate one:
ssh-keygen -t ed25519 -C "your@email.com" -f ~/.ssh/id_ed25519 -N ""

# Print public key → add at https://github.com/settings/keys
cat ~/.ssh/id_ed25519.pub

# Test
ssh -T git@github.com

# Switch remote from HTTPS to SSH
git remote set-url origin git@github.com:<user>/<repo>.git
```

### 4. Add, Commit, Push

```bash
cd ~/.hermes

# Remove any files that were previously tracked but are now gitignored
git rm -r --cached . 2>/dev/null

git add .
git commit -m "Initial commit: all Hermes profiles, skills, configs"
git push -u origin main
```

### 5. Verify

```bash
# Check no leaked sensitive files
git diff --cached --name-only | grep -E '(cron/output|\.history|state\.db|nous_auth|\.pid|\.log)'

# Show summary
git diff --cached --stat | tail -5
```

## Pitfalls

- **HTTPS push fails with "Device not configured"** — no credential helper set. Fix: switch to SSH (`git remote set-url origin git@github.com:...`).
- **`gh` CLI not installed** — don't try `gh auth login`. Use SSH keys directly.
- **`.gitignore` trailing `/` on nested paths** — patterns like `cron/output/` only match at repo root. Use `**/cron/output/` to match anywhere.
- **Embedded git repos** — `hermes-agent/` and `plugins/*/` are themselves git repos. `.gitignore` them to avoid nested-repo warnings.
- **Private repo already has content (README, LICENSE)** — use `git pull --rebase origin main` before push, or `git push --force` knowingly.

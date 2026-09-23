---
name: hermes-config-repo-sync
description: "Use when syncing the ~/.hermes config git repo to GitHub."
version: 1.0.0
platforms: [macos]
---

# Hermes Config Repo Sync (~/.hermes -> GitHub)

Use for any request to commit/push the user's Hermes configuration: new skills, profile
changes, plugins, plans, README. Triggered by "сделай пуш изменений в hermes",
"синхронизируй конфиг", "обнови README", or a bare "запушь изменения".

## Repo facts (verify, don't assume)

- **`~/.hermes` itself is the git repo** — remote `git@github.com:dmpotekhin/hermes_agents.git`,
  branch `main`, SSH auth. It tracks `config.yaml`, `SOUL.md`, `README.md`, `.gitignore`,
  `skills/**`, `profiles/<name>/{config.yaml,SOUL.md,skills/**,cron/jobs.json,plugins/**,tools/**}`,
  `jp_rag_data/**`, `plans/**`.
- **`~/.hermes/hermes-agent` is a SEPARATE nested checkout** and is gitignored. Never stage it
  from this repo; install upgrades belong to the `hermes-update-recovery` skill.
- Profiles in play: `developer`, `japanese-tutor`, `travel-agent`, `marketing`, `german-tutor`.
  `marketing` and `german-tutor` have only `SOUL.md` + `skills/` — no own `config.yaml`
  (they inherit the global one).

## Procedure

1. **Recon (read-only, cheap):**

   ```bash
   cd ~/.hermes
git branch --show-current && git remote -v
git status --porcelain | wc -l
git fetch origin && git rev-list --left-right --count origin/main...HEAD
git status --porcelain | grep '^??' | sed 's/^?? //' | while IFS= read -r p; do du -sh "$p"; done | sort -rh | head -25
   ```

   That last line is the important one: it shows which *untracked* paths are enormous before
   you decide anything.

2. **Stage deliberately — never `git add -A`.** A plain `add -A` in this repo sweeps ~1.4 GB of
   runtime state into git (see `references/staging-policy.md` for the junk map). Use
   `bash scripts/stage_config_changes.sh` — it stages tracked modifications with `git add -u`,
   builds a filtered candidate list of untracked files, stages them, and prints the largest
   staged blobs plus the final totals.

3. **SQLite sidecars.** `*.db-shm` / `*.db-wal` are now in `.gitignore` (closed 2026-09-23),
   so `kanban.db-shm|-wal` and `profiles/*/verification_evidence.db-shm|-wal` stay untracked.
   On a checkout with the older `.gitignore` they still show up and get staged — unstage them:

   ```bash
   git diff --cached --name-only | grep -E '\.db-(shm|wal)$'
git restore --staged kanban.db-shm kanban.db-wal profiles/japanese-tutor/verification_evidence.db-shm profiles/japanese-tutor/verification_evidence.db-wal
   ```

4. **Credential scan before committing (mandatory):**

   ```bash
   python3 ~/.hermes/profiles/developer/tools/scan_credentials.py --staged
   ```

   Run it WITHOUT a pipe if you care about the exit code (see pitfalls). A hit is NOT yet a
   confirmed secret: triage it before stopping — masked context, then the documentation-vs-key
   test in `references/scanner-hit-triage.md`. (The `credential-scan` skill is user-owned, so
   that procedure lives here.)

5. **Commit with an informative message, then push:**

   ```bash
   git commit -m "chore(sync): <area> — <one-line summary>" -m "+N общих навыков: ...\n+skills профиля developer: ...\nНовые профили ...\nПлагины ...\nПланы ..."
git push origin main
   ```

   Name the areas (profiles / skills / plugins / plans / config) — the older history contains
   commits whose entire message is a single digit, which makes rollback and audit impossible.

6. **Verify the push landed, don't assume:**

   ```bash
   git fetch origin && git rev-list --left-right --count origin/main...HEAD   # want: 0	0
git log --oneline -1 origin/main
   ```

## README upkeep

When the user asks to update the README, derive **every** fact from the files, never from the
previous README (it goes stale silently):

| Fact | Source |
|------|--------|
| Repo URL / badge links | `git remote -v` — the badge once carried a typo'd repo name; never copy the URL out of the old README |
| Profiles list | `ls -d profiles/*/` |
| Skills per profile / global | count `SKILL.md` files: `git ls-files '*SKILL.md' \| wc -l`, per profile `git ls-files 'profiles/<p>/**/SKILL.md' \| wc -l` |
| Model / provider per profile | the `model:` block of `profiles/<p>/config.yaml` (absent file = inherits global `config.yaml`) |
| MCP servers | keys under `mcp_servers:` in `profiles/<p>/config.yaml` |
| Plugins | `profiles/<p>/plugins/*/` |
| Plans | `git ls-files plans` |
| Cron jobs | `profiles/<p>/cron/jobs.json` |

Keep sections that are still true instead of rewriting from scratch, and add a short
"Что нового" section for the sync that just landed — that is what the user reads. Confirm
data sections did not change with `git show --stat <commit> -- jp_rag_data` rather than
re-describing them from memory. Full checklist: `references/staging-policy.md`.

## Pitfalls

- **`~/.hermes/README.md` and `~/.hermes/.gitignore` are protected agent-instruction files.**
  Writes to them are refused when the approval prompt times out, and re-routing the write
  through terminal/python is explicitly forbidden. Do not retry. Prepare the content at
  `/tmp/<name>.md` and hand the user ONE apply command:
  `cp /tmp/hermes-README-new.md ~/.hermes/README.md && cd ~/.hermes && git add README.md && git commit -m "docs: ..." && git push origin main`.
  Ask for README and `.gitignore` approval as separate questions — a refusal on one must not
  block the other.
- **A timed-out approval or `clarify` is NOT consent.** Stop, report exactly what is committed
  / pushed and what is pending, and leave the prepared artifacts on disk.
- **Check the scanner's exit code without a pipe.** `scan | tail -5; echo $?` prints tail's
  status, not the scanner's — `--staged` is documented to return `1` on a finding, so a piped
  invocation can look like success.
- **macOS BSD `xargs` has no `-a`.** Feed it `tr '\n' '\0' < list | xargs -0 git add --`, or use
  `git add --pathspec-from-file=list`; plain `xargs -a` fails with `illegal option -- a`.
  NUL-delimited input also survives paths containing spaces.
- **Gather facts with `read_file` / `search_files` / `git` plumbing.** Heredoc scripts
  (`python3 - <<'PY'`) and inline `python3 -c` one-liners hit the command-approval gate; when
  the user has stepped away they time out and burn a round trip for information that `git ls-files`
  or `read_file` returns instantly and ungated.
- **Large binaries are a judgement call, not an automatic include.** A generated multi-MB roster
  (`plugins/agency-agents-router/data/agents.json`) is committed but will bloat history if it
  churns; keep it only when the plugin cannot work without it, and say so in the report.
- **Report the split.** After a partial run, state plainly: what was committed+pushed (with the
  range `oldsha..newsha main -> main`), what stayed out of git and why, and the exact command
  the user can run to finish.

## Verification

```bash
cd ~/.hermes
git fetch origin && git rev-list --left-right --count origin/main...HEAD   # 0	0
git log --oneline -1 origin/main
git status --porcelain | grep -c '^??'                                    # remaining untracked = junk only
python3 ~/.hermes/profiles/developer/tools/scan_credentials.py --staged; echo "scan exit=$?"
```

## Support files

- `references/staging-policy.md` — the junk map of `~/.hermes` (what must never enter git),
  the recommended `.gitignore` block, and the README fact-gathering checklist.
- `references/scanner-hit-triage.md` — how to decide whether a `scan_credentials.py` hit is a
  real secret or documentation before stopping the commit.
- `scripts/stage_config_changes.sh` — one-shot stager: tracked mods + filtered untracked files,
  prints biggest staged blobs, SQLite sidecar warnings and totals. Never commits or pushes.

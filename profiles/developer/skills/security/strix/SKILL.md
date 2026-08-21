---
name: strix
description: Use when running AI pentest/security scans with Strix.
---

# Strix (AI pentesting tool)

Strix is an **open-source autonomous AI pentesting tool** (github.com/usestrix/strix). It is
**NOT a Hermes skill or plugin** — it is a standalone CLI whose agents dynamically run a target,
find vulnerabilities, and produce working PoCs + remediation guidance.

## When to use
- User asks to "scan / pentest / security-test" a repo, URL, API spec, or local directory.
- User references "strix" or pastes the repo link and asks "how do I use this".
- User wants to wire up automated security scanning (CI/CD, PR review).
- **Track record:** this user has already run Strix and it found real, actionable vulnerabilities —
  they explicitly said they liked it ("нашел уязвимости, понравился"). Don't hedge about whether
  Strix "works" — treat it as the proven default for this user's security-scan requests.

## Key facts (do not re-derive)
- Two distinct run modes, same engine:
  1. **Local CLI (self-hosted)** — free, BYO LLM key, **requires Docker** (sandbox container).
  2. **Managed cloud** (app.strix.ai) — no Docker, no LLM key, but uses Strix's own models and
     needs a separate Strix account + API token. Cannot reach `localhost` targets (live-test
     impossible for local apps) — cloud only scans public repos/URLs.
- The sandbox runtime has **exactly one backend**: `docker`. `STRIX_RUNTIME_BACKEND` supports no
  other value (confirmed from `strix/runtime/backends.py`). There is NO local non-Docker mode.
- LLM is selected via **LiteLLM** `provider/model` format (100+ providers supported).

## Install (macOS)
```bash
curl -sSL https://strix.ai/install | bash   # downloads binary to ~/.strix/bin
```
- The install script is clean (downloads a prebuilt binary from GitHub releases; references
  sandbox image `ghcr.io/usestrix/strix-sandbox`).
- Add to PATH (zsh): `export PATH="$HOME/.strix/bin:$PATH"` in `~/.zshrc`.
- **Pitfall:** the release binary is ~70 MB and GitHub release downloads are SLOW from some
  networks — the naive `curl | bash` can exceed the 300s foreground timeout. Download the asset
  directly in the background with resume instead:
  `curl -sSL -C - --retry 5 -o strix.tar.gz <asset-url>` then `tar xzf` and move to `~/.strix/bin/strix`.
- Verify: `strix --version`. (`strix --help` may hang because it probes Docker — not a failure.)

## LLM config (LiteLLM)
Set `STRIX_LLM` + `LLM_API_KEY`, either as env vars or in `~/.strix/cli-config.json`:
```json
{ "env": { "STRIX_LLM": "deepseek/deepseek-v4-pro", "LLM_API_KEY": "sk-..." } }
```
`chmod 600` the config file (contains a secret).

### DeepSeek specifics
- DeepSeek IS supported (LiteLLM provider prefix `deepseek/`).
- **Model names are V4 generation, NOT the old `deepseek-chat`/`deepseek-reasoner`.** This user's
  account exposes `deepseek-v4-pro` (better) and `deepseek-v4-flash` (cheap/fast). Always verify
  with: `curl -s https://api.deepseek.com/v1/models -H "Authorization: Bearer $KEY"` and use the
  IDs it returns → `deepseek/deepseek-v4-pro`.
- Default base `api.deepseek.com` is auto-detected; `LLM_API_BASE` only if custom.

## Running a scan
```bash
strix --target ./app-directory            # local code (mounted writable — commit/stash first)
strix --target https://github.com/org/repo
strix --target https://your-app.com        # black-box live test (needs public reachability)
strix -n --target ./ --scan-mode quick --max-budget 10   # headless CI mode (always use -n)
```
- `--scan-mode`: `quick` | `standard` | `deep`.
- Headless exit codes: `0` clean, `1` fatal, `2` vulnerabilities found.
- Artifacts in `strix_runs/<run-name>/`: `penetration_test_report.md`, `vulnerabilities/*.md`,
  `vulnerabilities.json`, `findings.sarif`, `run.json`.
- CLI docs for LLMs: https://docs.strix.ai/llms.txt

## Docker requirement & macOS vmnetd fix
Local CLI requires a working Docker daemon. On macOS, Docker Desktop can break with the backend
stuck logging `pinging vmnetd` and `docker ps` failing while `com.docker.backend` runs. Root cause
is usually a **missing `com.docker.vmnetd` binary** in `/Library/PrivilegedHelperTools/` (the plist
points there but the file was never copied). See `references/docker-desktop-vmnetd-fix.md` for the
diagnostic + one-command fix (restore the binary from inside Docker.app; needs sudo).

## Diagnosing an empty/failed run (0 findings ≠ clean)
A run that writes `findings.sarif` with `"results": []` may have found nothing — OR may never have
run. Before reporting "clean", confirm the scan actually executed:
- `run.json`: `"status"` must NOT be `"failed"`; `llm_usage.requests` must be > 0 (and `cost` > 0).
  `0` requests / `0` tokens / `0` cost means the agents never drove the LLM at all.
- `strix.log` signature of a Docker-down failure: an early `INFO ... Bringing up sandbox session`,
  then a long stall (tens of minutes), then `cleanup(...): no cached session` — the sandbox container
  never started, so nothing was analyzed.
- Telemetry `error` events + a SARIF with 0 results = the run died before analysis. Fix the
  environment (start Docker, wait for `docker ps` to succeed, pull the sandbox image) and RE-RUN —
  do not present it as "no vulnerabilities found".

## Pre-flight checklist (run before any scan — turns a would-be 70-min failed run into an instant diagnosis)
1. Docker daemon up: `docker ps` must list containers (not "Cannot connect to the Docker daemon").
   Down? `open -a Docker`, then poll `docker ps` until it answers (vmnetd fix may be needed — see reference).
2. Sandbox image present: `docker images | grep strix` should show `ghcr.io/usestrix/strix-sandbox:1.3.0`
   (~4 GB). If absent, `docker pull` it in the BACKGROUND (notify_on_complete) BEFORE launching the scan —
   pulling the 4 GB image inline is indistinguishable from the Docker-down hang above and eats the run budget.
3. LLM key actually configured: read `~/.strix/cli-config.json` and confirm `env` holds `STRIX_LLM` plus a
   non-empty `LLM_API_KEY`. Validate the key without ever printing it (reads the key from config, echoes only model IDs):
   `python3 -c "import json,urllib.request; d=json.load(open('/Users/<you>/.strix/cli-config.json')); r=json.load(urllib.request.urlopen(urllib.request.Request('https://api.deepseek.com/v1/models', headers={'Authorization':'Bearer '+d['env']['LLM_API_KEY']}))); print([m['id'] for m in r['data']])"`

## Pitfalls
- Strix "cloud" mode is a different product (own account/token, own models) — don't present it as a
  way to "use the user's own LLM key".
- A resolved model name in an old log does NOT mean the LLM key is persisted. `~/.strix/cli-config.json`
  can be just `{"env": {}}` if the key was only ever exported in a shell session. Before re-running,
  verify the config (or shell env) actually holds `STRIX_LLM` + `LLM_API_KEY`.
- Docker Desktop (current) and OrbStack require macOS 14+; Colima on Intel needs QEMU (brew can't
  compile without Xcode CLT). On an old Intel Mac (macOS 12.x) the realistic fix is usually the
  vmnetd restore below, not replacing the runtime.
- `npx skills add usestrix/strix` installs Strix's own 4 SKILL.md consumer skills (penetration-
  testing, managed-pentesting, fix-vulnerabilities, ci-scanning) — separate from this Hermes skill.
- Only scan targets the user is authorized to test.
- A successful run against a LOCAL directory writes artifacts to `<target>/strix_runs/` (inside the repo, NOT `~/strix_runs/` — that's only for runs that fail before mounting). Add `strix_runs/` to `.gitignore`.
- Strix does NOT just report findings on a writable local target — it AUTO-APPLIES its own remediation patches to your source files (e.g. rewrote the SQL validator, added a privilege-revocation migration, edited docker-compose). After a run, ALWAYS `git status`/`git diff` to review what it changed, then commit if the fixes look right. It also may run DB migrations live (e.g. `ALTER ROLE ... NOSUPERUSER`) against the running database.

## After a scan reports vulnerabilities (exit code 2)
See `references/post-scan-remediation.md` for the full follow-through: reviewing Strix's
auto-applied patches, verifying the fix live with curl, the dependency-bump path
(fastapi→starlette, postcss→nanoid, vite→plugin-react), and committing past bandit B324.

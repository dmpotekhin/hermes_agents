---
name: strix-security-scanning
description: Use when running Strix AI pentest scans or configuring it.
---

# Strix Security Scanning

Strix (github.com/usestrix/strix) is an open-source AI penetration-testing CLI. It runs autonomous agents in a Docker sandbox that find and exploit vulnerabilities in a target, producing validated findings with PoCs and remediation guidance. It is NOT a Hermes skill/plugin — it's a separate binary you install and invoke.

## Prerequisites
- **Docker** — the ONLY runtime backend (`STRIX_RUNTIME_BACKEND` accepts exactly `docker`; verified in `strix/runtime/backends.py`). No working Docker daemon = no local scan.
- **An LLM API key.** Strix uses LiteLLM internally (100+ providers), so DeepSeek, OpenAI, Anthropic, OpenRouter, Ollama, etc. all work.

## Install
```bash
curl -sSL https://strix.ai/install | bash   # fetches prebuilt binary to ~/.strix/bin
```
The install script is safe (only downloads from GitHub releases). Add `~/.strix/bin` to PATH (`.zshrc`). Verify: `~/.strix/bin/strix --version`.

If the curl install stalls (large release binary on a slow network), download the archive directly from GitHub releases (`strix-<version>-macos-x86_64.tar.gz`) and extract to `~/.strix/bin/strix`.

## Configure the LLM
Strix reads `~/.strix/cli-config.json` (auto-loaded; chmod 600 since it holds the key):
```json
{ "env": { "STRIX_LLM": "deepseek/deepseek-v4-pro", "LLM_API_KEY": "sk-..." } }
```
Or export per-session: `STRIX_LLM` + `LLM_API_KEY`.

Model format is LiteLLM's `provider/model`:
- **DeepSeek**: `deepseek/deepseek-v4-pro` or `deepseek/deepseek-v4-flash` — the current DeepSeek API exposes these two v4 models, NOT the older `deepseek-chat`/`deepseek-reasoner` names. Verify the key + models first: `curl https://api.deepseek.com/v1/models -H "Authorization: Bearer <key>"`.
- OpenAI `openai/gpt-5.4`, Anthropic `anthropic/claude-...`, OpenRouter `openrouter/...`, local `ollama/<model>` + `LLM_API_BASE`.

## Run a scan
```bash
strix -n --target <path|url|repo> --scan-mode quick --max-budget 3
```
- Targets: local dir, `https://github.com/org/repo`, live URL, OpenAPI/Swagger `.json/.yaml`, Postman collection.
- `-n` = headless (required for scripts/CI).
- `--scan-mode` = quick | standard | deep.
- `--max-budget` = USD cap on LLM spend (DeepSeek is cheap; $3 is plenty for quick mode).
- First run pulls `ghcr.io/usestrix/strix-sandbox` — a large image; slow on constrained networks. Run in the background (`terminal background=true, notify_on_complete=true`) and tee to a log.

## Exit codes (headless)
- `0` clean, `1` fatal error, `2` vulnerabilities found.
- A `0` only means "nothing found in what was analyzed" — check `strix_runs/<run>/run.json` (`status`, `llm_usage.cost` vs budget) before declaring a run clean.

## Artifacts
Written to `strix_runs/<run-name>/`: `penetration_test_report.md`, `vulnerabilities/*.md`, `vulnerabilities.json`, `findings.sarif` (SARIF 2.1.0), `run.json`.

## Pitfalls
- **A local-directory target is mounted into the sandbox LIVE and WRITABLE** — the agent edits your real files (`.git` excepted). Commit or stash first.
- After editing `.zshrc` to add `~/.strix/bin`, the current shell session won't have `strix` on PATH — use the full path or open a new shell.
- The DeepSeek key is used ONLY by the local CLI. The managed cloud (app.strix.ai) uses its own models + a separate account/API token, and it cannot reach localhost apps (only public repos/URLs). Don't conflate the two.
- On old/Intel Macs Docker Desktop can break in specific ways — see the repair reference below.

## References
- `references/docker-desktop-macos-repair.md` — fixing Docker Desktop on macOS (missing vmnetd binary, corrupted VM disk, elevated commands via osascript).

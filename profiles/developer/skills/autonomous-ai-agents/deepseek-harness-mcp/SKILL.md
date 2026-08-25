---
name: deepseek-harness-mcp
description: Install, run, wire DeepSeek Harness MCP server into Hermes.
---

# DeepSeek Harness MCP (dsh-harness-mcp-server)

Expose DeepSeek Harness agent capabilities as an MCP server so an external MCP client (Hermes) can delegate coding tasks. Hermes = brain, Harness = arms.

## Key facts
- `deepseek-harness` on npm is a RESERVED PLACEHOLDER, not the CLI. The real CLI is `@deepseek-ai/dsh` (bin: `dsh`).
- The MCP plugin `@chushixixin/dsh-harness-mcp-server` is NOT a standalone server. It is a Cordis plugin loaded INSIDE the Harness `web` profile; it starts a StreamableHTTP MCP server on `127.0.0.1:8090`.
- Exposed tools: `echo`, `harness_list_tools`, `agent_run`, `task_inbox`, `task_result`, `rename_session`, `attach_session`.
- SECURITY: binds 127.0.0.1 only and is UNAUTHENTICATED REMOTE CODE EXECUTION. Never bind 0.0.0.0 / expose to LAN/internet without auth + TLS + reverse proxy.

## Install
1. Node >= 22 required (see Pitfalls — macOS default node v14 breaks dsh).
2. `npm install -g @deepseek-ai/dsh@0.1.0-rc.8` — installs cleanly. Versions 0.1.1-rc.1/rc.2 FAIL with E404 on unpublished `@deepseek-ai/dsh-paths` (re-check if DeepSeek later publishes it; otherwise rc.8 stays the ceiling).
3. `npm install -g @chushixixin/dsh-harness-mcp-server --legacy-peer-deps` — its dep tree has peers referencing the unpublished `dsh-paths`; `--legacy-peer-deps` skips peer auto-install.
4. pnpm: `corepack enable` (`dsh plugin` needs pnpm on PATH).
5. Install the plugin INTO the web profile — global install alone is NOT enough (profile boots from `~/.dsh/profiles/web` and resolves packages relative to it):
   `dsh plugin --profile web add @chushixixin/dsh-harness-mcp-server`
   This writes the plugin into `~/.dsh/profiles/web/package.json` under `dsh.profile.bundles` — that IS the registration.
6. Fix the missing `@deepseek-ai/dsh-paths` runtime dep (required by dsh-agent-presets at load):
   `cd ~/.dsh/profiles/web && pnpm add "@deepseek-ai/dsh-paths@npm:@deepseek-ai/dsh-home-paths@0.0.1-rc.3"`
   `@deepseek-ai/dsh-home-paths` is the published equivalent (exports `expandHomePath`, which dsh-agent-presets imports).

## Run
```
export PATH="$HOME/.nvm/versions/node/v22.23.2/bin:$PATH"   # node>=22
set -a && source ~/.hermes/.env && set +a                   # DEEPSEEK_API_KEY etc.
dsh --profile web --no-open
```
- Plugin defaults: port 8090, host 127.0.0.1 (hardcoded).
- Do NOT also pass `--patch cordis.yml` when the plugin is already bundle-registered → `duplicate loader entry id` error. `--patch` is only for plugins installed but not registered.

## Verify
1. `lsof -nP -iTCP:8090 -sTCP:LISTEN` — node process should listen on 127.0.0.1:8090.
2. StreamableHTTP needs session affinity: capture the `Mcp-Session-Id` response header from `initialize`, then send it on later calls. Without it: `{"error":{"code":-32000,"message":"Bad Request: Server not initialized"}}`. See references/troubleshooting.md for a copy-paste probe.

## Wire into Hermes (MCP client)
```
printf 'n\nY\n' | hermes mcp add harness_plugin --url http://127.0.0.1:8090/mcp
```
- `n` = no auth, `Y` = enable all tools. Saved to `~/.hermes/profiles/developer/config.yaml` as `harness_plugin: {url, enabled: true}`. Tools appear in NEW sessions (current session's toolset is already loaded).

## Restart
Kill the dsh/node process on :8090, then re-run the Run block exactly (env + profile boot). Keep the cordis patch file at `~/dsh-harness/cordis.yml` if you ever boot a non-registered plugin.

## Pitfalls
- `ERR_UNKNOWN_BUILTIN_MODULE: No such built-in module: node:timers/promises` → the `node` resolved by PATH is <15 (macOS default is v14.21.3 via /usr/local/bin). Fix: prepend an nvm node >=22 bin dir to PATH. dsh rc.8 also warns EBADENGINE on node 20 (commander wants >=22.12, pi-ai >=22.19) — use 22.
- npm E404 `@deepseek-ai/dsh-paths` → latest dsh rc line is unpublishable from public npm; pin 0.1.0-rc.8.
- `ERR_MODULE_NOT_FOUND ... imported from /Users/<user>/.dsh/profiles/web/` → plugin not in the profile dir. Global install alone does not help: ESM resolution walks up from the PROFILE dir, never reaching the global node_modules root. Run `dsh plugin --profile web add ...`.
- `duplicate loader entry id: harness-mcp-server` → plugin registered twice (bundle + `--patch` overlay). Drop the `--patch`.
- `dsh: pnpm not found on PATH` → run `corepack enable` (creates pnpm shim in the active node bin dir).
- npm global installs land in the ACTIVE node root (`~/.nvm/versions/node/<ver>/lib/node_modules`). Install dsh AND the plugin under the SAME node version, and run dsh with that same node on PATH, or module resolution splits across roots. Background terminal processes inherit the PATH of the shell that spawned them — re-export PATH in the launch command itself.

## Support files
- references/troubleshooting.md — error → cause → fix table with exact transcripts and a copy-paste MCP verification probe.

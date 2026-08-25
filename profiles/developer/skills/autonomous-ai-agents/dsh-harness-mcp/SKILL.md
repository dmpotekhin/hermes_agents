---
name: dsh-harness-mcp
description: Use when running DeepSeek Harness MCP server (dsh, :8090).
---

# DeepSeek Harness MCP Server (dsh-harness-mcp-server)

DeepSeek Harness exposes its agent tools over StreamableHTTP MCP on `127.0.0.1:8090` via the Cordis plugin `@chushixixin/dsh-harness-mcp-server`. In Hermes it is registered as MCP server `harness_plugin` (7 tools: echo, harness_list_tools, agent_run, task_inbox, task_result, rename_session, attach_session).

## Quick start (server down / restart)

```bash
export PATH="$HOME/.nvm/versions/node/v22.23.2/bin:$PATH" && set -a && source ~/.hermes/.env && set +a && dsh --profile web --no-open
```

Run in background; wait ~15-25 s; verify with curl (see Verification). Or use the bundled script: `scripts/start_dsh_harness.sh`.

## Prerequisites (this machine)

- **node >= 22** — use nvm `v22.23.2`. Default `node` in PATH is `v14.21.3`, which BREAKS dsh (no `node:timers/promises`). Always export the nvm path first.
- `DEEPSEEK_API_KEY` lives in `~/.hermes/.env` (source it).
- `pnpm` via `corepack enable` (needed for `dsh plugin`).
- Installed global (root node22): `@deepseek-ai/dsh@0.1.0-rc.8`, `@chushixixin/dsh-harness-mcp-server` (`/Users/dmitrypotekhin/.nvm/versions/node/v22.23.2/lib/node_modules/`).
- Profile `~/.dsh/profiles/web/` already has the plugin + dsh-paths alias.

## One-time install (fresh machine)

1. `npm install -g @deepseek-ai/dsh@0.1.0-rc.8` — do NOT take latest: `@deepseek-ai/dsh@0.1.1-rc.2` depends on `@deepseek-ai/dsh-paths@^0.0.1-rc.1`, which is NOT in the public npm registry (broken release, E404).
2. `npm install -g @chushixixin/dsh-harness-mcp-server --legacy-peer-deps` — the `--legacy-peer-deps` flag is required; otherwise npm fails on the missing peer `@deepseek-ai/dsh-paths`.
3. `corepack enable` then `dsh plugin --profile web add @chushixixin/dsh-harness-mcp-server` — installs the plugin INTO the profile (`~/.dsh/profiles/web/node_modules/`). The plugin is resolved relative to the profile, NOT globally; `dsh plugin add` writes its own registration into the profile's cordis.yml (no need for a custom `--patch`).
4. Runtime alias fix (dsh-agent-presets does `import { expandHomePath } from '@deepseek-ai/dsh-paths'`):
   ```bash
   cd ~/.dsh/profiles/web && pnpm add "@deepseek-ai/dsh-paths@npm:@deepseek-ai/dsh-home-paths@0.0.1-rc.3"
   ```
   `dsh-home-paths` is the renamed package and exports `expandHomePath`.

## Register with Hermes (MCP client)

```bash
hermes mcp add harness_plugin --url http://127.0.0.1:8090/mcp
```

Tools become available in NEW sessions (MCP servers reload: `hermes mcp list` / session restart). Server entry is saved in `~/.hermes/profiles/developer/config.yaml`.

## Verification

Port listening: `lsof -nP -iTCP:8090 -sTCP:LISTEN`

MCP handshake (session-based StreamableHTTP — later calls MUST carry the session id, else `Bad Request: Server not initialized`):

```bash
# 1. initialize → capture Mcp-Session-Id response header
curl -s -D /tmp/hdr.txt -o /tmp/init.json -X POST http://127.0.0.1:8090/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"hermes","version":"1"}}}'
SID=$(awk 'tolower($1)=="mcp-session-id:"{print $2}' /tmp/hdr.txt | tr -d '\r')
# 2. tools/list with session
curl -s -X POST http://127.0.0.1:8090/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -H "Mcp-Session-Id: $SID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

## Pitfalls

- Default node v14 → dsh crashes at startup (ESM + missing `node:timers/promises`). Always use node 22.
- `@deepseek-ai/dsh@0.1.1-rc.2` is a broken release (depends on unpublished `@deepseek-ai/dsh-paths`) → pin `0.1.0-rc.8`.
- Installing the plugin globally is NOT enough — `dsh` looks for plugins inside the active profile. Use `dsh plugin --profile web add ...`.
- Do NOT pass a custom `--patch cordis.yml` duplicating the plugin registration — `dsh plugin add` already registers it; duplicate config caused the server to silently not bind 8090.
- Plugin defaults are already `http: true, port: 8090, host: 127.0.0.1` — no config change needed.
- `dsh web --help` in rc.8 shows only UI; `--patch`/`--no-open` are launcher options (`dsh --help`).

## Security

- Server binds 127.0.0.1 ONLY and has NO auth — it is an unauthenticated RCE surface. Never expose port 8090 externally, never proxy it without auth.
- `DEEPSEEK_API_KEY` is loaded from `~/.hermes/.env` — never print it.

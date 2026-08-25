# DeepSeek Harness MCP — troubleshooting reference

Verified 2026-08-24 on macOS 12.7.6 (node via nvm). Exact error → cause → fix.

## npm E404: @deepseek-ai/dsh-paths not found
```
npm error 404 Not Found - GET https://registry.npmjs.org/@deepseek-ai/dsh-paths - Not found
```
Cause: `@deepseek-ai/dsh@0.1.1-rc.1` / `0.1.1-rc.2` declare `dependencies: { "@deepseek-ai/dsh-paths": "^0.0.1-rc.1" }` but that package is NOT published to the public npm registry (private or unpublished). `npm search dsh-paths` → empty.
Fix: install the newest clean release:
```
npm install -g @deepseek-ai/dsh@0.1.0-rc.8
```
Check before installing: `npm view @deepseek-ai/dsh@<version> dependencies | grep dsh-paths` (0 hits = clean).
Note: if DeepSeek later publishes dsh-paths, the latest tag may work again — re-verify, don't assume.

## ERR_MODULE_NOT_FOUND: plugin resolved from profile dir, not global root
```
ERR_MODULE_NOT_FOUND: Cannot find package '@chushixixin/dsh-harness-mcp-server' imported from /Users/<user>/.dsh/profiles/web/
```
Cause: the Harness web profile boots from `~/.dsh/profiles/web/`; ESM resolution walks up from THERE, never reaching the global node root (`~/.nvm/versions/node/<ver>/lib/node_modules`). A global `npm install -g @chushixixin/dsh-harness-mcp-server` alone is NOT enough.
Fix: install the plugin INTO the profile (pnpm required — see below):
```
dsh plugin --profile web add @chushixixin/dsh-harness-mcp-server
```
This writes the plugin into `~/.dsh/profiles/web/node_modules/@chushixixin/` AND registers it in `~/.dsh/profiles/web/package.json` under `dsh.profile.bundles` (that registration is what actually loads it).

## ERR_MODULE_NOT_FOUND: @deepseek-ai/dsh-paths at runtime (after boot)
```
ERR_MODULE_NOT_FOUND: Cannot find package '@deepseek-ai/dsh-paths' imported from .../@deepseek-ai/dsh-agent-presets/lib/index.js
```
Cause: `dsh-agent-presets` imports `{ expandHomePath } from "@deepseek-ai/dsh-paths"` at runtime; the peer is unpublished (see first row). pnpm does NOT auto-install peers, so the boot fails.
Fix: alias the published equivalent `@deepseek-ai/dsh-home-paths` under the missing name (API-compatible — it also exports `expandHomePath`):
```
cd ~/.dsh/profiles/web && pnpm add "@deepseek-ai/dsh-paths@npm:@deepseek-ai/dsh-home-paths@0.0.1-rc.3"
```

## pnpm not found
```
dsh: pnpm not found on PATH — install pnpm to manage profile plugins
```
Fix: `corepack enable` (node >= 16.9) creates the pnpm/yarn shims in the ACTIVE node bin dir. Then re-run `dsh plugin ...`.

## duplicate loader entry id
```
TypeError: duplicate loader entry id: harness-mcp-server
```
Cause: plugin registered TWICE — once via `dsh.profile.bundles` (from `dsh plugin add`) and once via `dsh --patch cordis.yml` overlay inserting the same id.
Fix: do NOT pass `--patch` for a plugin already in profile bundles. `--patch` is only for registering a plugin that is installed but NOT bundle-registered.

## MCP probe: "Bad Request: Server not initialized"
```
{"jsonrpc":"2.0","error":{"code":-32000,"message":"Bad Request: Server not initialized"},"id":null}
```
Cause: StreamableHTTP MCP is sessionful. The `initialize` response carries a `Mcp-Session-Id` header; every subsequent request (tools/list, tools/call) must echo it.
Fix (verify with curl):
```
SID=$(curl -s -D - -o /dev/null -X POST http://127.0.0.1:8090/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"probe","version":"1"}}}' \
  | grep -i '^Mcp-Session-Id:' | tr -d '\r' | awk '{print $2}')
curl -s -X POST http://127.0.0.1:8090/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H "Mcp-Session-Id: $SID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

## node version: silent CLI crash / ERR_UNKNOWN_BUILTIN_MODULE
```
ERR_UNKNOWN_BUILTIN_MODULE: No such built-in module: node:timers/promises
```
Cause: `dsh` is an ESM CLI requiring node >= 20 (uses `node:timers/promises`, which does not exist in node 14 — the macOS default). rc.8 on node 20 also prints EBADENGINE warnings for commander >= 22.12 / pi-ai >= 22.19.
Fix: run with nvm node >= 22:
```
export PATH="$HOME/.nvm/versions/node/v22.23.2/bin:$PATH"
```
Diagnose first: `node --version` (if v14.x → the dsh crash is expected), `which node`, `ls ~/.nvm/versions/node/`.

## Global npm installs and nvm roots
`npm install -g` installs into the ACTIVE node root (`~/.nvm/versions/node/<ver>/lib/node_modules`). Mixing versions splits packages across roots: e.g. dsh in node20 root + node22 root, plugin only in node20 root → whichever node you run under, the other package is missing. Install BOTH under the SAME node version, then verify: `npm ls -g --depth=0`.

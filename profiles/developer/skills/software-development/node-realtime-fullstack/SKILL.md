---
name: node-realtime-fullstack
description: Use when building a Node.js full-stack realtime web app.
---

# Node.js Full-Stack Realtime App (Express + Socket.IO + Prisma + React/Vite)

Greenfield monorepo for a realtime web app: Node/Express + Socket.IO backend, Prisma
ORM (SQLite locally, switchable to PostgreSQL), React + Vite + TypeScript + Tailwind
frontend, all served as a single origin in production.

## When to use
- Building an app where multiple users must see changes instantly (rooms, live state).
- CRUD + WebSocket events + a relational DB, local-first.
- A "tool" the team opens in a browser over the LAN or a dedicated IP.

## Version preflight (do this first)
- **Node ≥ 18** required for Vite 5 and Prisma 5. If `node --version` reports 14/16,
  check nvm for a pre-installed modern version BEFORE scaffolding:
  `nvm ls`, then `export PATH="$HOME/.nvm/versions/node/v22.x.x/bin:$PATH"`.
  A stale `node@14` first in `~/.zshrc` is the classic silent cause of Vite/Prisma
  install-and-run failures. Re-export PATH in every subsequent terminal call (or the
  session may fall back to the old node).
- Verify `npm --version` resolves from the SAME node you picked (npm bundled with
  node 20/22, not the old `npm@6` from `/usr/local/bin`).

## Project layout
```
server/   package.json (type:module)  src/{index,config,prisma}.ts  src/{routes,socket,data,games}/
client/   package.json  src/{main,App,api,socket,store}.tsx  src/{pages,components}/
```
Keep backend and frontend as two independent `package.json` folders (no npm
workspaces — hoisting breaks Vite/Prisma). A root `package.json` holds `concurrently`
for `npm run dev` and a `setup` script (install → prisma generate/migrate → seed).

## Backend patterns
- **Run TS with `tsx`, not a tsc build.** Set `"type": "module"` + tsconfig
  `module: "ESNext"`, `moduleResolution: "Bundler"`, `noEmit: true`. This lets you
  write relative imports WITHOUT `.js` extensions and avoids the NodeNext extension
  hell. Use `tsx watch src/index.ts` for dev and `tsx src/index.ts` for prod
  (skip a separate build step — fine at this scale).
- **Prisma + SQLite**: `createMany` works on SQLite only from Prisma 5.12+. Store
  structured data (sector lists, dice faces, drawn cards) as `String` with
  `JSON.stringify`/`JSON.parse` — 100% portable to PostgreSQL and independent of
  Prisma `Json` support. Prisma CLI auto-loads `.env` from the schema/cwd dir, so
  `DATABASE_URL="file:./dev.db"` resolves relative to `prisma/`.
- **`.env` flow**: commit `.env.example`, gitignore `.env`; make `setup` copy it:
  `cp -n server/.env.example server/.env`.

## Frontend patterns (the key trick)
- **Use relative URLs everywhere + a Vite proxy.** In `vite.config.ts`:
  ```ts
  server: {
    host: '0.0.0.0',
    proxy: {
      '/api':       { target: 'http://localhost:3000', changeOrigin: true },
      '/socket.io': { target: 'http://localhost:3000', ws: true, changeOrigin: true },
    },
  }
  ```
  The client then calls `fetch('/api/...')` and `io()` (no URL), and it works
  unchanged in dev (proxied) and prod (same origin). No CORS config, no hardcoded
  host/IP — this is the single highest-leverage decision for LAN-deployable apps.
- `socket.io-client`: `io({ transports: ['websocket','polling'] })` connects to the
  current origin; the Vite `ws:true` proxy carries the WebSocket to the backend.
- In production the backend serves `client/dist` as static + SPA fallback:
  ```ts
  if (fs.existsSync(clientDist)) {
    app.use(express.static(clientDist));
    app.get('*', (req,res,next) => req.path.startsWith('/api') ? next() : res.sendFile(join(clientDist,'index.html')));
  }
  ```
  Put this check at startup — build the client BEFORE starting the server, or the
  static block won't register (restart to pick up a late build).

## Realtime patterns
- Room naming: `team:<teamId>` for team broadcasts, `game:<code>` for per-game rooms.
- **Server-authoritative randomness.** Compute results (tarot cards, wheel sector,
  dice face, icebreaker) on the server and broadcast to the room — everyone sees the
  same result; never let each client roll its own.
- **Mini-game engine = in-memory reducers.** A `games/manager.ts` holding a
  `Map<roomId, GameState>` with `createGame(type)` (initial state) and
  `applyAction(roomId, action, payload)` (reducer). New game = one type + one
  `createGame` branch + one reducer branch + one frontend page. See
  `references/realtime-patterns.md`.
- **Rooms are lost on reconnect — re-join on `connect`.** Socket.IO room membership
  is per-connection and silently vanishes when the socket reconnects. Don't emit
  `joinRoom` only once on mount; re-emit it whenever the socket (re)connects:
  ```ts
  useEffect(() => {
    if (!teamId) return;
    const join = () => socket.emit('joinRoom', { teamId });
    join();                       // immediate
    socket.on('connect', join);   // after reconnect
    return () => {
      socket.off('connect', join);
      socket.emit('leaveRoom', { teamId });
    };
  }, [teamId]);
  ```
  Without this, a dropped + reconnected socket leaves clients missing every realtime
  event (wheel spin, tarot draw, …) with no error — a classic "nothing happens" bug.

## Verification (required before "done")
- REST: `curl`/urllib each endpoint, including a POST round-trip (create → read).
- Socket: write a throwaway `.mjs` that connects with `socket.io-client`, emits, and
  asserts responses. **Put the script in the directory where `socket.io-client` is
  installed** (e.g. `client/`), because `NODE_PATH` does NOT apply to ESM imports —
  node resolves `import 'socket.io-client'` relative to the importing file's tree.
- Production: build client, restart server, then `curl` `/` (200 html), a deep route
  like `/tarot` (SPA fallback 200), and `/api/health`.

## Multi-user realtime verification (Playwright MCP)
- **Never test two users via two browser tabs** — tabs of one Playwright context
  SHARE `localStorage`, so logging out in tab B wipes tab A's token and Alice
  silently resets to the login screen. Use `browser_run_code_unsafe` to spawn an
  ISOLATED context for the second user inside one call:
  ```js
  async (page) => {
    const ctx2 = await page.context().browser().newContext(); // isolated storage
    const page2 = await ctx2.newPage();
    // login user B, open shared page, type; then inspect user A's `page` DOM
  }
  ```
  Contexts do NOT persist across `browser_run_code_unsafe` calls — create the
  context AND do all cross-user assertions in ONE invocation. Read the other
  user's state via `page.evaluate(innerText/querySelectorAll)` without reloading
  (a reload drops the socket wiring until the effect re-runs).
- **Presence ≠ cursor ≠ edit: verify each path separately.** Presence (`page:join`
  → avatar chip) can work while cursor:move and page:edit don't. Client emits
  `cursor:move` on editor selection change (NOT on every keystroke), `page:edit`
  on `onUpdate`; receiver applies `setContent` behind an `isRemote` ref so it
  doesn't re-broadcast. If events don't arrive, diff the payload shape first
  (server `createdBy` vs client `user` etc.) before suspecting socket plumbing.
- **Lost test-user password mid-session:** reset it directly via a Prisma script
  (bcryptjs hash + `user.update`) — faster than hunting the old password.
- **Zombie browsers from a previous session break realtime experiments.** A headless
  MCP/Playwright Chrome left running from an earlier session (`--user-data-dir=...ms-playwright-mcp/...`)
  still holds a live socket with a stale page state, injects its own `page:edit`
  traffic, and can be the "mystery client" that keeps an echo loop alive — or drowns
  real events so they appear "not delivered". Before any two-client realtime test:
  `ps aux | grep mcp-chrome`, `lsof -i :<port> | grep ESTABLISHED`, and kill stale
  browsers (kill by PID from the `--user-data-dir` line).
- **Debug realtime loops server-side, then client-side.** Start the server with
  `DEBUG='socket.io:*'` — every `got packet` / `emitting event` / `dispatching` is
  logged with the payload. An echo loop shows as a burst of 10-20 identical events
  in <100ms that never stops; a healthy app shows one event per user action. On the
  client, count mutations: attach a `MutationObserver` to `.ProseMirror` before
  typing N characters — healthy ≈ N mutations, loop = 100+.
- **Cursor labels may render the EMAIL, not the name** (e.g. `charlie@ui.test`), so
  assertions matching the display name ('Charlie') give false negatives. Check for
  the email string too, or read what the component actually passes as the label.

For a collaborative doc app (auth + sharing + TipTap editor), see
`references/notion-clone-session.md` — data model, permission middleware,
vitest/supertest structure, and the two real bugs (router mount mismatch,
GET/PATCH response shape drift).

## Pitfalls
- **Router mount path must match the router's internal paths.** Mounting
  `app.use('/api', pagesRouter)` where `pagesRouter` defines `/` and `/:id`
  matches only `/api/` and `/api/:id` — NOT `/api/pages`. Auth routes worked while
  every `/api/pages` call returned 404 with an HTML body, which is a confusing
  half-working state. Either mount on the full prefix (`app.use('/api/pages',
  pagesRouter)` with `/`, `/:id` inside) or use full paths (`/pages`, `/pages/:id`)
  inside a router mounted at `/api`. Keep the same convention in the test app
  factory — tests silently 404 for the same reason.
- **Keep GET and PATCH response shapes identical.** In this app GET `/pages/:id`
  returned `role` at the TOP level, PATCH returned `page` WITHOUT `role`, and the
  client read `page.role`. Result: after the first autosave the client state got
  clobbered, `page.role` became undefined, and owner-only buttons (Share/Invite)
  stayed disabled. Every field the client merges from a PATCH must exist in that
  response — or the client must preserve fields it already has
  (`setPage(p => ({ ...p, ...res.page, role: p.role }))`).
- **Watch field-name drift across the whole API surface, not just GET vs PATCH.**
  Same class of bug hit versions/restore: POST `/pages/:id/versions` returned
  `createdBy` while the client's `Version` type reads `user` (crash rendering
  `v.user.name`); restore returned `{ content }` while the client read
  `res.page.content`. Also POST required `content` in the body while the client
  sent only `note` → 400. Fix each side so client type ↔ server payload match
  (`include: { createdBy }` + rename to `user`; wrap restore in `{ page: { content } }`;
  pass editor content from the frontend). When you change a server contract, the
  matching vitest assertion MUST be updated in the same commit
  (`restore.body.page.content`) or the suite fails.
- **TipTap `editor.commands.setContent([])` throws** `RangeError: Unknown node
  type: undefined` when loading a page whose content is an empty array. Guard:
  `setContent((Array.isArray(c) && c.length > 0 ? c : [{ type: 'paragraph' }]) as never)`.
- **An `isRemote` ref alone does NOT stop edit echo loops.** `editor.commands.setContent()`
  fires `onUpdate` ASYNCHRONOUSLY (after dispatch, next tick), so
  `isRemote.current = true; setContent(...); isRemote.current = false;` is useless —
  by the time `onUpdate` runs, the flag is already false and the client re-broadcasts.
  Two clients → infinite `page:edit` avalanche (100+/sec of identical content) that
  makes cursors/live text appear "not delivered" and clobbers typing. Fix = content
  comparison on BOTH sides:
  ```ts
  // onUpdate: skip re-sending what we already sent
  if (lastSentRef.current && JSON.stringify(lastSentRef.current) === JSON.stringify(content)) return;
  lastSentRef.current = content;
  // page:edit handler: skip applying identical content (setContent would re-fire onUpdate)
  if (JSON.stringify(editor.getJSON().content ?? []) === JSON.stringify(payload.content)) return;
  ```
  Reset `lastSentRef.current = null` when loading a new page. See
  `references/realtime-editor-echo-loop.md` for the full diagnosis + probe script.
- `once('event')` in a socket test captures the FIRST of several broadcasts. When a
  client emits two sequential actions (e.g. `correct` then `next`) that each broadcast
  a new state, attach the listener BEFORE emitting and read the LAST received state,
  or count expected events — otherwise you assert against an intermediate state.
- Server `createMany`/nested `create` both fine on SQLite (Prisma 5.12+).
- Keep `server/prisma/migrations/` committed, but gitignore `*.db*` — the SQLite file
  itself must never enter git.
- **Framer Motion: rotate an HTML wrapper, not an SVG `<g>` with px-string origin.**
  `style={{ originX: '150px', originY: '150px' }}` on a `motion.g` does NOT work —
  Framer Motion's `originX`/`originY` expect 0–1 fractions, so the SVG rotates around
  its own origin (0,0) and the animation breaks or does nothing. Rotate a `motion.div`
  wrapper around its center and keep any pointer as a separate non-rotating overlay:
  ```tsx
  <div className="relative h-72 w-72">
    <motion.div className="absolute inset-0"
      animate={{ rotate }} style={{ transformOrigin: '50% 50%' }}>
      <svg viewBox="0 0 300 300">…</svg>
    </motion.div>
    <div className="absolute left-1/2 top-0 -translate-x-1/2">▲</div>
  </div>
  ```
  Compute the landing angle inside `setRotation(r => …)` (functional updater), not
  from a captured `rotation` value, so repeated spins accumulate correctly.
- **Verifying animation via Playwright MCP:** `getComputedStyle(el).transform` and
  `.rotate` report `"none"` while Framer Motion is animating — v11 writes the live
  transform to the inline `style` attribute (`transform: rotate(5970deg)`), so read
  `el.getAttribute('style')` instead. Also target the EXACT animated element: a loose
  selector (any ancestor of the SVG) matches a wrapper that has no transform of its
  own and misleads you into "nothing is animating". Use a precise selector like
  `.absolute.inset-0` or an id, not a parent that merely contains the SVG.

# Notion-clone session notes (collab doc app: auth, sharing, realtime editor)

Worked example from a session building a Notion-like collaborative document app on
the node-realtime-fullstack stack. Supplements the SKILL.md pitfalls with the
data model, test structure, and the debugging path for the two bugs.

## Data model (Prisma, SQLite)

- `User` — email/password, `bcryptjs` (NOT `bcrypt` — pure-JS, no native build;
  this machine has no Xcode CLT so native node-gyp deps fail).
- `Page` — `title`, `icon`, `parentId` (self-relation for the sidebar tree),
  `ownerId`, `content` stored as `String` (JSON.stringify of the TipTap document
  array) — same portable pattern as the skill recommends for structured data.
- `Share` — `pageId_userId` compound unique, `role` enum `editor|viewer`.
  Owner is NOT a Share row; owner access is `page.ownerId === userId`.
- `Comment` — `pageId`, `blockId` (TipTap node id), `text`, `userId`.
- `Version` — snapshot of `content` + `note`, for history/restore.

## Permission middleware pattern

```ts
getPageRole(pageId, userId) → 'owner' | 'editor' | 'viewer' | null
requirePageAccess  // any role, sets req.pageRole
requirePageEdit    // owner|editor
requirePageOwner   // owner only
```
Stick to this three-tier access model for any doc-app: read / edit / own.

## Testing structure (vitest + supertest + socket.io-client)

- `tests/api.test.ts` — build the Express app IN the test via a `makeApp()`
  factory (import the routers directly, no listen). Supertest against the factory.
  Register users in `beforeAll`, log in (don't re-register — 409) for later blocks.
- `tests/socket.test.ts` — create a real `http.Server` on an ephemeral port,
  attach `Server(io)` with the same JWT auth middleware as prod, connect
  `socket.io-client` from `server/node_modules` (installed as devDependency; the
  ESM resolution note in SKILL.md applies), assert broadcast events.
- Debug scripts (`/tmp/nc-debug.ts` run with `tsx`) instead of inline
  `python3 -c` in curl pipelines — inline python in a `terminal` call trips a
  consent prompt that stalls; a script file runs clean.

## Bug 1 — half-mounted router (all /api/pages → 404 with HTML body)

Symptom: `/api/auth/*` worked, every `/api/pages*` call returned 404.
Root cause: `app.use('/api', pagesRouter)` + `router.get('/')`/`router.get('/:id')`
matches `/api/` and `/api/:id`, never `/api/pages`. Other routers (shares,
comments, versions) used full `/pages/...` paths inside, so they were fine — the
inconsistency made the bug look like it was in pages.ts.
Fix: `app.use('/api/pages', pagesRouter)`. Also fix the same line in the test's
`makeApp()` — the tests reproduce the exact production routing.

## Bug 2 — disabled owner-only buttons after first autosave

Symptom: Share dialog Invite button `disabled`, even for the page owner.
Root cause: GET `/pages/:id` returned `role` top-level; PATCH returned `page`
without `role`; `setPage(p => ({ ...p, ...res.page }))` dropped `role` → became
undefined → `role !== 'owner'` disabled the button. Fixed on both sides:
server returns `role` inside `page` on GET and PATCH; client preserves `p.role`.

## Bug 3 — versions/restore: three contract-drift failures in one feature

Found during UI verification of the History panel (Playwright). All three were
client-type vs server-payload mismatches, not socket/DB problems:

1. **POST /versions → 400.** Server validated `content` in the body; client sent
   only `note`. Fix: client passes editor content
   (`createVersion(pageId, getContent?.())`), VersionsPanel gets a `getContent`
   prop from Editor (`editor.getJSON().content`).
2. **Snapshot rendered → crash `v.user.name`.** Server's POST response returned
   `createdBy`, client's `Version` type reads `user`. Fix: `include: { createdBy }`
   in the create + rename to `user` in the map; client guards
   `v.user?.name || v.user?.email || 'Unknown'`. The GET list had the same
   `createdBy` vs `user` mismatch.
3. **Restore → crash `res.page.content` undefined.** Server restore returned
   `{ content }`; client read `res.page.content`. Fix: server wraps as
   `{ page: { content } }`; vitest assertion updated to
   `restore.body.page.content` (suite was red until the test was updated — the
   contract change and test change must land together).

Lesson: for every new endpoint, diff the client's TypeScript interface against
the server's response shape BEFORE wiring UI — and re-run the API suite after
any server contract change.

## TipTap realtime wiring notes

- Empty page content is `[]`; `setContent([])` throws — fall back to
  `[{ type: 'paragraph' }]`.
- `isRemote` ref pattern: set true around programmatic `setContent` so `onUpdate`
  doesn't echo server-loaded content back to the socket room.
- Presence: `page:join` / `page:leave` rooms `page:<id>`, server broadcasts the
  user list on join; client tracks `presence` for avatar chips and assigns colors
  by index. Cursors are `{ userId, blockId, pos }` broadcast to the room.

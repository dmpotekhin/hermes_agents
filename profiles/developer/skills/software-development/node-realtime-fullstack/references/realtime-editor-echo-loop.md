# Realtime editor echo loop (TipTap/ProseMirror + Socket.IO)

Diagnosed on the notion-clone app (Express + Socket.IO + TipTap v2 + React 18).

## Symptom
- Presence works (avatars appear), but cursor:move and page:edit seem "not delivered":
  typing in browser B never shows in browser A, or appears with a long delay.
- Server `DEBUG='socket.io:*'` log shows a never-ending burst of identical
  `page:edit` events (10-20+ per 100ms) with the SAME content, from every client.
- Client `onUpdate` fires constantly with `isRemote = false` even though the user
  typed nothing.

## Root cause
`editor.commands.setContent(content)` fires the Tiptap `onUpdate` callback
ASYNCHRONOUSLY (after the ProseMirror dispatch, on a later tick). The classic
guard is synchronous:

```ts
isRemote.current = true;
editor.commands.setContent(payload.content);
isRemote.current = false;
```

By the time `onUpdate` actually runs, `isRemote` is already `false`, so the client
re-broadcasts the content it just received. With two clients:

1. A loads page → `setContent` → async `onUpdate` (isRemote false) → emit → B
2. B receives → `setContent` → async `onUpdate` → emit → A
3. …forever, even when the content is byte-identical.

The avalanche also clobbers concurrent typing (last-write-wins races lose
characters: "REALTIME-CHECK" arrives as "REALTME-"), which looks like yet another
realtime bug.

## Fix (both sides)
```ts
// 1. onUpdate: never re-send what we already sent
onUpdate: ({ editor }) => {
  if (isRemote.current) return;
  const content = (editor.getJSON().content ?? []) as unknown[];
  if (lastSentRef.current && JSON.stringify(lastSentRef.current) === JSON.stringify(content)) return;
  lastSentRef.current = content;
  socket.emit('page:edit', { pageId, content });
};

// 2. page:edit handler: skip applying identical content (setContent would re-fire onUpdate)
socket.on('page:edit', (payload) => {
  if (payload.pageId !== pageId || payload.by === user.id) return;
  if (JSON.stringify((editor.getJSON().content ?? []) as unknown[]) === JSON.stringify(payload.content)) return;
  isRemote.current = true;
  editor.commands.setContent(payload.content);
  isRemote.current = false;
});
```
Reset `lastSentRef.current = null` when loading a new page (otherwise the guard
can suppress the first legitimate send of a page whose content equals the last
one sent).

After the fix a two-client session produces exactly ONE `page:edit` per user
action (plus the initial load emit), then silence.

## Probe script pattern (two isolated clients)
Standalone Playwright script (NOT MCP tabs — tabs share localStorage). Launch
with the exact Chrome for Testing binary from the ms-playwright cache when the
bundled playwright revision is missing:

```ts
const CHROME = process.env.HOME + '/Library/Caches/ms-playwright/chromium-<rev>/chrome-mac-x64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing';
const browser = await chromium.launch({ headless: true, executablePath: CHROME });
const ctxA = await browser.newContext();
const ctxC = await browser.newContext();
```
Run with `NODE_PATH=<path to npx-cache node_modules>` + `npx tsx script.ts`.

Typing probe (health = N chars → ~N mutations):
```ts
await alice.evaluate(() => {
  (window as any).__muts = 0;
  const el = document.querySelector('.ProseMirror');
  if (el) {
    const mo = new MutationObserver(() => { (window as any).__muts++; });
    mo.observe(el, { childList: true, subtree: true, characterData: true });
  }
});
for (const ch of 'X9Q7Z') { await charlie.keyboard.type(ch); await charlie.waitForTimeout(300); }
const muts = await alice.evaluate(() => (window as any).__muts);
// muts ≈ 5 → healthy; muts > 50 → echo loop is back
```

## Verification gotchas
- Check presence, cursor, and edit as SEPARATE assertions — they use different
  socket events and can independently break.
- Cursor labels may show the email (`charlie@ui.test`) instead of the name —
  assert on both.
- Kill zombie headless browsers before the test:
  `ps aux | grep mcp-chrome`, `lsof -i :3000 -P | grep ESTABLISHED`.
- If the server was started WITHOUT DEBUG (an old process still owns the port),
  `kill <pid>` first, then restart with `DEBUG='socket.io:*'` so the loop is
  visible in the process log.

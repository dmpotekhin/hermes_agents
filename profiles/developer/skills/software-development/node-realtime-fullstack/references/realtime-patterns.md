# Realtime patterns (worked example: Agile Oracle)

Concrete snippets distilled from a working Express + Socket.IO + Prisma build.

## Socket.IO client singleton (shared, same-origin)
```ts
// client/src/socket.ts
import { io, Socket } from 'socket.io-client';
export const socket: Socket = io({ autoConnect: true, transports: ['websocket', 'polling'] });

// hook with auto-unsubscribe
export function useSocketEvent(event: string, handler: (data: any) => void) {
  useEffect(() => {
    socket.on(event, handler);
    return () => { socket.off(event, handler); };
  }, [event, handler]);
}
```

## Room join on team select (React store)
```tsx
useEffect(() => {
  if (teamId) socket.emit('joinRoom', { teamId });
  return () => { if (teamId) socket.emit('leaveRoom', { teamId }); };
}, [teamId]);
```

## Server: authoritative draw + broadcast (tarot example)
```ts
socket.on('drawTarot', async ({ sprintId, count }) => {
  const keys = shuffle([...Array(22).keys()]).slice(0, count);
  const reading = await prisma.tarotReading.create({
    data: { sprintId, cards: JSON.stringify(keys) },
  });
  const sprint = await prisma.sprint.findUnique({ where: { id: sprintId } });
  io.to(`team:${sprint.teamId}`).emit('tarotDrawn', { sprintId, cards, count });
});
```

## Mini-game engine shape (in-memory reducers)
```ts
// server/src/games/manager.ts
const store = new Map<string, GameState>();

export function createGame(type: GameType): GameState {
  switch (type) {
    case 'alias':    return { type:'alias', words, index:0, scores:{a:0,b:0}, turn:'a', ... };
    case 'codenames': return { type:'codenames', words, colors, turn:'red', revealed:[], ... };
    // ...
  }
}

export function applyAction(roomId: string, action: string, payload: any): GameState | null {
  const state = store.get(roomId);
  if (!state) return null;
  switch (state.type) {
    case 'codenames':
      if (action === 'reveal') { /* mark, switch turn, check win */ store.set(roomId, next); return next; }
      // ...
  }
}
```
Socket layer just relays: `gameCreate` → `saveGame(roomId, createGame(type))`,
`gameAction` → `applyAction(...)` then `io.to(roomId).emit('gameState', state)`.

## Socket smoke test (throwaway, run from client/ where socket.io-client lives)
```js
// smoke.mjs — place in client/ so `import 'socket.io-client'` resolves
import { io } from 'socket.io-client';
const s = io('http://localhost:3000', { transports: ['websocket'] });
await new Promise(r => s.on('connect', r));
// fetch ids via REST first, then:
await new Promise(res => { s.once('tarotDrawn', d => { /* assert */ res(); }); s.emit('drawTarot', { sprintId, count: 2 }); });
s.close(); process.exit(0);
```
Run: `node smoke.mjs` (with modern node in PATH). Key: the script MUST sit in the
folder that has `socket.io-client` in its `node_modules` — `NODE_PATH` is ignored by
ESM resolution, so pointing it at another folder's node_modules silently fails.

## Prisma schema notes (SQLite + portable JSON)
```prisma
model Wheel {
  id       String @id @default(cuid())
  teamId   String
  team     Team   @relation(fields: [teamId], references: [id], onDelete: Cascade)
  name     String
  sectors  String // JSON array of {label,color} — stored as String for portability
}
```
Read back with a `parseJson(s, fallback)` helper (JSON.parse in try/catch). This
avoids relying on Prisma `Json` scalar support and makes the same schema work on
PostgreSQL unchanged.

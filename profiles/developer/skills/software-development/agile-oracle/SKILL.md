---
name: agile-oracle
description: Work on the agile-oracle project (Agile Oracle) full-stack.
version: 1.0.0
platforms: [macos]
metadata:
  hermes:
    tags: [agile-oracle, node, express, socket-io, prisma, react, vite, fullstack]
    related_skills: [node-realtime-fullstack, web-audio-sound-effects, native-project-deployment]
---

# Agile Oracle

Интерактивный инструмент для Agile-команд (таро, колесо фортуны, кости, ледоколы, ретро, покер, игротека мини-игр). Реалтайм-мультиплеер через Socket.IO — изменения видят все в комнате.

## Project / repo
- Локально: `/Users/dmitrypotekhin/projects/agile-oracle`
- GitHub: `dmpotekhin/agile-oracle` (SSH `git@github.com:dmpotekhin/agile-oracle.git`, ветка `master`)

## Architecture
- **client/** — React 18 + Vite 5 + TypeScript + Tailwind (тема `mystic-*`) + framer-motion + socket.io-client.
- **server/** — Node + Express + TypeScript (запуск через `tsx watch`) + Socket.IO + Prisma ORM.
- **DB** — SQLite `server/prisma/dev.db` (переключение на PostgreSQL описано в README).
- Vite dev-сервер на `:5173` проксирует `/api` и `/socket.io` на бэкенд `:3000`. В prod бэкенд раздаёт `client/dist` на `:3000`.

## CRITICAL — версия Node
- Vite 5 и tsx требуют Node ≥18. Системный `node` на этой машине — v14 и ломает `vite build` ошибкой `SyntaxError: Unexpected token '??='` (UnhandledPromiseRejectionWarning).
- Перед ЛЮБОЙ npm-командой: `export PATH="$HOME/.nvm/versions/node/v20.20.0/bin:$PATH"` (в nvm есть v20 и v22).
- `tsc --noEmit` может пройти на старом node, а `vite build` упадёт — гоняй ОБА шага.

## Run (dev)
```bash
export PATH="$HOME/.nvm/versions/node/v20.20.0/bin:$PATH"
cd ~/projects/agile-oracle
npm --prefix server run dev     # бэкенд :3000 (tsx watch, авто-рестарт)
npm --prefix client run dev     # фронт :5173 (vite, HMR)
```
- Health: `curl http://localhost:3000/api/health` → `{"ok":true}`.
- Фронт БЕЗ бэкенда заливает консоль socket.io `WebSocket ... handshake response` ошибками и `/api/*` 500 — это ECONNREFUSED, не баг (не путай с крашем React).
- Первичная настройка: `npm run setup` (установка + миграции + seed). Сброс БД: `npm run db:reset`.

## Conventions
- Комментарии в коде и UI-тексты — на русском.
- Стили Tailwind, палитра `mystic-*` (gold/violet/purple).
- REST-клиент: `client/src/api.ts` — `api.get/post/patch/del`, пути относительные `/api/...`.
- Socket: `client/src/socket.ts` — единый `socket` + хук `useSocketEvent(event, handler)` (авто-отписка).
- Текущая команда/спринт: `client/src/store.tsx`, localStorage-ключи `ao.teamId` / `ao.sprintId`.
- UI-примитивы: `client/src/components/ui.tsx` (`Button/Card/Input/Title/Empty`) и `components/Modal.tsx`.

## Feature notes (data patterns)

### Таро — `server/src/data/tarot.ts`
- 78 карт. Ключи `0..21` — старшие арканы, `22..77` — младшие (4 масти × 14: Туз..10, Паж, Рыцарь, Королева, Король). Масти: Жезлы 🔥, Кубки 💧, Мечи ⚔️, Пентакли 🪙.
- `deckKeys(deck: 'major'|'minor'|'all')` отдаёт пул ключей. Розыгрыш — в `socket/index.ts` `drawTarot`, принимает `deck`.
- Клиент `pages/Tarot.tsx`: тумблер `DECKS` (Старшие/Младшие/Все) + `socket.emit('drawTarot', { sprintId, count, deck })`.
- Расклады хранятся в `TarotReading.cards` как JSON-строка ключей.

### Ретро «миро-доска» — `pages/Retro.tsx` + `routes/retro.ts`
- Колонки — JSON в `RetroBoard.columns` (String): массив `[{id, title, color}]`. БЕЗ миграции схемы.
- `RetroCard.column` (String) хранит **id** колонки, а не имя.
- Обратная совместимость: старые доски хранили колонки как массив имён — `normalizeColumns` конвертирует имя→id (id=имя), старые карточки не ломаются.
- Колонки: POST/PATCH/DELETE `/retro/:boardId/columns...`, reorder через PATCH c `{ columnIds }`. Перенос карточки — PATCH `/retro/:boardId/cards/:cardId` c `{ columnId }`.
- Все мутации шлют socket-событие `retroBoardUpdated`; клиент перечитывает доску.
- Drag-and-drop — нативный HTML5 DnD (`onDragStart/onDragOver/onDrop`), паттерн взят из `pages/Matrix.tsx`. Колонки тащатся за заголовок, карточки целиком.

### Звук — `client/src/sound.ts` + `SoundProvider.tsx`
- Процедурный Web Audio (без ассетов). Полный гайд — skill `web-audio-sound-effects`.
- События→звук централизованы в `SoundProvider` (broadcast-события: `diceRolled`→dice, `wheelSpinResult`→wheelLand, `tarotDrawn`→cardFlip, `icebreakerSelected`→reveal, `matrixUpdated`→tick). Локальный `play('spin')` — в `Wheel.tsx`.

## Pitfalls
- **Карточка-флип (framer-motion backface):** `initial rotateY:180 → animate rotateY:0` оставляет карту РУБАШКОЙ. Правильно `0 → 180` (рубашка → лицо). См. `TarotCardView` в `Tarot.tsx`.
- **Пустой массив ≠ «не передано»:** `customTitles.length ? customTitles : default` считает `[]` за отсутствие и подставляет дефолтный шаблон. Для «пустой доски» проверяй `Array.isArray(req.body.columns)` явно.
- **SVG-указатель колеса** (`Wheel.tsx`): `polygon points="14,0 0,28 28,28"` (остриё вверху) указывает НАРУЖУ; внутрь колеса — остриё внизу `"14,34 0,0 28,0"`.

## Verification workflow
- `npm --prefix client run typecheck` + `npm --prefix client run build` (оба под node v20).
- Браузерный smoke-тест через playwright MCP: `browser_navigate` → `browser_snapshot` → select команды/спринта в сайдбаре → клик по фиче → `browser_snapshot` проверить результат. Бэкенд должен быть запущен.
- Быстрая проверка целостности данных (78 карт, ключи, масти): пиши `.ts`-скрипт и гоняй `npx tsx <script>.ts` из `server/` (tsx не проверяет типы — ок для одноразовых проверок).

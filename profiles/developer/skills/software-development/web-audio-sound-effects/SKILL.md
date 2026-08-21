---
name: web-audio-sound-effects
description: Add sound effects to a web app via Web Audio API.
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [web-audio, audio, react, vite, socket-io, ux, frontend]
    related_skills: [node-realtime-fullstack, full-stack-fastapi-react, spec-driven-implementation]
---

# Web Audio Sound Effects (procedural synthesis)

## When to use
- User asks for "sound feedback", "звуковые отклики", "sound effects", "звук", "звуковое сопровождение" in a web app (games, dashboards, interactive tools).
- Any interactive browser UI that needs audible feedback WITHOUT shipping audio asset files.

## Why procedural (Web Audio API) FIRST
- Zero npm dependencies, zero asset files, works offline. Ships in one module.
- Instant iteration: tweak a frequency/envelope, not a file.
- Good enough for UI blips and short game effects. NOT for rich/musical sounds — escalate to Howler.js + curated assets (freesound.org, kenney.nl, mixkit.co) as phase 2, or Tone.js for ambient music as phase 3.

## Core architecture (all in one framework-agnostic module)
1. **Lazy AudioContext** — create on first `play()`, never at module load. Autoplay policy blocks a context created without a user gesture.
2. **Single master `GainNode` → destination** — one place to apply global volume/mute.
3. **`unlock()`** — resume the context on first `pointerdown`/`keydown` (attach in a top-level provider/effect).
4. **`play(name)`** — if muted return; ensure ctx; if `state === 'suspended'`, `resume().then(run)`; else `run()` immediately.
5. **Mute state** in `localStorage` + a `subscribe(fn)` set, surfaced to React via `useSyncExternalStore(subscribe, isMuted)` — no context needed.

## Sound recipes (oscillator/noise + envelope)
- **dice/clatter**: bandpass-filtered noise burst (~3 kHz, ~0.2 s) + 3 square "clack" transients at ~40 ms offsets.
- **whoosh/spin**: bandpass noise (~800 Hz, Q 2) ~0.35 s.
- **bell/ding**: 2–3 sine overtones (880 / 1320 / 1760 Hz) with long decay (~0.9 s) — "mystic" chime.
- **card flip/swish**: short noise (~0.12 s) + triangle tone sweeping 400→900 Hz.
- **reveal/success**: rising two-note pluck (E5 659.25 → A5 880).
- **tick**: 30 ms square at 1200 Hz, low gain (0.06) — subtle UI feedback.

Full copy-pasteable engine: `templates/sound-engine.ts`; React router/provider: `templates/SoundProvider.tsx`.

## Multiplayer (socket.io) routing pattern
- The server broadcasts an event to ALL clients in a room — INCLUDING the actor. So play the sound on the **broadcast** event (`diceRolled`, `wheelSpinResult`, …), not on the local `emit`.
- Route everything in ONE central `SoundProvider` that subscribes to socket events and maps event→sound. Pages stay untouched.
- Exceptions: purely local, non-broadcast actions (e.g. "start spinning" `spinWheel` emit) get a direct `play('spin')` call in that one handler.

## React integration shape
- `sound.ts` — engine only, no React import (testable/portable).
- `SoundProvider.tsx` — mounts unlock listeners + `useSocketEvent` mapping; exports `useMuted(): [boolean, () => void]`.
- Mount `<SoundProvider>` inside the store/router providers in `main.tsx`.

## Pitfalls
- `exponentialRampToValueAtTime` cannot target `0` — use `0.0001` for both attack start and release end.
- `resume()` returns a Promise; schedule the synth AFTER it resolves, or the very first play is silent.
- An `AudioContext` constructed outside a user gesture starts in `'suspended'` state.
- Guard `window.AudioContext || (window as any).webkitAudioContext` for Safari.
- The `subscribe` unsubscribe must return `() => void`; a bare `() => set.delete(fn)` returns boolean — wrap in braces.
- No test runner in many Vite apps: verification = `tsc --noEmit` + `vite build` + manual browser check. Don't force-add vitest for audio side-effects (thin unit-testable surface).
- Vite 5 requires Node ≥18. `npm run build` failing with `SyntaxError: Unexpected token '??='` (or an `UnhandledPromiseRejectionWarning` pointing at it) means the shell's default `node` is too old (e.g. 14) while npm runs on it — select a newer node first: `export PATH="$HOME/.nvm/versions/node/v20.20.0/bin:$PATH"` (or `nvm use`), then rebuild. `tsc --noEmit` can pass on old Node while `vite build` fails, so always run the build too.
- Smoke-testing a frontend whose backend ISN'T running will flood the console with socket.io `WebSocket ... handshake response` failures and `/api/*` 500s — those are expected (ECONNREFUSED), NOT your bug. Don't misread them as a React crash. Verify with playwright MCP instead of eyeballing: `browser_navigate` → `browser_snapshot` (your UI rendered, e.g. the mute toggle) → `browser_click` on the toggle → `browser_evaluate` `() => localStorage.getItem('app.muted')` to confirm the key wrote. Only treat a console error as yours if its source references your module file.

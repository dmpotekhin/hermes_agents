# TypeScript / Vite pitfalls (worked example: notion-clone client)

Concrete pitfalls from building a React/Vite + TS client for an Express + Socket.IO
app (notion-clone). All observed in a real session.

## `as` binds tighter than `??` (TS operator precedence)

Wrong (type error TS2345 at a call site, e.g. `JSONContent` not assignable to
`unknown[]`):

```ts
const content = editor.getJSON().content as unknown[] | undefined ?? [];
```

Parses as `(x as unknown[] | undefined) ?? []` — the cast wins over the nullish
coalescing, and the union type leaks through to wherever `content` is used.

Correct — cast AFTER the coalescing, parenthesize the whole expression:

```ts
const content = (editor.getJSON().content ?? []) as unknown[];
```

Rule: `(x ?? fallback) as T`, never `x as T | undefined ?? fallback`.

## Stale tsc errors with incremental builds

Symptom: `tsc --noEmit` reports an error (e.g. `Cannot find module '../api'`) that
does NOT match the current file content (the file already imports `./api`).

Cause: `tsconfig.tsbuildinfo` incremental cache. The reported error is from a
previous state.

Fix procedure:
1. Re-read the file BEFORE "fixing" anything — confirm the error still exists.
2. Re-run `tsc --noEmit` — the phantom often disappears on a fresh run.
3. Only then fix genuinely real errors.

Related: never commit `*.tsbuildinfo` — it churns every build and is
machine-specific. Add to `.gitignore` alongside `*.db*`.

## `vite build` in Hermes terminal is misclassified as a long-lived server

Running `npx vite build` in a foreground `terminal` call can be refused with
"this foreground command appears to start a long-lived server/watch process".

Workaround: run it with `background=true` + `notify_on_complete=true` (or
`terminal` with a short timeout via a wrapper). It exits normally and prints
bundle sizes. Same applies to any bundler CLI that might look like a dev server
(esbuild, rolldown watch modes).

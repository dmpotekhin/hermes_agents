# vaultRoot cache leak across test files — root cause (commit 4730ba0)

## Symptom

- New test file `tests/core/journal.test.ts` passed in isolation (`bun test tests/core/journal.test.ts`) but the FULL suite showed 12 failures in unrelated files: `log.test.ts`, `dream.test.ts` (runDream), `vault.test.ts`, `config.test.ts`, `admin.test.ts` (status/audit/rollback).
- Isolated pairs passed too (`vault + admin` = pass; `journal + dream` = pass), but `journal + log` = fail.
- Lint also picked up the new code: `unicorn(no-array-sort)` — use `toSorted()` not `sort()` in `src/core/journal.ts`.

## Root cause

`vaultRoot()` in `src/core/vault.ts` caches the resolved `BRAIN_VAULT` path in a module global (`vaultRootCache`) on first call:

```ts
let vaultRootCache: string | null = null;
export function vaultRoot(): string {
  // cache first resolved env value forever
}
```

bun:test does NOT reset module state between test FILES (same process, shared module registry). So the FIRST test file to call `vaultRoot()` wins: every later file's `beforeAll`/`tempVault` sets a fresh `BRAIN_VAULT`, but code paths (`brainDir()`, `appendLogEvent`, etc.) keep reading/writing the FIRST file's vault.

Why it only broke NOW: before this session the first file's vault was `fixtures/test-vault` (shared, deleted only in that file's afterAll) — later files accidentally read/wrote it and their assertions on `join(TEST_VAULT, ...)` happened to match. The new `tempVault()`-based file (`journal.test.ts`) sorts BEFORE `log.test.ts` alphabetically, resets nothing, and DELETES its vault in afterEach — so `log.test.ts` (which asserts on its own `fixtures/test-vault` path) suddenly reads a deleted vault and fails.

Debugging evidence that nailed it: a `console.log` inside the failing test showed `entries` containing records written by the PREVIOUS test file (timestamps from `spills` test) while `process.env.BRAIN_VAULT` pointed at a fresh vault — i.e. reads hit the cached path, not the env.

## Fix

1. `src/core/vault.ts`: export a public reset:

```ts
export function resetVaultRoot(): void {
  vaultRootCache = null;
}
```

2. Every test file that assigns `BRAIN_VAULT` must call `resetVaultRoot()` on the line immediately BEFORE the assignment — in `tempVault()` helpers and `beforeAll` blocks alike. Applied to all 20 test files (script-assisted: regex for `process.env["BRAIN_VAULT"] =` / `process.env.BRAIN_VAULT =`).

3. `tests/cli.test.ts` is exempt: it passes `BRAIN_VAULT` via `spawnSync` env object to a separate CLI process — no shared module state.

## Rule

Any NEW test file touching the vault MUST include `resetVaultRoot()` before setting `BRAIN_VAULT`. Without it the suite order becomes load-bearing and unrelated files fail in full runs while passing in isolation.

## Verification

- `bun test` → 135 pass / 0 fail (was 130 + 5 new)
- `bun run lint` → 0 warnings / 0 errors (after `sort()` → `toSorted()`)
- `bun run typecheck` → clean

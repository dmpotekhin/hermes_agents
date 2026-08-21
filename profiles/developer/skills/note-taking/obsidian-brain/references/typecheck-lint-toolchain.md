# Typecheck / lint toolchain (fixed 2026-08-20)

Status: `bun test` (130), `bun run typecheck`, `bun run lint` all green on main.

## Commands

- `bun test` — 130 tests across 23 files
- `bun run typecheck` — `tsc --noEmit`
- `bun run lint` — oxlint via bun (see below)
- `bun run lint:fix`, `bun run fmt` / `bun run fmt:check` (oxfmt)

## Root cause 1 — typecheck failed (obligations.ts)

tsconfig has `noUncheckedIndexedAccess: true`, so a regex group `match[1]` and
`.split("T")[0]` are typed `string | undefined`. Fixes:

- `parseInt(match[1] ?? "0", 10)` (never pass `string | undefined` to parseInt)
- `date.toISOString().slice(0, 10)` instead of `.split("T")[0]`

Also: oxlint's unicorn rules push `sort()` → `toSorted()` and `reverse()` →
`toReversed()`. Those ES2023 methods require `"lib": ["ES2023"]` in tsconfig
(bun runtime supports them fine; tsc does not know them without the lib entry).

## Root cause 2 — lint never ran (oxlint shim vs Node 14)

`node_modules/oxlint/bin/oxlint` (v1.75) is an extensionless ESM shim
(`import "../dist/cli.js"`). System Node is v14.21.3 → `ERR_UNKNOWN_FILE_EXTENSION`;
lint was dead even on a clean checkout. `bunx oxlint` fails the same way.

Fix — run oxlint through bun:

```
bun node_modules/oxlint/dist/cli.js -c .oxlintrc.json
```

package.json scripts `lint` / `lint:fix` now use this form.

Do NOT "fix" by upgrading system Node: v14 is system-level and the machine
lacks Xcode CLT, so brew native builds are painful. The bun route is zero-install.

## .oxlintrc.json format (1.x)

INVALID — oxlint rejects it ("recommended" is not a severity):

```json
{ "rules": { "typescript": "recommended", "import": "recommended", "unicorn": "recommended" } }
```

VALID:

```json
{
  "$schema": "https://raw.githubusercontent.com/oxc-project/oxc/main/npm/oxlint/configuration_schema.json",
  "plugins": ["typescript", "import", "unicorn"],
  "categories": { "correctness": "error", "suspicious": "warn" }
}
```

Categories bundle rule sets from the listed plugins; `rules` only takes
individual rule names with `error|warn|off`.

## Pitfall: surgical unused-import removal

oxlint's no-unused-vars flags ONE identifier (`existsSync is imported but never
used`) — other names in the SAME import statement may still be used. Remove only
the flagged name, then verify (LSP diagnostics / typecheck). Removing whole
import lines this way broke 4 test files in one pass; LSP caught it immediately
and the edits were reverted. Lesson: read the exact flagged identifier, edit the
import statement in place.

## Other lint fixes applied

- `for (const f of list(...).filter((f) => ...))` → rename the callback param
  (`no-shadow`; the `f` from the for-loop is shadowed)
- `_vaultRoot` → `vaultRootCache` (`no-underscore-dangle` — leading `_` banned)
- unused function param → prefix `_` (`_args`)
- dead imports removed: `vaultRoot` in writer.ts, `fileExists` in dream.ts,
  plus ~10 in tests

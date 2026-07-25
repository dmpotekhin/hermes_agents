---
name: spec-driven-implementation
description: Use when implementing from a task brief or spec that includes reference/example code — the brief's code is a design guide, not a copy-paste source. Verify every dependency's actual signatures before implementing.
---

# Spec-Driven Implementation

## Overview

Task briefs and specs often include reference implementation code. That code is a design guide, not production code. It frequently contains bugs: missing `await` on async functions, incorrect assumptions about module APIs, logic errors, and edge-case omissions.

**Core principle:** The brief tells you WHAT to build. The actual module signatures tell you HOW.

## When to Use

- Implementing from a task brief with reference code
- Following a spec that includes example implementations
- Any workflow where you're given "here's the code you should write"

## The Verification Gate

Before writing a single line of implementation:

1. **Map every import to its actual module.** For each `import { X } from "./foo"` in the brief's reference code, `read_file` the actual module to verify `X`'s real signature.
2. **Check async/sync.** Is `X` exported as `async function`? The brief may call it without `await`.
3. **Run the test first (TDD).** Even before reading the reference implementation, write the test and watch it fail. This proves the test is valid.
4. **Compare, don't copy.** The reference code is ONE input to your implementation. Use it as guidance, but cross-check every line against the verified module signatures.

## Common Brief Code Bugs

| Pattern | Example | Fix |
|---------|---------|-----|
| Missing `await` on async | `const x = loadConfig()` when `loadConfig` is `async` | `const x = await loadConfig()` |
| Missing `await` on async helper | `const c = readFile(path)` when `readFile` is `async` | `const c = await readFile(path)` |
| Orphaned state breaks idempotency | Signals stay in inbox after processing | Move ALL scanned items, not just action-triggering ones |
| Double-processing | Same item processed in two phases (e.g., rebutted then expired) | Remove from lookup after first action |
| Wrong extraction method | Parsing YAML by line-matching instead of using the parsed object | Use the already-parsed frontmatter data |
| Runtime-incompatible library | `import Database from "better-sqlite3"` under Bun (needs native .node bindings) | Use `import { Database } from "bun:sqlite"` instead; verify imports in target runtime |

## Workflow

1. Read the brief — understand the requirements
2. Read ALL dependency modules — verify their actual exports and signatures
3. Write tests first (TDD) — watch them fail
4. Implement, cross-referencing brief code against verified signatures
5. Run tests, iterate until green
6. Run full test suite to catch regressions
7. Commit

## Pitfalls

- **Do NOT copy-paste the brief's code.** It will have bugs. Always.
- **Do NOT trust the brief's module imports.** Read the actual module files.
- **Do NOT assume sync when the module exports async.** Vault helpers (`readFile`, `atomicWrite`) are async. Config loading is async. Check every call.
- **Do NOT trust the brief's library choice.** A library that works in one runtime (Node.js `better-sqlite3`) may not work in another (Bun). Always verify the import actually succeeds in the target runtime before writing code against it.
- **Test for idempotency.** Running the same operation twice with no new inputs should touch nothing.

## Verification Commands by Runtime

The TDD skill uses `npm test` generically. Match the project's actual test runner:

| Runtime | Test command | Notes |
|---------|-------------|-------|
| Node.js / npm | `npm test` | Standard |
| Bun | `bun test` | Bun projects have `bun test` in `package.json` scripts |
| Deno | `deno test` | |

## Reference Files

- `references/task-2.5-brief-bugs.md` — Concrete example: 5 bugs found in the dream algorithm brief's reference implementation (missing awaits, idempotency, double-retirement).
- `references/task-3.1-brief-bugs.md` — FTS5 search index: wrong SQLite library for runtime, missing content column, delete ordering, title extraction, async/sync mismatch.
- `references/task-3.2-clean-brief.md` — Counterexample: a brief with no bugs, all imports and signatures verified correct. Validates that the Verification Gate catches both broken AND clean briefs.
- `references/task-3.3-brief-bugs.md` — `brain_status` tool: missing `await` on `loadConfig()` (same class of bug as Task 2.5 Bug 1 — recurring pattern).

# Task 3.3: brain_status Brief Bug

## Brief Reference: task-3.3-brief.md

The brief for `brain_status` MCP tool included a reference implementation of `src/mcp/tools/admin.ts`.

## Bug Found

### Bug: Missing `await` on `loadConfig()`

**Line:** `const config = loadConfig();`
**Actual:** `loadConfig` is exported as `async function loadConfig()` in `config.ts`.
**Fix:** `const config = await loadConfig();`
**Impact:** `config` would be a Promise<BrainConfig>, not a BrainConfig object. `config.vaultPath`, `config.candidateThreshold`, etc. would all be `undefined`. The returned status object would have `vault_path: undefined` and `config: { candidate_threshold: undefined, stale_evidence_days: undefined }`.

Note: this is the **same class of bug** as Task 2.5 Bug 1 — the brief consistently calls `loadConfig()` without `await`. This has now appeared in two tasks, making it a recurring pattern worth double-checking in every new brief.

## What Was Correct

| Check | Result |
|-------|--------|
| `brainDir`, `listDir`, `fileExists` from `vault.ts` | ✅ All sync, all exist |
| `loadConfig` from `config.ts` | ❌ Async, but brief called it without `await` |
| Path joining with `join()` | ✅ Correct |
| Return object shape | ✅ Matches interface |

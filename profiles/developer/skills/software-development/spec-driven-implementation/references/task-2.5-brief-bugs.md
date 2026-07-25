# Task 2.5 Dream Algorithm — Brief Bugs

## Brief Reference: task-2.5-brief.md

The brief for the dream algorithm included a full reference implementation of `src/core/dream.ts`. That code had 5 bugs that caused test failures or correctness issues.

## Bugs Found

### Bug 1: Missing `await` on `loadConfig()`
**Line:** `const config = loadConfig();`
**Actual:** `loadConfig` is exported as `async function loadConfig()` in `config.ts`.
**Fix:** `const config = await loadConfig();`
**Impact:** `config` would be a Promise, not a BrainConfig object. All `.candidateThreshold` etc. accesses would be undefined.

### Bug 2: Missing `await` on `readFile(path)` 
**Line:** `const content = readFile(path);`
**Actual:** `readFile` is exported as `async function readFile()` in `vault.ts`.
**Fix:** `const content = await readFile(path);`
**Impact:** `content` would be a Promise, `parseFrontmatter` would fail.

### Bug 3: Missing `await` on `readFile` (second occurrence)
**Line:** `const principle = readFile(group[0]!.path).split("\n")`
**Fix:** `const principle = (await readFile(group[0]!.path)).split("\n")`

### Bug 4: Orphaned signals break idempotency
**Description:** The brief code only moved signals to `inbox/processed/` when they triggered an action (preference created, rebutted, or noted redundant). Signals below the candidate threshold stayed in the inbox. On the next `runDream()` call, they'd be re-scanned, breaking the idempotency test expectation of `signals_processed: 0`.
**Fix:** Move ALL scanned signals to `processed/`, tracked via `allSignalPaths`.

### Bug 5: Double-retirement of rebutted preferences
**Description:** Phase 5 rebuts preferences (opposite-sign signal group meets threshold). Phase 6 iterates over `existingPrefs` to check for retirement conditions (expiry, staleness). If a pref was rebutted in Phase 5, its entry still exists in `existingPrefs`. Phase 6 would try to `moveToRetired()` again, which throws "Preference not found" because the file was already removed.
**Fix:** After rebuttal, `existingPrefs.delete(slug)` to remove the entry before Phase 6 runs.

# Task 3.1 Brief Bugs: FTS5 Search Index

Concrete bugs found when implementing from the Task 3.1 brief (FTS5 search index). The brief's reference `search.ts` had 3 classes of bugs.

## Bug 1: Wrong SQLite library for runtime

**Brief code:** `import Database from "better-sqlite3"`

**Problem:** `better-sqlite3` requires native C++ bindings compiled against Node.js. When the runtime is Bun (as this project uses), the `.node` bindings file doesn't exist and the import crashes:
```
error: Could not locate the bindings file. Tried:
 → …/better-sqlite3/build/better_sqlite3.node
```

**Fix:** Use `import { Database } from "bun:sqlite"` when running under Bun. The APIs are similar but not identical — verify parameter order and method names.

**Verification pattern:**
```bash
# Always test that the SQLite library actually imports before writing code
bun -e "import Database from 'better-sqlite3'; console.log('ok')"  # fails under Bun
bun -e "import { Database } from 'bun:sqlite'; const db = new Database(':memory:'); console.log('ok');"  # works
```

## Bug 2: Missing content column in external content FTS5 table

**Brief code:**
```sql
CREATE TABLE IF NOT EXISTS files (
  path TEXT PRIMARY KEY,
  title TEXT,
  kind TEXT,
  mtime INTEGER
);
CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(
  title, content, content=files, content_rowid=rowid
);
```

**Problem:** The FTS5 table references a `content` column in the `files` table via `content=files`, but the `files` table doesn't have a `content` column. When deleting or querying, SQLite throws `SQLiteError: no such column: T.content`.

**Fix:** Add a `content TEXT` column to the content table, matching the column referenced by the FTS declaration.

```sql
CREATE TABLE IF NOT EXISTS files (
  path TEXT PRIMARY KEY,
  title TEXT,
  content TEXT,  -- ← MUST exist, referenced by FTS content=files
  kind TEXT,
  mtime INTEGER
);
```

## Bug 3: Delete order with external content FTS5 tables

**Brief code:**
```typescript
this.db.exec("DELETE FROM files");
this.db.exec("DELETE FROM files_fts");
```

**Problem:** With external content FTS5 tables, deleting from the content table (`files`) first causes the subsequent FTS delete to fail because FTS5 tries to sync with rows that no longer exist in the content table.

**Fix:** Delete from the FTS table FIRST, then the content table:
```typescript
this.db.exec("DELETE FROM files_fts");
this.db.exec("DELETE FROM files");
```

## Bug 4: Title extraction missing H1 fallback

**Brief code:**
```typescript
const title = (data["title"] as string) ?? filePath.split("/").pop() ?? "";
```

**Problem:** The brief's test fixtures have no `title` field in their frontmatter — only an H1 heading (`# Search Test Rule`). The test expects `results[0]!.title` to contain "Search Test Rule", but the code falls back to the filename (`pref-search-test.md`).

**Fix:** Extract the title from three sources in priority order:
```typescript
// Title: frontmatter "title" → first H1 → filename
let title = data["title"] as string | undefined;
if (!title) {
  const h1Match = body.match(/^#\s+(.+)$/m);
  title = h1Match?.[1] ?? filePath.split("/").pop() ?? "";
}
```

## Bug 5: Async/sync mismatch on `readFile`

**Brief code:** `const content = readFile(filePath)` — calling without `await` on an async function.

**Problem:** `readFile` in `vault.ts` is exported as `async function readFile()` and returns `Promise<string>`. The brief code calls it synchronously, which in Bun would give a Promise, not a string.

**Fix:** Either `await readFile(filePath)` or use `readFileSync` from `node:fs` directly. For this implementation, `readFileSync` was used since the SQLite operations are synchronous and mixing async file reads with sync DB writes is awkward.

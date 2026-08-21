# Entities & FTS5 search (obsidian-brain)

Added 2026-08-20 (commit 873413f) — backported from akitaonrails/ai-memory
(their "entities" recall concept) into the Brain MCP server.

## Entities auto-generation (src/core/entities.ts)

- `extractEntities(body, title, max=10)` — frequency-based keyword extraction:
  - token regex `[a-zа-яё][a-zа-яё0-9-]{2,}` (≥4 chars after lowercase),
  - drops pure numbers, EN+RU stop-word set,
  - strips markdown: code fences, inline code, links, headings, `[*_>~|+]`.
- `brain_create_note` auto-fills `entities` frontmatter unless the caller
  provided them explicitly (explicit values are never overwritten).
- Title words are included in the token stream so a note titled
  "PostgreSQL Migration Notes" gets `postgresql` as an entity.

## Search integration (src/core/search.ts)

- `indexFile()` appends `data.entities` (joined) to the FTS5 content column:
  `body + " " + entities` — so a query matching only an entity word still
  finds the page.
- Existing notes without `entities` frontmatter keep working; entities only
  help notes created after the feature.

## The two hyphen gotchas (both fixed)

1. **FTS5 MATCH**: `a-b` parses as `a NOT b`. Searching `docker-compose`
   excluded the file containing `docker-compose`. Fix in `search()`:
   ```ts
   const ftsQuery =
     query.includes("-") && !query.includes('"') && !query.includes(" ")
       ? `"${query}"`   // phrase match
       : query;
   ```
2. **stripMarkdown**: character class `[*_>~|+-]` includes `-`, which split
   `docker-compose` into `docker` + `compose` before counting. Kept as
   `[*_>~|+]` — hyphens survive, markdown bullets (`- item`) still produce
   the item token because the token regex requires a leading letter.

## Verification pattern for pre-existing failures

`bun run validate` = typecheck + lint + test. On this machine it fails on a
clean checkout: `src/mcp/tools/obligations.ts` TS errors (string|undefined)
and oxlint `ERR_UNKNOWN_FILE_EXTENSION` under bun. When hitting these:
```bash
git stash -u && bun run typecheck && bun run lint && git stash pop
```
If it fails there too, it's pre-existing — verify with `bun test` only.

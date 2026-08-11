---
name: books-batch-update
description: "Batch book note generation (10+ books) — subagent delegation, terminal blocking workarounds, verification. Companion to add-book-note."
---

# Books Batch Update — 10+ New Books

Trigger: when `add-book-note` detects 10+ books without notes. Load alongside `add-book-note` — this skill extends step 3 (note writing) and step 5 (verification) for large batches.

## Step 3 (extended): Parallel Note Generation

### Dispatching subagents
Split books into 3 groups of ~15 each. Use `delegate_task` with `tasks` array:

```python
delegate_task(tasks=[
  {"goal": "Write book notes for N books. Return valid JSON object...",
   "context": "Books 1-15:\nAuthor | Title | Genre\n...\n\n⚠️ CRITICAL: Write result to /Users/dmitrypotekhin/book_notes_group1.json using write_file. Do NOT output JSON in final message — delegation truncates large output."},
  # ... groups 2, 3
])
```

### Pitfall: Subagent Output Truncation
Subagent final messages truncate large JSON. ALWAYS instruct subagents to write JSON to a FILE. Then read the files after delegation completes. If a subagent ignores this and outputs in message only, the JSON may be lost — you'll need to re-generate that group manually.

### Combining results
After all subagents complete, read their JSON files, merge into one dict, and insert into notes-data.js via a Python script (see below).

## Terminal Blocking Patterns

User consistently blocks these command forms — avoid them:
- `node -e "..."` — blocked
- `python3 -c "..."` with heredoc/herestring — blocked
- `rm` for file deletion — blocked

**Preferred approach for all steps:**
1. `write_file` to create a Python script (e.g., `_rebuild_books.py`, `_insert_notes.py`, `hermes-verify-books.py`)
2. `terminal python3 script.py` to run it
3. Don't attempt `rm` cleanup — leave temp scripts, user deletes manually

### Insertion script pattern
Write a standalone Python script that:
1. Reads all note data (from subagent JSON files or hardcoded dicts)
2. Opens `js/notes-data.js`
3. Finds `\n};` (closing of `const bookNotes = {`)
4. Inserts all new entries before it
5. Writes back

```python
with open('js/notes-data.js', 'r') as f:
    content = f.read()
closing_pos = content.rfind('\n};')
insertion = # build new entries as JS object notation
new_content = content[:closing_pos] + insertion + content[closing_pos:]
with open('js/notes-data.js', 'w') as f:
    f.write(new_content)
```

## Step 5 (extended): Verification

Use `execute_code` instead of terminal — it's non-destructive and can read files via `read_file` tool.

### execute_code read_file format
Lines come with number prefix: `1|content`. Regex must account for this:

```python
# In execute_code:
from hermes_tools import read_file
r = read_file("js/notes-data.js", limit=100)
content = r['content']  # "1|// comment\n2|const x = {\n3|  \"key\": {..."

# Match note keys:
note_keys = re.findall(r'\|\s{2}"([^"]+)": \{', content)
```

### Verification checklist
- [ ] books-data.js: starts with `const booksData = [`, ends with `];`, count matches Excel
- [ ] notes-data.js: ends with `};`, total notes >= previous + new
- [ ] Spot-check 5-10 new entries present
- [ ] Last new entry has `"theses": [` and `"takeaway":` structure
- [ ] Git commit pushed to master

## Subagent Group Size Reference
- 3 subagents × 15 books each = 45 max per batch
- Max concurrent: 3 (configurable via delegation.max_concurrent_children)
- Each subagent takes ~2-4 minutes with web_search

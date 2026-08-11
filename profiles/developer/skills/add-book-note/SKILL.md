---
name: add-book-note
description: "Full book update cycle: Excel → JS → notes → commit → devlog → devjournal → content-factory. Triggered by 'обнови таблицу с книгами', '/books', 'update books'."
---

# Add Book & Note to GitHub Pages — Full Cycle

Triggers: "обнови таблицу с книгами", "/books", "update books", "обнови таблицу", "добавь книгу", "новая книга".

## Workflow (8 steps, do NOT skip any)

### 1. Parse Excel → rebuild `js/books-data.js`
Write a Python script to `_rebuild_books.py`, run with `terminal python3 _rebuild_books.py`, delete temp script.
- Use openpyxl. Data starts at row 2 (row 1 = headers, often read as None).
- Columns: A=author, B=title, C=genre.
- Escape: `title.replace("\n", " ").replace("\r", " ")`, `str.replace('"', '\\"')`.
- Verify: `node -e "const b=eval(...);console.log(b.length)"` — must match Excel row count.

### 2. Find books without notes
Compare books-data.js titles against notes-data.js keys. List ALL missing titles with their author and genre.
Output the list before proceeding to step 3.

### 3. Write theses + takeaway for EACH new book
For EACH missing book:
- Search the web for content summary (web_search + web_extract).
- Write 5 theses + takeaway in Russian.
- Insert all new notes into `notes-data.js` at once using terminal + Python heredoc (NOT execute_code/write_file — silently fails on large files).
- Key = EXACT title from books-data.js. Insert before `\n};` with `\n` separator (NO double comma).

Notes format:
```json
{
  "theses": [
    "Тезис 1: главный герой/тема и задача",
    "Тезис 2: место/время или ключевая концепция",
    "Тезис 3: главный конфликт или практическое применение",
    "Тезис 4: поворот/инсайт",
    "Тезис 5: финал/итог"
  ],
  "takeaway": "2-3 предложения: суть книги, чему учит, польза."
}
```
Non-fiction adaptation: тема → концепции → применение → инсайт → итог.

### 4. Commit & Push
```bash
cd ~/Downloads/dmpotekhin.github.io
git add Книги.xlsx js/books-data.js js/notes-data.js
git commit -m "feat: update books from Excel — N books (+M new)"
git push origin master
```

### 5. Verify JS + CDN
- JS syntax: node -e eval check on both books-data.js and notes-data.js.
- Count match: books-data.js count == expected, new notes present with 5 theses each.
- CDN: `curl -sI https://dmpotekhin.github.io/js/notes-data.js | grep content-length`. May lag up to 10 min.

### 6. Devlog → Brain/journal/YYYY-MM-DD.md
```python
mcp__obsidian_brain__brain_devlog(entry="...", project="books-library")
```
One line: what was updated, how many books, which are new, commit hashes.

### 7. Devjournal → Brain/notes/YYYY-MM-DD-journal.md
```python
mcp__obsidian_brain__brain_create_note(
    path="YYYY-MM-DD-journal.md",
    content="## Books update\n\n- New books: ...\n- Notes added: ...\n- Commits: ..."
)
```
More detailed entry: list of new books with authors/genres, notes summary, commit details.

### 8. Content factory → Brain/notes/content/YYYY-MM-DD-topics.md
```bash
cd ~/content-factory && python3 -c "
from modules.devlog_scanner import scan_recent_events
from modules.topic_suggester import suggest_topics_rule_based, save_topics_to_obsidian
events = scan_recent_events(7)
topics = suggest_topics_rule_based(events, 5)
save_topics_to_obsidian(topics.topics, events)
"
```
Generates 5 topic ideas for blog posts based on recent dev activity.

## Important
- Key must match `title` EXACTLY (punctuation, quotes, years)
- Genre emoji: 📖 🧠 💻 🌍
- Append before `};` in notes-data.js — NO double commas
- Regenerate books-data.js fully from Excel — don't hand-edit
- Always write notes for ALL new books before committing
- Use terminal + Python heredoc, NOT execute_code write_file for large JS files
- Clean up temp `_*.py` scripts after each step
- NEVER skip steps 6, 7, 8 — they are mandatory

# Missing-Notes Check & Typo-Fix Detection (2026-08-24 session)

Quick reference for the "find books without notes" step (used with the `add-book-note`
8-step cycle and the `github-pages-books` umbrella).

## Fast semantic check on JS data (node available / approved)

The data files are JS, not JSON. For quick in-terminal checks use:

```bash
node -e "
const fs = require('fs');
const books = eval('(' + fs.readFileSync('js/books-data.js','utf8').replace('const booksData =','').replace(/;\s*$/,'') + ')');
const notes = eval('(' + fs.readFileSync('js/notes-data.js','utf8').replace('const bookNotes =','').replace(/;\s*$/,'') + ')');
const missing = books.filter(b => !(b.title in notes));
console.log('books:', books.length, '| notes:', Object.keys(notes).length, '| missing:', missing.length);
for (const b of missing) console.log(' -', JSON.stringify(b));
"
```

Two traps that WILL bite:

1. **Variable name**: notes-data.js declares `const bookNotes = {...}` — NOT `notesData`.
   (books-data.js uses `booksData`.) Wrong name → `TypeError: Cannot use 'in' operator`.

2. **Parens are required**: `eval('(' + src + ')')`. A bare `eval('{' + src + '}')`
   parses `{...}` at statement position as a BLOCK, and quoted keys like
   `"«Азазель», 1876 год":` fail with `SyntaxError: Unexpected token ':'`
   (string literals can't be labels). Strip the `const X =` prefix and trailing `;`
   before wrapping.

For heavier checks prefer the bundled script:
`python3 <skill_dir>/scripts/verify_books_data.py` — node --check + trailing-comma-tolerant
parse + MISSING + duplicate keys + 5-theses per title.

## Typo fix vs new book detection

After a rebuild, diff against the previous commit to classify changes:

```bash
git show HEAD:js/books-data.js | diff - js/books-data.js
# or compare via node: build Set(title|author) for HEAD vs working tree
```

- A title present in BOTH the NEW and REMOVED lists = **typo fix**, not a new book.
  Example: Шекспир «Укрощение строптивиой» → «Укрощение строптивой» (2026-08-24).
  The note already existed under the CORRECT title — do NOT write a second note.
- Only genuinely new keys (not in HEAD at all) need new notes.

## Garbage rows in Excel

`Книги.xlsx` can contain accidental single-char titles (e.g. `ы` with no author/genre).
The rebuild script must skip them: `if len(title) < 2: continue`.
Don't publish garbage rows; mention to the user that the Excel cell is dirty
(leave the Excel file itself untouched — it's the user's source of truth).

# Verifying JS data files (books-data.js / notes-data.js)

Pitfalls hit while comparing `books-data.js` titles against `notes-data.js` keys and
checking syntax/counts.

## Variable names (get these right first)

- `js/books-data.js` → `const booksData = [ ... ]`
- `js/notes-data.js` → `const bookNotes = { ... }`  ← NOT `notesData`

Using the wrong variable name in an eval/compare script fails with:
`Cannot use 'in' operator to search for '<title>' in undefined` (or similar).

## eval'ing a JS data file from node

Wrap the object/array literal in parens:

    node -e "const src = require('fs').readFileSync('js/notes-data.js','utf8'); const b = eval('(' + src + ')'); console.log(Object.keys(b).length)"

Bare `eval(src)` on `{...}` is parsed as a *block statement*, not an object literal →
`SyntaxError: Unexpected token ':'` (the string keys get read as labels).
Arrays (`[...]`) eval fine bare; objects do not.

## Comparing titles vs note keys (Python, no node)

    import re
    books = re.findall(r'"title": "([^"]+)"', open('js/books-data.js').read())
    notes = re.findall(r'^\s{2}"([^"]+)": \{', open('js/notes-data.js').read(), re.MULTILINE)
    missing = [t for t in books if t not in set(notes)]

- books-data.js entries look like `{"author": "...", "title": "...", ...}` — match on `"title": "..."`.
- notes-data.js keys are top-level object keys, 2-space indented — `^\s{2}"..."`.

## Count semantics

- Excel row count ≠ `booksData.length` (garbage rows + duplicate author/title rows are
  filtered/deduped during rebuild — see `excel-unsaved-edits.md`).
- A book whose title was typo-fixed (e.g. «Укрощение строптивиой» → «Укрощение строптивой»)
  is NOT a new book if a note already exists under the corrected key — check the note keys
  before declaring "missing note".

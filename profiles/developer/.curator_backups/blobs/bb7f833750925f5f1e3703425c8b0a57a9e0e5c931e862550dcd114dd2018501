# Books Update Pitfalls — Session 2026-08-10

## Double Comma After Insertion

When inserting new notes before the closing `};` in notes-data.js, the last existing entry may already have a trailing comma:

```python
insert_pos = content.rfind('\n};')
# If last entry is "takeaway": "..."\n  },\n};
# Inserting ",\n  \"New Book\": {...}" before \n}; produces:
#   },\n  "New Book": {...\n  },\n};  — correct
# But if last entry already has comma: "takeaway": "..."\n  },,\n  "New Book"
```

**Fix**: grep for `},,` after insertion and replace with `},`:

```bash
grep -n '},,' js/notes-data.js
```

Or use `patch` tool to replace `},,` → `},`.

## Node eval with const

`eval()` in Node.js module scope does NOT create `const` bindings visible to the eval'd code:

```javascript
// WRONG — ReferenceError: bookNotes is not defined
eval("const bookNotes = {...};");
console.log(bookNotes);

// RIGHT — use var
var nd = fs.readFileSync('js/notes-data.js','utf8').replace('const bookNotes','var bookNotes');
eval(nd);
// bookNotes now accessible
```

Don't strip the declaration wrapper — `eval('{...}')` returns the block statement, not the object.

## Verify Script Template

```javascript
var fs = require('fs');
var nd = fs.readFileSync('js/notes-data.js','utf8').replace('const bookNotes','var bookNotes');
var bd = fs.readFileSync('js/books-data.js','utf8').replace('const booksData','var booksData');
eval(nd); eval(bd);
var s = new Set(Object.keys(bookNotes));
var m = booksData.filter(x => !s.has(x.title));
console.log('Books:', booksData.length, 'Notes:', Object.keys(bookNotes).length, 'Missing:', m.length);
if (m.length) m.forEach(x => console.log('MISSING:', x.title));
process.exit(m.length ? 1 : 0);
```

## JSON Parsing Failure on notes-data.js

Python `json.loads()` fails on notes-data.js (>700KB) with encoding issues and JSON syntax errors deep in the file. Use Node.js eval instead for verification.

## Variable Name

The notes file uses `const bookNotes = {...}`, NOT `notesData`. The add-book-note skill incorrectly references `notesData`.

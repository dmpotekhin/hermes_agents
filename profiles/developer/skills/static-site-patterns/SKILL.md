---
name: static-site-patterns
description: Patterns, pitfalls, and workflows for maintaining static sites — JS data handling, emoji/unicode bugs, CDN deployment quirks, and dynamic UI on static pages.
---

# Static Site Patterns

Use when working on static sites (GitHub Pages, plain HTML/JS/CSS, or similar) — especially when adding data-driven features, dealing with Unicode/emoji in JS, or debugging deployment issues.

## Pitfalls

### Emoji in JavaScript regex character classes breaks on surrogate pairs
JavaScript regex character classes `[...]` match individual UTF-16 **code units**, not code points. Emoji above U+FFFF (📖🧠💻🌍 etc.) are surrogate pairs — two code units. A regex like `/^([📖🧠💻🌍])\s*/` captures only the first surrogate half, producing broken output (`�`).

**Fix:** Use `.split(' ')`, `Array.from()`, or `String.codePointAt()` instead of regex for emoji extraction.

```javascript
// BROKEN — captures surrogate half
const emoji = book.genre.match(/^([📖🧠💻🌍])\s*/)[1]; // → "�"

// FIXED — split on space
const emoji = book.genre.split(' ')[0]; // → "📖"
```

### GitHub Pages CDN propagation is not instant
After `git push`, different CDN edge nodes serve different file versions for up to 10 minutes. `curl` from terminal and browser may see different content.

**How to verify deploy:**
```bash
# Check raw file version via curl
curl -sI https://<user>.github.io/js/file.js | grep last-modified
curl -s https://<user>.github.io/js/file.js | grep "expected-string"
```
If curl shows the new version but browser shows old — it's CDN lag. Wait 2-5 minutes or use cache-busting query param (`?t=...`).

### Language toggle + dynamic content race condition
When `main.js` uses `data-lang` attributes with `innerHTML` replacement (`updateTextContent`), it overwrites any dynamically-populated child elements (counts, numbers). The language init runs after data init, nuking the populated values.

**Fix:** Split label and value into separate elements. The label span gets `data-lang`, the value span has only an `id`.

```html
<!-- BROKEN — language toggle overwrites the 521 -->
<p data-lang-ru="Всего книг: <span id='total-books'>N</span>">
  Всего книг: <span id="total-books">521</span>
</p>

<!-- FIXED — label has data-lang, value is separate -->
<p>
  <span data-lang-ru="Всего книг:" data-lang-en="Total books:">Всего книг:</span>
  <span id="total-books">521</span>
</p>
```

### Data-driven image lists load eagerly → first-paint cost scales with N
A render loop that injects one `<img>` per list item (map sidebar, city/card grid) and does NOT set `loading="lazy"` fetches every item's image the moment the list builds. On a static-site page this is the real "load": the initial download grows roughly as item_count × average image size and pins first paint (worst on mobile). The server/CDN side is usually NOT the concern — GitHub Pages serves static files free via CDN and a site well under the 1 GB soft limit is fine; the client-side eager fetch is what hurts.

- Eager list thumbs: `buildList()`-style loops render all N items → all N images are fetched at page open.
- On-demand popup images (e.g. a MapLibre popup photo injected after a click) already load lazily *by timing* — those are fine and often must STAY eager (lazy on a popup/DOM-rebuilt element can fail to load).
- Fix: add `loading="lazy"` to the list thumbnails so only near-viewport items fetch; and/or generate a small thumbnail variant (e.g. 200 px q70) for the list while keeping the full-size image for the on-demand popups.

```javascript
// BROKEN — every list item's image fetched at open regardless of scroll
var dot = '<img class="list-thumb" src="' + item.photo + '" alt="">';
// FIXED — only visible list items load
var dot = '<img class="list-thumb" loading="lazy" src="' + item.photo + '" alt="">';
```

## Patterns

### Excel → JS data pipeline
For static sites, store data in Excel for easy editing, then extract to JS with Python.

```python
import openpyxl, json

wb = openpyxl.load_workbook("data.xlsx")
ws = wb.active
books = []
for r in range(2, ws.max_row + 1):
    author = str(ws.cell(r, 1).value or "").strip()
    title = str(ws.cell(r, 2).value or "").strip()
    genre = str(ws.cell(r, 3).value or "").strip()
    if author and title:
        # Clean newlines that break JSON strings
        title = title.replace("\n", " ").replace("\r", " ")
        books.append({"author": author, "title": title, "genre": genre})

# Generate JS
with open("js/books-data.js", "w") as f:
    f.write(f"const booksData = {json.dumps(books, ensure_ascii=False, indent=2)};")
```

### Expandable notes on static site cards
Pattern for adding per-item notes to a static site without a backend:

1. Store notes in `js/notes-data.js` as an object keyed by title/ID
2. In `createBookCard()`, check `typeof bookNotes !== 'undefined' && bookNotes[book.title]`
3. Add a toggle button + hidden panel with `max-height: 0` → `max-height: 600px` CSS transition
4. Toggle `.notes-open` class on click to expand/collapse

See `references/expandable-notes.md` for the full implementation pattern.

## Verification

Before committing static site changes, run a quick smoke check:
```bash
# 1. All JS files parse without errors
for f in js/*.js; do node -e "require('./$f')" 2>&1 && echo "OK: $f"; done

# 2. Data has expected structure
node -e "const d = require('./js/books-data.js'); console.log(Object.keys(d[0]))"

# 3. HTML loads all scripts in correct order
grep '<script' index.html
```

## Referenced Patterns

- **Dark theme as default (no FOUC):** `references/dark-theme-no-fouc.md` — inline `<head>` script + `html.dark-theme body` CSS + localStorage persistence
- **Responsive layout with clamp():** `references/responsive-clamp-pattern.md` — `clamp()` for spacing/fonts/images, `auto-fit` grids, touch targets ≥44px
- **Expandable notes on cards:** `references/expandable-notes.md` — CSS transition toggle for per-item notes

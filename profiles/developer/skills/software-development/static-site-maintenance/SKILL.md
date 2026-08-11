---
name: static-site-maintenance
description: Maintaining static HTML/CSS/JS websites — verification, data pipelines from external sources, common pitfalls with generated content, GitHub Pages deployment.
---

# Static Site Maintenance

## Overview

For static websites (GitHub Pages, plain HTML/CSS/JS) — verifying correctness, updating data from external sources, and avoiding common pitfalls with dynamic content in otherwise static pages.

## Trigger Conditions

Use when:
- Verifying a static site before claiming work is complete
- Regenerating JS data files from external sources (Excel, CSV, JSON)
- Debugging rendering issues on a plain HTML/CSS/JS page
- Updating data-driven content on a static site

## Verification Workflow

Static sites have no compiler or test runner. Verification must be explicit:

### 1. JavaScript Syntax

Every JS file must pass Node.js `new Function()`:

```bash
node -e 'const fs=require("fs");new Function(fs.readFileSync("file.js","utf8"));console.log("OK");'
```

For generated data files, also verify data integrity:

```bash
node -e 'const a=JSON.parse(fs.readFileSync("data.js","utf8").match(/\[[\s\S]*\]/)[0]);
console.log(JSON.stringify({count:a.length, missing_fields:a.filter(b=>!b.key).length}));'
```

### 2. HTML Structure

Verify key elements exist in the served HTML:

```python
html = open("page.html").read()
for name, pattern in [("filter", 'id="genre-filter"'), ("sort", "genre-asc")]:
    assert pattern in html, f"Missing: {name}"
```

### 3. CSS Rules

Check that new CSS classes are present:

```python
css = open("styles.css").read()
assert '.new-component' in css
```

### 4. Browser Rendering (when JS generates content)

Start a local server and use Playwright:

```bash
cd /path/to/site && python3 -m http.server PORT &
```

Then verify via `mcp__playwright__browser_evaluate`:
```javascript
() => ({
    elementCount: document.querySelectorAll('.card').length,
    counterText: document.getElementById('counter')?.textContent,
})
```

### 5. Summary Script

Combine checks into one Python verification script. Use the template at `scripts/verify-static-site.py` — copy it, customize `PROJECT` path and `CHECKS`/`CSS_CHECKS` lists, then run.

## Data Pipeline: Excel/CSV → JS

When the source of truth is a spreadsheet:

1. **Extract** with openpyxl: read author, title, genre columns
2. **Clean**: replace newlines (`\n` → space), trim whitespace, collapse multi-spaces
3. **Escape**: backslashes and double-quotes for JS string literals
4. **Generate**: write `const dataName = [{...}, ...];` format
5. **Verify**: Node.js syntax check + field completeness check

Full working example with all edge cases handled: `references/excel-to-js-pipeline.py`

## Common Pitfall: Language Toggle + Dynamic Content

When a page has a language toggle (`data-lang-ru`/`data-lang-en`) that replaces `innerHTML`:

**Problem:** The toggle overwrites child elements that JS dynamically populated.

```html
<!-- BROKEN: toggle replaces innerHTML, wiping the dynamic span -->
<p data-lang-ru="Books: <span id='count'>N</span>">Books: <span id="count">521</span></p>
```

**Fix:** Separate the static label from the dynamic value:

```html
<!-- FIXED: label is its own element, count span is outside data-lang scope -->
<p><span data-lang-ru="Books:" data-lang-en="Books:">Books:</span> <span id="count">521</span></p>
```

## GitHub Pages Specifics

- Site is served from repo root — all paths relative
- `index.html` is the default page
- No server-side processing — all logic must be client-side JS
- CSS and JS are static files, cached aggressively by browsers (use cache-busting if needed)

### Pitfall: Stale Browser Cache After Deploy

After pushing to GitHub Pages, the user may see the old version even though the deploy succeeded. GitHub Pages itself updates within ~1 minute, but the browser holds cached copies of JS/CSS.

**Symptoms:** User reports "nothing changed" or "still broken" despite confirmed push.

**Fix:** Instruct the user to hard-refresh: **Cmd+Shift+R** (macOS) or **Ctrl+Shift+R** (Windows/Linux). This bypasses the cache and forces a full reload of all assets.

**Prevention:** Add cache-busting query strings to script/link tags after major updates:
```html
<script src="js/books.js?v=2"></script>
```

### Pitfall: Playwright Caches Stale JS (Agent-Side)

**Symptom:** After a GitHub Pages deploy, `curl` confirms the new file is live, but Playwright's browser still renders old content. Network inspection shows the same `x-fastly-request-id` across navigations — Playwright is serving from disk cache, not making new HTTP requests.

**Why:** Playwright's browser instance accumulates cache across tabs. Even `browser_navigate` to the same URL may hit the disk cache.

**Fix:**
- Open a **new tab** via `browser_tabs(action='new', url='...')` — new tabs bypass stale disk cache
- Alternatively, add `?nocache=TIMESTAMP` query param to the URL
- Verify with `curl` before Playwright — curl always gets the freshest CDN copy, confirming the deploy is complete

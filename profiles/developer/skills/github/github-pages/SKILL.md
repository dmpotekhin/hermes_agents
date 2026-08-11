---
name: github-pages
description: Deploy and debug GitHub Pages static sites — CDN propagation, cache invalidation, emoji/encoding pitfalls, and verification patterns.
---

# GitHub Pages Deploy & Debug

## When to use

- Deploying static sites to `*.github.io`
- Verifying that a deploy actually reached users
- Debugging "I pushed but the site hasn't updated"
- Working with JS-heavy pages that may have encoding/emoji issues

## Key Pitfalls

### 1. CDN propagation delay

After `git push`, GitHub Pages runs a build and deploys to Fastly CDN edge nodes. Different edge nodes update at different times. Your terminal curl may hit a node that has the new version while a browser in a different region gets a stale one.

**Wait time:** usually 1–2 minutes, occasionally up to 10 (cache-control: max-age=600).

**How to verify deployment:**
```bash
# Check headers to see which version the CDN is serving
curl -sI https://USER.github.io/js/file.js | grep -E 'last-modified|content-length|etag|x-served-by'
curl -s https://USER.github.io/js/file.js | grep -c 'EXPECTED_STRING'
```

If `last-modified` is stale and `content-length` is wrong, the edge node hasn't updated yet. Wait and retry.

### 2. User-side stale cache

Users may see old versions due to browser cache. They need **Cmd+Shift+R** (hard reload, bypass cache). A query string (`?v=2`) on the URL does NOT help for linked JS/CSS assets — it only affects the HTML itself.

### 3. JavaScript emoji regex surrogate-pair pitfall

In JavaScript, emoji characters above U+FFFF (most emojis: 📖, 🧠, 💻, 🌍) are represented as UTF-16 surrogate pairs (two code units). A regex character class like `/[📖🧠]/` matches individual code units, not full emojis. This silently breaks extraction.

**Wrong:**
```javascript
// Captures only one surrogate half — produces broken/garbled icon
const match = genre.match(/^([📖🧠💻🌍])\s*/);
icon.textContent = match ? match[1] : '📚'; // -> "\ud83d" (broken)
```

**Right:**
```javascript
// split on space keeps surrogate pairs intact
const parts = genre.split(' ');
icon.textContent = parts[0] || '📚'; // -> "📖" (correct)
```

Alternative correct approach: use `String.codePointAt()` or `Array.from()`.

### 4. i18n data-attribute vs dynamic content

When using `data-lang-ru`/`data-lang-en` attributes with `innerHTML` replacement, any child element with dynamically-updated content (e.g. `<span id="counter">521</span>`) will be overwritten when the language toggles, because the data attribute stores the HTML template.

**Fix:** Keep the dynamic child OUTSIDE the data-lang element, as a sibling span. Use separate `<span data-lang-ru="Label:" data-lang-en="Label:">` for the label and `<span id="counter">N</span>` for the number.

## Verification Script

Run `scripts/verify-deploy.sh USER REPO PATH EXPECTED_STRING` to confirm a deploy reached the CDN. The script checks headers (last-modified, content-length, edge node) and verifies expected content is in the response body.

Example:
```bash
bash ~/.hermes/profiles/developer/skills/github/github-pages/scripts/verify-deploy.sh dmpotekhin dmpotekhin.github.io js/books.js genreParts
```

# Vanilla JS Frontend Patterns

Proven patterns from Travel Content Factory SPA. Zero dependencies, dark theme, all browser-native APIs.

---

## API wrapper

```javascript
const API = {
    async get(url) {
        const r = await fetch(url);
        if (!r.ok) throw new Error(await r.text());
        return r.json();
    },
    async post(url, data) {
        const r = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!r.ok) throw new Error(await r.text());
        return r.json();
    },
    async del(url) {
        const r = await fetch(url, { method: 'DELETE' });
        if (!r.ok) throw new Error(await r.text());
        return r.json();
    },
};
```

Error body is read as text (not JSON) because FastAPI returns plain-text error details.

---

## Tab navigation

```javascript
document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        state.tab = tab.dataset.tab;
        document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
        document.getElementById(`tab-${state.tab}`).classList.add('active');
        if (state.tab === 'projects') loadProjects();
    });
});
```

State tracked in a global `state` object with `tab` field. Tab switch triggers data reload for content that may have changed.

---

## Modal pattern

```html
<div id="modal-render" class="modal hidden">
    <div class="modal-content">
        <span class="modal-close">&times;</span>
        <!-- content -->
    </div>
</div>
```

```css
.modal { position: fixed; inset: 0; z-index: 200; background: rgba(0,0,0,0.7);
         display: flex; align-items: center; justify-content: center; }
.modal.hidden { display: none; }
```

```javascript
// Close on × button — works for ALL modals
document.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', () => {
        btn.closest('.modal').classList.add('hidden');
    });
});

// Close on backdrop click
document.querySelectorAll('.modal').forEach(m => {
    m.addEventListener('click', (e) => {
        if (e.target === m) m.classList.add('hidden');
    });
});
```

The `.modal-close` handler uses `closest('.modal')` so one handler works for every modal.

---

## Toast notification

```javascript
function toast(msg, type = 'info') {
    const el = document.getElementById('toast');
    el.textContent = msg;
    el.className = `toast ${type}`;   // success | error | info
    setTimeout(() => el.classList.add('hidden'), 3000);
}
```

```css
.toast { position: fixed; bottom: 24px; right: 24px; z-index: 300; }
.toast.success { background: #1b5e20; color: #a5d6a7; }
.toast.error   { background: #b71c1c; color: #ef9a9a; }
.toast.info    { background: #1565c0; color: #90caf9; }
```

---

## Music upload (multipart/form-data)

```javascript
async function uploadMusic() {
    const input = document.getElementById('music-upload-input');
    if (!input.files.length) return;
    const file = input.files[0];
    const formData = new FormData();
    formData.append('file', file);

    const r = await fetch('/api/music/upload', {
        method: 'POST',
        body: formData       // no Content-Type header — browser sets it with boundary
    });
    if (!r.ok) throw new Error(await r.text());
    const data = await r.json();

    // Add to dropdown and select
    const sel = document.getElementById('render-music-select');
    const opt = document.createElement('option');
    opt.value = data.path;
    opt.textContent = `${data.filename} (${data.size_mb}MB)`;
    sel.appendChild(opt);
    sel.value = data.path;
}
```

**Critical:** when sending `FormData`, do NOT set `Content-Type` header — the browser auto-sets it with the correct multipart boundary.

---

## XSS-safe templating

```javascript
function esc(s) {
    if (!s) return '';
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
}
```

Use `esc()` for ALL user-provided strings before inserting into HTML. This prevents XSS without a framework.

---

## Debounced input

```javascript
function debounce(fn, ms) {
    let t;
    return (...args) => {
        clearTimeout(t);
        t = setTimeout(() => fn(...args), ms);
    };
}

document.getElementById('filter-hashtag').addEventListener('input',
    debounce(() => { state.archivePage = 1; loadMedia(); }, 400)
);
```

---

## Dark theme variables (CSS custom properties pattern)

The app uses hardcoded dark values rather than CSS custom properties for simplicity. Color palette:

| Token | Hex | Usage |
|-------|-----|-------|
| Background | `#0f0f14` | Page background |
| Surface | `#1a1a24` | Cards, modals, panels |
| Border | `#2a2a3a` / `#333` | Card borders, inputs |
| Primary | `#7c5cfc` | Buttons, active states, badges |
| Text | `#e0e0e0` | Body text |
| Muted | `#888` / `#666` | Labels, meta, placeholders |
| Success | `#1b5e20` / `#4caf50` | Toast, status badges |
| Error | `#b71c1c` / `#f44336` | Toast, status badges |
| Warning | `#6b5a00` / `#ffc107` | Processing status |

---\n\n## Captions toggle with conditional input\n\n```html\n<label style=\"display:flex;align-items:center;gap:8px;cursor:pointer\">\n    <input type=\"checkbox\" id=\"render-captions\" onchange=\"onCaptionsToggle()\">\n    <span>  AI-generated text captions on video</span>\n</label>\n<div id=\"caption-extra\" class=\"hidden\" style=\"margin-top:6px\">\n    <input type=\"text\" id=\"render-caption-text\"\n           placeholder=\"Or type your own caption for all clips...\">\n</div>\n```\n\n```javascript\nfunction onCaptionsToggle() {\n    const checked = document.getElementById('render-captions').checked;\n    document.getElementById('caption-extra').classList.toggle('hidden', !checked);\n}\n\n// Reset on dialog open:\ndocument.getElementById('render-captions').checked = false;\ndocument.getElementById('render-caption-text').value = '';\ndocument.getElementById('caption-extra').classList.add('hidden');\n\n// Pass to API:\nconst captions = document.getElementById('render-captions').checked;\nif (captions) {\n    body.add_captions = true;\n    const captionText = document.getElementById('render-caption-text').value.trim();\n    if (captionText) body.caption_text = captionText;\n}\n```\n\nPattern: checkbox controls visibility of a sibling div. On dialog close, all state resets. The API receives `add_captions: true` with optional `caption_text` — empty string means \"AI generate per clip\".\n\n---\n\n## Generic .hidden class — must exist

```css
.hidden { display: none !important; }
```

Without `!important`, it won't override `.modal { display: flex }`. Place it in the Reset section at the top of the stylesheet.

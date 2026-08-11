# Dark Theme as Default — No FOUC

Goal: serve dark theme by default, respect user's saved preference, and prevent flash of white on load.

## Pattern

Three coordinated changes:

### 1. CSS — dual selector for dark variables

```css
/* :root holds LIGHT variables (unchanged) */
:root { --bg-primary: #ffffff; --text-primary: #212529; ... }

/* Two selectors for dark — html.dark-theme (inline script) + body.dark-theme (JS toggle) */
html.dark-theme body,
body.dark-theme {
    --bg-primary: #1a1a1a;
    --text-primary: #f8f9fa;
    ...
}
```

### 2. HTML — inline script in `<head>` (runs before paint, no FOUC)

```html
<head>
    <link rel="stylesheet" href="css/styles.css">
    <script>
        (function() {
            var theme = localStorage.getItem('theme');
            if (theme === 'dark' || (!theme && window.matchMedia('(prefers-color-scheme: dark)').matches) || !theme) {
                document.documentElement.classList.add('dark-theme');
            }
        })();
    </script>
</head>
```

Logic: localStorage → OS preference → default to dark. Applied to `<html>` because `<body>` isn't parsed yet.

### 3. JS — toggle + persistence + `<html>` sync

```javascript
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    applyTheme(savedTheme);
}

function applyTheme(theme) {
    const body = document.body;
    const html = document.documentElement;
    const icon = document.querySelector('.theme-icon');

    if (theme === 'dark') {
        body.classList.add('dark-theme');
        html.classList.add('dark-theme');
        if (icon) icon.textContent = '☀️';   // sun = switch to light
    } else {
        body.classList.remove('dark-theme');
        html.classList.remove('dark-theme');
        if (icon) icon.textContent = '🌙';   // moon = switch to dark
    }
    localStorage.setItem('theme', theme);
}
```

## Why This Works

- **Inline script** runs synchronously before CSS paints → no white flash
- **`html.dark-theme body`** in CSS catches the class set by the inline script
- **`body.dark-theme`** catches the class set by JS toggle (backward compat)
- **localStorage persistence** means user's choice survives page reloads
- **`prefers-color-scheme`** respects OS preference when user hasn't chosen

## Verification

```python
# Check HTML has inline dark-theme script
assert 'localStorage.getItem(\'theme\')' in html
assert 'documentElement.classList.add(\'dark-theme\')' in html

# Check CSS has html.dark-theme selector
assert 'html.dark-theme body' in css

# Check JS defaults to 'dark'
assert "getItem('theme') || 'dark'" in js
assert 'html.classList.add(\'dark-theme\')' in js
```

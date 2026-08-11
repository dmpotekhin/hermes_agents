# Responsive Layout with clamp() — No Media Query Spaghetti

Goal: make a static site work from iPhone SE (320px) to 4K monitors without dozens of breakpoint-specific overrides.

## Core Pattern: clamp() for Everything

`clamp(MIN, PREFERRED, MAX)` lets values scale smoothly between breakpoints.

### Spacing Variables

```css
:root {
    --spacing-xs: clamp(0.25rem, 0.5vw, 0.5rem);
    --spacing-sm: clamp(0.5rem,  1vw,   1rem);
    --spacing-md: clamp(0.75rem, 1.5vw, 1.5rem);
    --spacing-lg: clamp(1rem,    2vw,   2rem);
    --spacing-xl: clamp(1.5rem,  3vw,   3rem);
}
```

On a 320px phone: `--spacing-xl` ≈ 1.5rem (not 3rem). On a 1920px monitor: hits the 3rem cap.

### Font Sizes

```css
h1 { font-size: clamp(1.75rem, 4vw,   2.5rem); }
h2 { font-size: clamp(1.5rem,  3.5vw, 2rem);   }
h3 { font-size: clamp(1.25rem, 3vw,   1.75rem); }
h4 { font-size: clamp(1.1rem,  2.5vw, 1.5rem);  }
```

No `h1 { 40px }` and separate `@media (max-width: 768px) { h1 { 28px } }`.

### Images That Scale

```css
.profile-photo {
    width:  clamp(140px, 20vw, 220px);
    height: clamp(140px, 20vw, 220px);
}
```

## Grids: auto-fit Instead of Fixed Columns

```css
/* BEFORE: fixed 4 columns → overflows on mobile */
.stats-grid { grid-template-columns: repeat(4, 1fr); }

/* AFTER: auto-fit with min — 4 on desktop, 2 on tablet, 1 on phone */
.stats-grid { grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); }
```

## Stack-on-Mobile, Row-on-Desktop

For filter/sort controls that should stack on mobile:

```css
.books-controls {
    display: grid;
    grid-template-columns: 1fr;          /* mobile: single column */
}

@media (min-width: 640px) {
    .books-controls {
        grid-template-columns: 2fr 1fr 1fr;  /* desktop: search + filter + sort */
    }
}
```

## Touch Targets

Apple HIG recommends ≥44px for touch targets. Ensure interactive elements hit this:

```css
@media (max-width: 480px) {
    .filter-section select,
    .sort-section select,
    .search-box input {
        min-height: 44px;
    }
}
```

## What to Keep in @media Queries

`clamp()` handles 80% of responsive needs, but keep media queries for:
- Layout restructuring (grid-template-columns, flex-direction)
- Visibility toggling (hide/show elements)
- Non-linear changes (font-weight, border-width)

## Verification

```python
css = open('styles.css').read()
checks = [
    ('clamp spacing', r'--spacing-xs:\s*clamp'),
    ('clamp headings', r'h1\s*\{[^}]*clamp'),
    ('auto-fit grids', r'auto-fit.*minmax'),
    ('touch 44px', r'min-height:\s*44px'),
]
for desc, pat in checks:
    assert re.search(pat, css, re.DOTALL), f'Missing: {desc}'
```

---
name: web-design-prototyping
description: "Design and prototype web artifacts — from polished one-off HTML (landing pages, decks, prototypes) to throwaway sketch variants for quick comparison. General design process, taste, and anti-slop rules."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [design, html, prototype, ux, ui, mockup, sketch, creative, artifact]
    category: creative
---

# Web Design & Prototyping

Two complementary modes for producing HTML design artifacts:
- **Polished artifact** (Section 1) — landing pages, decks, high-fidelity prototypes
- **Sketch variants** (Section 2) — 2-3 throwaway mockups to compare directions

Also see: `popular-web-designs` for ready-to-paste design systems.

---

## Section 1: Polished HTML Artifacts

### When to Use
Landing pages, slide decks, interactive prototypes, component labs, motion studies, visual option boards, design-system previews.

### Start From Context
Before designing, look for: brand docs, existing screenshots, repo components, design tokens, UI kits. If a repo exists, read source files before inventing UI.

### Artifact Format
- Single self-contained HTML file with embedded CSS/JS
- Responsive behavior unless intentionally fixed-size
- Real focus/hover states, prefers-reduced-motion handling
- Semantic HTML, CSS grid, CSS variables for tokens

### Variation Rules
Default to 3 options: Conservative (closest to existing), Strong-fit (best interpretation), Divergent (more novel). Explore layout, hierarchy, type, density, color, motion.

### Anti-Slop Rules
Avoid: aggressive gradients, glassmorphism by default, emoji unless brand uses them, generic SaaS cards, fake dashboards, stock-photo heroes, rainbow palettes, vague labels like "Insights" or "Growth".

### Content Discipline
No filler content. Every element must earn its place. No fake metrics, decorative stats, placeholder testimonials.

---

## Section 2: Sketch Variants (Throwaway Mockups)

### When to Use
User says "sketch this screen", "show me 2-3 takes", "compare layouts". Design direction isn't locked yet.

### Core Method: intake → variants → head-to-head → pick winner

### Intake (three questions)
1. "What should this feel like?"
2. "What apps/sites capture that feel?"
3. "What's the single most important action?"

### Variants (2-3)
Each is a complete HTML file with a different design stance (density, emphasis, layout). Realistic fake content, interactive, not static.

```html
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, ...; }
</style>
```

### Interactivity Bar
Click something → visible happens. One state transition. Hover affordances.

### Verification
Use browser tools to visually verify each variant.

### Head-to-Head Comparison
Opinionate with a comparison table, then let the user pick.

---

## CSS/HTML/JS Standards

- CSS grid, container queries, text-wrap: pretty
- Plain HTML/CSS/JS by default; React CDN only for complex state
- Mobile hit targets >= 44px

## Deck Rules
- Fixed-size canvas (1920x1080, 16:9) scaled to fit viewport
- Keyboard navigation, visible slide count
- 1-2 background colors max, sparse slides

## Color
- Use brand colors first; if none exists, define small system
- Prefer oklch for harmonious palettes
- Check WCAG contrast for text

## Typography
Choose deliberately: editorial (serif), software (precise sans), luxury (spacing discipline), technical (mono accents). Use type as hierarchy before adding boxes or color.

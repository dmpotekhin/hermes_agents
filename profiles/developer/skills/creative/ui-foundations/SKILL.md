---
name: ui-foundations
description: "Build UI without AI slop: intentional palettes and tokens."
author: Dmitry Potekhin (dmitrypotekhin), Hermes Agent
license: MIT
version: 0.1.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [ui, design, frontend, tokens]
    related_skills: [claude-design, popular-web-designs, architecture-diagram, static-site-maintenance]
---

# UI Foundations (anti-slop)

## When to Use

При любом создании/редактировании фронтенда: лендинги, дашборды, формы, чаты,
ИИ-приложения. Грузится первой — задаёт палитру, типографику и токены.

## Главное правило: не «VibeCode Purple»

НЕ бери по умолчанию:

- сине-фиолетовый / индиго / лавандовый градиент на кнопках и заголовках;
- шрифт Inter «просто потому что»;
- типовой скелет лендинга (hero → 3 карточки фич → CTA).

Если цвет/бренд не заданы — спроси или возьми одну из палитр ниже, а НЕ индиго.

## Готовые палитры (вместо индиго)

### Neutral Slate (дефолт для дашбордов/SaaS)
```css
:root {
  --background: #ffffff; --foreground: #0f172a; --muted: #f1f5f9;
  --border: #e2e8f0; --primary: #0f172a; --primary-fg: #ffffff;
  --accent: #2563eb; --ring: #94a3b8;
}
```

### Warm Editorial (лендинги, контент, «человечный» тон)
```css
:root {
  --background: #faf8f5; --foreground: #1c1917; --muted: #f5f0e8;
  --border: #e7e0d5; --primary: #1c1917; --primary-fg: #faf8f5;
  --accent: #c2410c; --ring: #a8a29e;
}
```

### Fresh Emerald (рост, финансы, health)
```css
:root {
  --background: #ffffff; --foreground: #052e16; --muted: #ecfdf5;
  --border: #d1fae5; --primary: #059669; --primary-fg: #ffffff;
  --accent: #047857; --ring: #6ee7b7;
}
```

### Mono Contrast (техно/дев-инструменты)
```css
:root {
  --background: #0a0a0a; --foreground: #fafafa; --muted: #171717;
  --border: #262626; --primary: #fafafa; --primary-fg: #0a0a0a;
  --accent: #f59e0b; --ring: #525252;
}
```

## Типографика (замена «просто Inter»)

- SaaS/нейтрально: Geist или IBM Plex Sans.
- Editorial/лендинг: заголовки — serif (Fraunces, Instrument Serif), текст — sans.
- Техно/дев: Geist Mono / JetBrains Mono для акцентов.

Правила: 1 шрифт для UI + максимум 1 акцентный; шкала 12/14/16/20/24/32/48;
line-height 1.5 для текста, 1.1–1.2 для заголовков.

## Токены (единый источник правды)

- Радиусы: `--radius-sm: 6px`, `--radius-md: 10px`, `--radius-lg: 16px`.
- Отступы: шаг 4px (4/8/12/16/24/32/48/64).
- Тени: мягкие `0 1px 2px rgba(0,0,0,.06)` → усиливай по elevation.

Никогда не хардкодь цвет/отступ/радиус — только через токены.

## Фундамент компонентов

Строй на **shadcn/ui** (ui.shadcn.com) — код в проекте, редактируй свободно.
Расширенный набор (в т.ч. под ИИ) — **coss.com/ui**.
См. также: `ui-components`, `ui-animations`, `ui-checklist`.

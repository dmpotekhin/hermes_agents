---
name: ui-animations
description: Keep UI animations fast and tasteful (<300ms).
author: Dmitry Potekhin (dmitrypotekhin), Hermes Agent
license: MIT
version: 0.1.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [ui, animations, motion, frontend]
    related_skills: [ui-foundations, claude-design]
---

# UI Animations

## When to Use

При добавлении любой анимации, перехода или микровзаимодействия.

## Каталог

- **transitions.dev** — готовые переходы и микроанимации: открытие модалок,
  скелетоны, анимация цифр, ресайз карточек. Код копируется или подключается
  как skill. База бесплатна.

## Правила умеренности (Эмиль Ковальски, автор sonner и vaul)

Источник: emilkowal.ski/ui/you-dont-need-animations

1. **Частые/повторяющиеся действия НЕ анимируй** — они раздражают.
2. **Держи анимации быстрее 300 мс:**
   - hover/focus: 100–150 мс;
   - появление/уход элементов: 150–250 мс;
   - крупные переходы: до 300 мс.
3. Анимация помогает понять, что произошло (откуда/куда элемент), а не украшает.
4. Уважай `prefers-reduced-motion` — отключай/упрощай анимации.
5. `ease-out` для появления, `ease-in` для ухода. Не `linear` для UI.

## Анти-паттерны

- Анимация каждого клика/тоста дольше 300 мс.
- Параллакс и «жидкие» эффекты в рабочих сценариях (дашборды, формы).
- Много одновременно движущихся элементов на экране.

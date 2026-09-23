---
name: ui-components
description: Catalog of UI component libraries, incl. AI interfaces.
author: Dmitry Potekhin (dmitrypotekhin), Hermes Agent
license: MIT
version: 0.1.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [ui, components, shadcn, frontend]
    related_skills: [ui-foundations, claude-design, popular-web-designs]
---

# UI Components

## When to Use

Когда нужно собрать конкретные блоки интерфейса, особенно для ИИ-приложений
(чаты, стриминг, подтверждения действий агента).

## База

- **shadcn/ui** (ui.shadcn.com) — фундамент, стандарт индустрии. Код в проекте,
  агент редактирует свободно. Установка: `npx shadcn@latest add <component>`.
- **coss.com/ui** — библиотека поверх базового UI, под ИИ-приложения. Опенсорс.

## Под ИИ-интерфейсы

- **beautifului.dev** — чаты, стриминг-лоадеры, блоки кода, карточки подтверждения
  действий агента, визуализация воркфлоу. Copy-paste, бесплатно.
- **beui.dev** — анимированные React/Next.js компоненты (Framer Motion + Tailwind):
  модалки, кнопки, табы, тосты, доки. Через shadcn CLI. База опенсорс, есть Pro.

## Акценты (дозированно)

- **rareui.com** — «вау»-компоненты (папки, гравитация букв, жидкий шар).
  Один файл, одна команда, бесплатно. Использовать редко, как акцент.

## Правила сборки

1. Ищи компонент по приоритету: shadcn/ui → coss.com/ui → beautifului/beui.
2. Не смешивай стили разных библиотек без приведения к общим токенам
   (см. `ui-foundations`).
3. Каждый интерактивный компонент обязан иметь состояния: `hover`,
   `focus-visible`, `disabled`, `loading`, `empty`, `error`.
4. Для ИИ-чатов обязательны: стриминг-индикатор, стоп-генерация, карточка
   подтверждения перед действием агента, отображение ошибки/ретрая.

## Обновление каталога ui-skills

Скиллы `improve-ui`, `baseline-ui`, `fixing-accessibility`,
`fixing-motion-performance` приходят из каталога **ui-skills.com**
(`github.com/ibelick/ui-skills`), ставится через Skills CLI:

```bash
npx skills add ibelick/ui-skills --skill improve-ui
npx skills add ibelick/ui-skills --skill baseline-ui
npx skills add ibelick/ui-skills --skill fixing-accessibility
npx skills add ibelick/ui-skills --skill fixing-motion-performance
```

Для массового обновления — `npx skills add ibelick/ui-skills`. Локальные копии в
`~/.hermes/profiles/developer/skills/creative/<name>/` адаптированы под Hermes
(description ≤60, `author`/`license`/`platforms`/`metadata.hermes.*`), поэтому
после переустановки стоит перепроверить frontmatter.


---
name: discuss
description: Use before planning. Captures implementation decisions.
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [planning, discuss, design-decisions, context]
    related_skills: [brainstorming, writing-plans, project-state]
---

# Discuss — Implementation Decisions Before Planning

## Когда использовать

**Всегда перед writing-plans для feature и architecture-change.**
Не для tiny-fix и quick-win.

Если задача уже прошла brainstorming (дизайн утверждён) — discuss фокусируется на implementation decisions, не на дизайне.
Если brainstorming не было — discuss покрывает и дизайн, и implementation.

**Когда discuss недостаточно — используй grill-me:**
- Проект новый или домен незнакомый → grill-me покрывает 3 слоя: бизнес, система, реализация
- Фича крупная, много неизвестных → grill-me вместо discuss
- Discuss = 5 вопросов, grill-me = исчерпывающее интервью
- После grill-me → discuss записывает CONTEXT.md из полученного design tree

## Почему

Planning не может начаться, пока неизвестно КАК строить, а не только ЧТО строить.
Без Discuss planner гадает — иногда правильно, часто правдоподобно, но ошибочно.
Ошибка в assumptions → план когерентный, но не соответствующий реальным предпочтениям.
К моменту обнаружения ошибки — часы переделок.

Discuss — это лёгкий разговор, не упражнение в спецификации.
Результат: CONTEXT.md — структурированная запись решений, которую читают planner, executor и verifier.

## Процесс

### Шаг 1: Загрузить контекст

Загрузить `project-state` skill и выполнить `state show`.

Прочитать (если существуют):
- `.planning/PROJECT.md` — описание проекта
- `.planning/ROADMAP.md` — дорожная карта
- `.planning/phases/<name>/CONTEXT.md` — предыдущие decisions

### Шаг 2: Понять цель

Спросить: «Что мы строим в этой фазе? Какая цель?»

Уточнить одним предложением. Записать как goal.

### Шаг 3: Задать решающие вопросы

По одному вопросу за раз. Порядок:

1. **Стек и зависимости:** какие библиотеки, фреймворки, версии? Есть ограничения?
2. **Стратегия обработки ошибок:** глобальный handler или per-route? Что с edge cases?
3. **Границы фазы:** что ВХОДИТ в эту фазу, что НЕ ВХОДИТ?
4. **Критерий готовности:** как мы узнаем, что фаза завершена?
5. **Открытые вопросы:** что ещё неясно и требует уточнения позже?

Не больше 5 вопросов. Если ответ очевиден из контекста — пропустить.

### Шаг 4: Записать CONTEXT.md

Создать `.planning/phases/<phase-name>/CONTEXT.md`:

```markdown
# Phase Context: [phase-name]

**Goal:** [одно предложение]

**Date:** YYYY-MM-DD

## Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | [что решили] | [почему] |
| D2 | [что решили] | [почему] |

## Constraints

- [ограничение 1]
- [ограничение 2]

## Out of Scope

- [что НЕ делаем в этой фазе]

## Acceptance Criteria

- [ ] AC1: [конкретный, проверяемый критерий]
- [ ] AC2: [конкретный, проверяемый критерий]

## Open Questions

- [ ] [вопрос для уточнения позже]
```

### Шаг 5: Обновить состояние

Загрузить `project-state` skill, выполнить `state update`:
- status: plan
- decisions: D1, D2, ... со статусом pending
- activity: «discuss: captured N decisions for phase <name>»

### Шаг 6: Предложить переход

«Decisions записаны в `.planning/phases/<name>/CONTEXT.md`. Готов перейти к planning?»

## Правила

- Не больше 5 вопросов — conversation, не specification exercise
- Каждое решение получает ID (D1, D2, ...) для отслеживания coverage
- Acceptance criteria — конкретные и проверяемые
- Out of Scope — явно, чтобы planner не ушёл в стороны
- CONTEXT.md — человекочитаемый Markdown, коммитится в git

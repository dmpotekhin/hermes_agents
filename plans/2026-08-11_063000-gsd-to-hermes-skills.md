# GSD Core → Hermes Skills: План адаптации

> **Для Hermes:** Реализовать через subagent-driven-development, каждая задача = один skill.

**Цель:** Адаптировать три ключевые идеи GSD Core в существующие Hermes-скиллы: Discuss (фиксация implementation decisions), STATE.md (файловое состояние), Verify+ (coverage check).

**Архитектура:** Три новых скилла + изменения в 3 существующих. Все артефакты — Markdown в `.planning/` проекта. Никаких внешних зависимостей.

---

## Карта покрытия GSD Core → Hermes

| Шаг GSD Core | Текущий Hermes | Что меняется |
|---|---|---|
| **Discuss** | brainstorming (design focus) | **НОВЫЙ** `discuss` — implementation decisions, не дизайн |
| **Plan** | writing-plans + plan | План читает CONTEXT.md перед генерацией |
| **Execute** | executing-plans + subagent-driven-development | Без изменений |
| **Verify** | verification-before-completion + requesting-code-review | **УСИЛИТЬ** coverage checks (requirement, decision, goal) |
| **Ship** | finishing-a-development-branch | Без изменений |
| **State** | memory + session_search | **НОВЫЙ** `project-state` — STATE.md в .planning/ |

---

## Task 1: Новый skill — `discuss` (Capture implementation decisions)

**Objective:** Создать skill, который запускается ПЕРЕД planning и фиксирует implementation decisions в CONTEXT.md.

**Файлы:**
- Create: `~/.hermes/profiles/developer/skills/software-development/discuss/SKILL.md`

**Спецификация скилла:**

```yaml
---
name: discuss
description: Use before planning any feature — captures implementation decisions (libraries, strategies, edge cases) into CONTEXT.md
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [planning, discuss, design-decisions, context]
    related_skills: [brainstorming, writing-plans, project-state]
---
```

### Содержание SKILL.md

```markdown
# Discuss — Implementation Decisions Before Planning

## Когда использовать

**Всегда перед writing-plans для feature и architecture-change.** 
Не для tiny-fix и quick-win.

## Почему

Planning не может начаться, пока неизвестно КАК строить, а не только ЧТО строить.
Без Discuss planner гадает — иногда правильно, часто правдоподобно, но ошибочно.
Ошибка в assumptions → план когерентный, но не соответствующий твоим реальным предпочтениям.
К моменту обнаружения ошибки — часы переделок.

Discuss — это лёгкий разговор, не упражнение в спецификации.
Результат: CONTEXT.md — структурированная запись решений, которую читают planner, executor и verifier.

## Процесс

### Шаг 1: Загрузить контекст проекта

Прочитать (если существуют):
- `.planning/PROJECT.md` — описание проекта
- `.planning/STATE.md` — текущее состояние
- `.planning/ROADMAP.md` — дорожная карта
- `CONTEXT.md` — предыдущие decisions (если есть)

### Шаг 2: Понять цель

Спросить пользователя: «Что мы строим в этой фазе? Какая цель?»

Уточнить одним предложением. Записать как goal в CONTEXT.md.

### Шаг 3: Задать решающие вопросы

По одному вопросу за раз. Порядок:
1. **Стек:** библиотеки, фреймворки, версии? Есть ограничения?
2. **Стратегия ошибок:** как обрабатывать ошибки? Глобально или per-route?
3. **Edge cases:** что насчёт пустого ввода, таймаутов, гонок?
4. **Границы фазы:** что ВХОДИТ в эту фазу, что НЕ ВХОДИТ?
5. **Критерий готовности:** как мы узнаем, что фаза завершена?

Не больше 5 вопросов. Это разговор, не допрос.

### Шаг 4: Записать CONTEXT.md

Сохранить в `.planning/phases/<phase-name>/CONTEXT.md`:

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

- [ ] AC1: [критерий]
- [ ] AC2: [критерий]

## Open Questions

- [ ] [вопрос, требующий уточнения позже]
```

### Шаг 5: Обновить STATE.md

Вызвать `project-state` skill для обновления состояния.

### Шаг 6: Предложить переход к planning

«Decisions записаны в `.planning/phases/<name>/CONTEXT.md`. Готов перейти к planning?»
```

---

## Task 2: Новый skill — `project-state` (STATE.md management)

**Objective:** Создать skill для управления файловым состоянием проекта через `.planning/STATE.md`.

**Файлы:**
- Create: `~/.hermes/profiles/developer/skills/software-development/project-state/SKILL.md`

### Содержание SKILL.md

```markdown
# Project State — File-Based Project Memory

## Когда использовать

Автоматически — при старте ЛЮБОГО workflow (discuss, plan, execute, verify, ship).
Вручную — `/state` для просмотра текущего состояния.

## Почему

AI-агенты не помнят, что делали в прошлой сессии.
STATE.md — это «spine» системы: файл, который переживает `/clear`, перезапуск и смену сессии.
Любой агент в любой момент может прочитать его и понять, где мы находимся.

## Формат STATE.md

```markdown
# Project State

**Project:** [имя проекта]

## Current Position

- **Milestone:** [M1: название]
- **Phase:** [P1: название] | статус: discuss|plan|execute|verify|ship|done
- **Last updated:** YYYY-MM-DD HH:MM

## Active Decisions

- D1: [decision] — status: pending|implemented|verified
- D2: [decision] — status: pending|implemented|verified

## Blockers

- [блокер] — [что нужно для разрешения]

## Progress

- [x] Phase 1: Auth — shipped 2026-08-01
- [ ] Phase 2: Dashboard — in plan
- [ ] Phase 3: Settings — not started

## Recent Activity

- YYYY-MM-DD HH:MM — discuss: captured decisions for Phase 2
- YYYY-MM-DD HH:MM — plan: generated PLAN-01.md, PLAN-02.md
```

## Команды

### `state init`

Создать `.planning/STATE.md` для проекта:

```
Initialize project state — прочитать PROJECT.md, ROADMAP.md (если есть), создать STATE.md.
```

### `state show`

Показать текущее состояние:

```
Прочитать .planning/STATE.md и вывести краткую сводку:
- Текущий milestone/phase
- Статус
- Активные decisions
- Блокеры
```

### `state update`

Обновить состояние (вызывается другими скиллами):

```
Обновить .planning/STATE.md:
- Current Position (milestone, phase, status)
- Active Decisions (пометить implemented/verified)
- Progress (пометить фазу shipped)
- Recent Activity (добавить запись)
```

## Интеграция с другими скиллами

- **discuss:** после записи CONTEXT.md → `state update` (статус: discuss → plan)
- **writing-plans:** перед планированием → `state show` (прочитать контекст)
- **executing-plans:** после каждого task → `state update` (пометить decision implemented)
- **verification-before-completion:** после проверки → `state update` (пометить decision verified)
- **finishing-a-development-branch:** после ship → `state update` (фаза done)

## Правила

- STATE.md НИКОГДА не удаляется — только дополняется
- Каждое изменение — новая запись в Recent Activity с timestamp
- Если STATE.md не существует при старте workflow → создать через `state init`
```

---

## Task 3: Усилить `verification-before-completion` — Coverage checks

**Objective:** Добавить в verification-before-completion проверку coverage: требований, решений и цели фазы.

**Файлы:**
- Modify: `~/.hermes/skills/superpowers/skills/verification-before-completion/SKILL.md`

**Изменения:** добавить новый раздел «Coverage Verification» ПОСЛЕ существующего «The Iron Law» и ДО «Common Failures».

### Добавляемый блок:

```markdown
## Coverage Verification (GSD-style)

Для feature и architecture-change — ПЕРЕД объявлением готовности:

### Шаг 1: Requirement Coverage

Если существует REQUIREMENTS.md или ROADMAP.md с REQ-ID:

1. Извлечь все REQ-ID из `.planning/REQUIREMENTS.md` или `.planning/ROADMAP.md`
2. Для каждого REQ-ID найти evidence в коде/тестах
3. Создать checklist:

```markdown
## Requirement Coverage

| REQ-ID | Description | Covered? | Evidence |
|--------|-------------|----------|----------|
| REQ-01 | [описание] | ✅ | tests/test_auth.py::test_login |
| REQ-02 | [описание] | ❌ | НЕТ РЕАЛИЗАЦИИ |
```

4. Если есть uncovered requirements → СТОП. Не «готово». Сгенерировать fix plan.

### Шаг 2: Decision Coverage

Если существует `.planning/phases/<name>/CONTEXT.md`:

1. Извлечь все decisions (D1, D2, ...)
2. Для каждого decision проверить, реализован ли он
3. Создать checklist:

```markdown
## Decision Coverage

| Decision | Description | Implemented? | Evidence |
|----------|-------------|--------------|----------|
| D1 | [решение] | ✅ | src/auth.py:45 |
| D2 | [решение] | ✅ | src/middleware.py:120 |
```

4. Если есть нереализованные decisions → СТОП. Сгенерировать fix plan.

### Шаг 3: Goal Alignment

Если существует `.planning/phases/<name>/CONTEXT.md` с фазой goal:

1. Прочитать goal
2. Проверить, что построенное соответствует цели
3. Проверить acceptance criteria (AC1, AC2, ...)

```markdown
## Goal Alignment

**Goal:** [из CONTEXT.md]
**Verdict:** aligned | partial | misaligned

**Acceptance Criteria:**
- [x] AC1: [критерий] — ✅
- [x] AC2: [критерий] — ✅
- [ ] AC3: [критерий] — ❌ НЕ ВЫПОЛНЕН
```

4. Если acceptance criteria не покрыты → СТОП.

### Интеграция

Coverage check выполняется ПОСЛЕ стандартной верификации (тесты, линтер, билд)
и ПЕРЕД объявлением «готово».
```

---

## Task 4: Обновить `writing-plans` — Reference CONTEXT.md

**Objective:** Перед генерацией плана проверять наличие CONTEXT.md и включать decisions в план.

**Файлы:**
- Modify: `~/.hermes/skills/superpowers/skills/writing-plans/SKILL.md`

**Изменения:** добавить после «Step 1: Understand Requirements» новый обязательный шаг.

### Добавляемый блок (вставить после строки «### Step 1: Understand Requirements»):

```markdown
### Step 1.5: Load Phase Context (GSD Discuss)

**Если задача — feature или architecture-change:**

1. Проверить существование `.planning/phases/<name>/CONTEXT.md`
2. Если существует — прочитать и извлечь:
   - Goal
   - Decisions (D1, D2, ...)
   - Constraints
   - Out of Scope
   - Acceptance Criteria
3. Если НЕ существует — спросить: «CONTEXT.md не найден. Запустить discuss для фиксации implementation decisions? (yes/no)»
4. При генерации плана:
   - Каждая задача плана должна ссылаться на relevant decisions (D1, D2)
   - Acceptance criteria из CONTEXT.md включаются в план как verification steps
   - Out of Scope explicitly помечается как «НЕ ДЕЛАТЬ»
```

---

## Task 5: Обновить `requesting-code-review` — Coverage checklist

**Objective:** Добавить в шаблон code review проверку coverage.

**Файлы:**
- Modify: `~/.hermes/skills/superpowers/skills/requesting-code-review/SKILL.md`

**Изменения:** добавить в секцию «How to Request» после пункта 2 упоминание CONTEXT.md.

### Добавляемый блок (вставить в секцию «How to Request», пункт 2):

```markdown
**2b. Если существует CONTEXT.md — включить в контекст ревьюера:**

```
В дополнение к плану, включи в ревью:
- CONTEXT_PATH: .planning/phases/<name>/CONTEXT.md
- Проверь decision coverage: все ли D1, D2, ... реализованы?
- Проверь acceptance criteria: все ли AC покрыты?
```
```

---

## Task 6: Обновить developer profile — Интеграция новых шагов в цикл

**Objective:** Обновить систему классификации задач в профиле разработчика, добавив discuss и project-state.

**Файлы:**
- Modify: `~/.hermes/profiles/developer/profiles/developer/system_prompt.md` (или где хранится профиль)

**Изменения:** добавить discuss в цикл feature/architecture-change.

### Текущий цикл (feature):
```
ПОЛНЫЙ ЦИКЛ: brainstorming → writing-plans → OK → RED/GREEN/REFACTOR → COMMIT →
  simplify-code → requesting-code-review → verification-before-completion → "Готово"
```

### Новый цикл (feature):
```
ПОЛНЫЙ ЦИКЛ: project-state (init) → discuss → brainstorming → writing-plans → OK →
  RED/GREEN/REFACTOR → COMMIT → simplify-code → requesting-code-review →
  verification-before-completion (с coverage check) → project-state (update) → "Готово"
```

**Добавить в «Обязательный процесс»:**

```markdown
**Перед задачей:**
1. project-state (прочитать STATE.md для ориентации)
2. Классифицировать задачу
3. Если feature/architecture-change и нет CONTEXT.md → discuss
4. ...
```

---

## Итоговая карта файлов

| Файл | Действие | Что меняется |
|------|----------|-------------|
| `skills/software-development/discuss/SKILL.md` | **Create** | Новый skill: implementation decisions |
| `skills/software-development/project-state/SKILL.md` | **Create** | Новый skill: STATE.md management |
| `superpowers/skills/verification-before-completion/SKILL.md` | **Modify** | +Coverage Verification раздел |
| `superpowers/skills/writing-plans/SKILL.md` | **Modify** | +Step 1.5: Load Phase Context |
| `superpowers/skills/requesting-code-review/SKILL.md` | **Modify** | +CONTEXT.md в контекст ревью |
| `profiles/developer/profiles/developer/` | **Modify** | +discuss и project-state в цикл |

---

## Порядок реализации

1. `project-state` (нужен всем остальным для STATE.md)
2. `discuss` (создаёт CONTEXT.md, обновляет STATE.md)
3. `writing-plans` (читает CONTEXT.md)
4. `verification-before-completion` (coverage checks)
5. `requesting-code-review` (CONTEXT.md в ревью)
6. Developer profile (интеграция в цикл)

---

## Проверка

После реализации всех изменений проверить на QA Interview Trainer:

1. `project-state init` → создан `.planning/STATE.md`
2. `discuss` → создан `.planning/phases/test/CONTEXT.md`
3. `plan` → план ссылается на decisions из CONTEXT.md
4. `execute` + `verify` → coverage checklist заполнен
5. `ship` → STATE.md обновлён, фаза помечена done

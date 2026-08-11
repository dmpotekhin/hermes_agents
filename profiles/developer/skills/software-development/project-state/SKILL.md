---
name: project-state
description: Use before any workflow. Manages .planning/STATE.md.
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [state, planning, context, persistence, project-management]
    related_skills: [discuss, writing-plans, executing-plans, verification-before-completion, finishing-a-development-branch]
---

# Project State — File-Based Project Memory

## Когда использовать

**Автоматически:**
- При старте ЛЮБОГО workflow (discuss, plan, execute, verify, ship) — `state show` для ориентации
- При завершении любого шага цикла — `state update` для фиксации прогресса

**Вручную:**
- `/state` — показать текущее состояние проекта
- `/state init` — создать STATE.md для нового проекта

## Почему

AI-агенты не помнят, что делали в прошлой сессии. memory tool ограничен 2200 символами и хранит статические факты, не динамическое состояние. session_search требует перечитывания истории.

STATE.md — файл, который переживает `/clear`, перезапуск и смену сессии. Любой агент в любой момент читает его и мгновенно понимает: на какой мы фазе, какие decisions активны, что сделано, что блокирует.

## Формат STATE.md

```markdown
# Project State

**Project:** [имя проекта]

## Current Position

- **Milestone:** [M1: название]
- **Phase:** [P1: название]
- **Status:** discuss | plan | execute | verify | ship | done
- **Current task:** [Task N/M — описание]
- **Last updated:** YYYY-MM-DD HH:MM

## Active Decisions

- [ ] D1: [decision text] — status: pending | implemented | verified
- [ ] D2: [decision text] — status: pending | implemented | verified

## Blockers

- [блокер] — [что нужно для разрешения]

## Progress

- [x] Phase 1: [название] — shipped YYYY-MM-DD
- [ ] Phase 2: [название] — in plan
- [ ] Phase 3: [название] — not started

## Recent Activity

- YYYY-MM-DD HH:MM — [workflow]: [что произошло]
```

## Процесс

### `state init` — Инициализация

Вызывается когда `.planning/STATE.md` не существует.

1. Проверить существование `.planning/PROJECT.md` или `README.md` — извлечь имя проекта
2. Если нет — спросить пользователя: «Как называется проект?»
3. Проверить `.planning/ROADMAP.md` — извлечь milestones и phases
4. Создать `.planning/STATE.md` с начальным состоянием:

```markdown
# Project State

**Project:** [имя]

## Current Position

- **Milestone:** M1 — [первый milestone из ROADMAP или «Initial»]
- **Phase:** P1 — [первая фаза или «Setup»]
- **Status:** discuss
- **Current task:** не начата
- **Last updated:** [текущая дата/время]

## Active Decisions

(пока нет)

## Blockers

(пока нет)

## Progress

(фазы ещё не завершены)

## Recent Activity

- [timestamp] — state: initialized project state
```

5. Сообщить: «Project state инициализирован: `.planning/STATE.md`»

### `state show` — Показать состояние

Вызывается при старте любого workflow.

1. Прочитать `.planning/STATE.md`
2. Вывести краткую сводку:

```
Project: QA Interview Trainer
Phase: P2-OAuth | Status: execute | Task 3/5
Active decisions: D1 (implemented), D2 (implemented)
Blockers: нет
Last activity: 2026-08-10 18:30 — execute: completed Task 2/5
```

3. Если файла нет — запустить `state init`

### `state update` — Обновить состояние

Вызывается другими скиллами при завершении шага.

**Параметры (через контекст вызова):**
- `status` — новый статус фазы (discuss|plan|execute|verify|ship|done)
- `task` — текущая задача (опционально)
- `decision_id` — ID решения для обновления (опционально)
- `decision_status` — новый статус решения (опционально)
- `blocker` — добавить/убрать блокер (опционально)
- `phase_done` — имя завершённой фазы (опционально)
- `activity` — описание последнего действия

**Действия:**
1. Прочитать текущий STATE.md
2. Обновить секцию Current Position (status, task, timestamp)
3. Если передан decision_id — обновить статус в Active Decisions
4. Если передан blocker — добавить/убрать из Blockers
5. Если передана phase_done — перенести фазу из Current в Progress с [x]
6. Добавить запись в Recent Activity с timestamp
7. Записать обновлённый STATE.md

## Интеграция с другими скиллами

| Скилл | Когда вызывает | Что обновляет |
|-------|---------------|---------------|
| `discuss` | После записи CONTEXT.md | status: discuss→plan, добавляет decisions |
| `writing-plans` | Перед планированием | `state show` для ориентации |
| `executing-plans` | После каждого task | task progress, decision→implemented |
| `verification-before-completion` | После coverage check | decision→verified |
| `finishing-a-development-branch` | После ship | фаза→done, status→следующая фаза |

## Правила

- STATE.md НИКОГДА не удаляется — только дополняется и обновляется
- Каждое изменение — новая запись в Recent Activity с timestamp
- Формат — человекочитаемый Markdown, можно коммитить в git
- Если STATE.md не существует при старте workflow → автоматический `state init`
- Блокеры отображаются prominently — агент НЕ продолжает фазу с активным блокером

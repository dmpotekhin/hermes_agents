---
name: precommit-quality-gate
description: Use when adding quality pre-commit hooks to any repo.
version: 1.0.0
author: dmitrypotekhin
license: MIT
metadata:
  hermes:
    tags: [quality-gate, pre-commit, pre-push, lint-staged, ruff, eslint, ai-agents]
    related_skills: [travel-media-admin]
---

# Pre-Commit Quality Gate (для ИИ-агентов)

## Overview
Жёсткая техническая граница поверх работы ИИ-агента. LLM предсказывает токены,
поэтому даже с инструкциями не гарантирует корректный результат на 100%. Хук
физически блокирует коммит со сломанным/нелинованным кодом — независимо от
«решения» агента. Это дополнительный сигнал: коммит не прошёл → агент чинит.

## When to Use
- Setup or audit a quality gate (lint + tests) in a repo driven by an AI agent.
- Any repo where an LLM (Claude/Codex/etc.) commits code and you want to physically
  block broken or unlinted commits — not just rely on "the agent should test".
- Adapting the gate to a Python / Node / mixed / Docker-based project.
- NOT for projects that already run lint + tests in CI on every PR (that's fine too,
  but this is the local "before you commit" wall).

## Три сигнала качества
1. Автотесты — агент гоняет при изменениях.
2. Визуальный (браузер/Playwright) — что реально отрисовывается.
3. Инфраструктурный (pre-commit/pre-push хук) — блокирует коммит при поломке.

## Правило распределения проверок
- **pre-commit** (быстрые, staged-файлы): синтаксис + линт staged `.py`/`.js`.
  Должно жить в пределах ~1-3 сек.
- **pre-push** (тяжёлые, полные): полный линт + тесты + сборка (нужны БД/инфра).
- Критичные для рабочего кода e2e можно перенести в pre-commit с учётом
  компромисса (нужна поднятая БД).

## Переносимый шаблон хука
См. `scripts/precommit-quality-gate.sh`. Скопировать в
`<repo>/.git/hooks/pre-commit` и `chmod +x`. Шаблон отказоустойчивый: если
инструмент не установлен — предупреждает, НЕ блокирует; блокирует реальный
провал линта/синтаксиса. Путь к eslint-директории может требовать правки под
конкретный репо (см. адаптацию).

## Матрица адаптации (какой инструмент — какому стеку)
| Стек | Линт | Формат | Тест | Установка |
|------|------|--------|------|-----------|
| Python | ruff | ruff format | pytest | `pip install --user ruff pytest` |
| Node/React | eslint | prettier | vitest/jest | `npm i -D eslint prettier` |
| Monorepo (Python+Node) | ruff + eslint | ruff + prettier | pytest + vite build | см. выше |
| Docker-based | хуки на ХОСТЕ лёгкими (ruff/syntax), тяжёлые — опционально | | | |
| Нет инструментов | начать с ruff + py_compile (Python), eslint + vite build (JS) | | | |

## Установка инструментов на хост
- Python (нужен только ruff для линта — НЕ требует зависимостей проекта):
  `pip install --user ruff` (+ `pytest` по желанию).
- Frontend: `cd <frontend-dir> && npm i -D eslint prettier`, добавить конфиги и
  скрипты `lint`/`format:check` в `package.json`.

## Бонус из урока
- Playwright-скриншоты складывать в `screenshots/` и добавить её в `.gitignore`,
  чтобы не засорять репо.

## Common Mistakes / Pitfalls
- **КРИТИЧНО: `set -o pipefail`** в хуке. Без него любой `cmd | tee file`
  сообщает код `tee` (обычно 0), поэтому упавший линт/тест НЕ заблокирует коммит —
  гейт молча пропускает. Это причина №1 «хук не блокирует».
- **Host Node ≠ runtime Node**: хуки гоняются с Node хоста (shell PATH). Если код
  требует новый Node (напр. Vite 18+), а на хосте старый (14), пинай eslint на
  совместимый с хостом мажор (eslint@8 для Node 14), а проверки, требующие нового
  Node (vite build), делай отказоустойчивыми (предупредить, не блокировать) —
  иначе хук будет ложно валить коммиты.
- **ruff --fix может править существующие файлы** (сортировка импортов, удаление
  неиспользуемых) при чистке базлайна — коммить эти правки как часть настройки.
- Хук должен быть **отказоустойчивым** (`command -v tool` → warn), иначе сломанный
  бинарь сам валит все коммиты.
- **Никогда `git commit --no-verify` по привычке** — это и есть обход замка.
- Для монрепо не тянуть Husky (нужен root package.json) — достаточно bash-хука
  на уровне repo, как здесь.
- pytest/тяжёлые проверки — в pre-push, чтобы не тормозить каждый коммит.
- Если Docker сломан, гонять НА ХОСТЕ лёгкие проверки (ruff/синтаксис), не в
  контейнере.

## Verification
- После настройки специально сломать код (убрать импорт) → `git commit` должен
  заблокировать → агент чинит → коммит проходит.
- `git -C <repo> log --oneline -1` — убедиться, что коммит прошёл.

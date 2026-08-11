---
name: grilling
description: "Use when the user wants to stress-test their thinking, needs a plan sharpened, or triggers with 'grill', 'interview', 'проясни', 'разбери'. Reusable interview primitive — relentlessly maps a design tree to shared understanding."
version: 1.0.0
author: Hermes Agent (adapted from mattpocock/skills)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [grilling, interview, planning, design-review, decision-tree]
    related_skills: [grill-me]
---

# Grilling

## Overview

Interview the user relentlessly until you reach a shared understanding of a plan, decision, or idea. Map this as a **design tree**: every decision branches into the decisions that hang off it.

This is the reusable interview primitive behind `grill-me`. Load it when any skill needs to walk a decision tree with the user.

**Core principle:** every branch of the design tree must be visited. Nothing left silently assumed.

## When to Use

- User says: "grill me", "interview me", "stress-test this", "проясни план", "разбери решение"
- Another skill delegates a decision-tree walk (grill-me, improve-codebase-architecture, triage)
- Any situation where assumptions need to be surfaced before building

**Don't use for:**
- Simple yes/no confirmation (use `clarify`)
- Gathering facts the agent can look up itself
- User explicitly says "just do it, don't ask questions"

## The Algorithm

### The Three Layers

Every grilling session must cover three layers in order. The frontier is not empty until each layer has been systematically visited. Skipping a layer is the #1 cause of missed requirements and late-stage rework.

**Layer 1: Business & Domain** — зачем мы это делаем?

- **Problem:** Какую проблему решаем? Для кого? Что произойдёт, если не решить?
- **Users:** Кто пользователи? Какие у них роли? Как они работают сейчас (as-is)?
- **Value:** Как измеряем успех? Какие метрики? Что такое «готово» с точки зрения бизнеса?
- **Stakeholders:** Кто ещё затронут? Какие у них ожидания и ограничения?
- **Domain constraints:** Юридические, compliance, отраслевые стандарты, регуляторные требования?
- **Competitive context:** Есть ли аналоги? Чем отличаемся? Что пользователи ожидают по умолчанию?

**Layer 2: System & Integration** — как это работает в существующей системе?

- **System landscape:** С какими системами взаимодействуем? Какие API, БД, внешние сервисы?
- **Data flows:** Какие данные входят, какие выходят? Где хранятся? Кто владелец данных?
- **Dependencies:** Что должно работать, чтобы это работало? Что ломается, если зависимость недоступна?
- **Boundaries:** Где границы нашей системы? Что внутри, что снаружи? Кто отвечает за стыки?
- **Scale & load:** Ожидаемая нагрузка? Пики? Ограничения по ресурсам?
- **Security model:** Аутентификация, авторизация, данные (PII?), threat model?

**Layer 3: Implementation** — как мы это строим?

- **Tech choices:** Языки, фреймворки, библиотеки, версии? Почему?
- **Error strategy:** Глобально или per-route? Retry, circuit breaker, fallback?
- **Edge cases:** Пустой ввод, таймауты, гонки, частичные отказы?
- **Testing strategy:** Уровни тестирования? Интеграционные vs unit? Test data?
- **Deployment:** Как деплоим? Миграции? Rollback? Мониторинг?
- **Scope:** Что входит в эту фазу, что НЕ входит?

### Layer Enforcement Rules

- Каждый раунд grilling должен явно указывать, какой слой обрабатывается
- Не переходить к следующему слою, пока текущий не имеет пустого frontier
- Если ответ пользователя на вопрос слоя 1 вскрывает неизвестные системные факты — не спрашивать пользователя, исследовать самому (fact-finding rule)
- Layer 3 (implementation) — самая знакомая территория, её часто хочется начать первой. Не поддаваться. Бизнес и система сначала.

### Design Tree

Every decision branches into sub-decisions. The **frontier** is every decision whose prerequisites are already settled — the questions you can ask _now_ without guessing at answers you haven't heard yet.

### Round Structure

Work the tree in **rounds**:

1. **Compute the frontier** — which questions can be asked given what's already settled?
2. **Ask the whole frontier** in one round: number each question, give your recommended answer
3. **Wait** for the user's answers
4. **Recompute** — settled decisions push the frontier outward, unblocking new questions
5. **Repeat** until the frontier is empty

### Question Format

Each question must follow this exact format:

```
❓ **Q1** — **<question title>**: <question body — may be multiple paragraphs, with choices>

➡️ <your recommended answer with reasoning>
```

### Fact-Finding Rule

Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, codebase, git log, web search), use your tools to find it — don't ask the user.

If a fact-finding exploration is slow, dispatch a sub-agent (`delegate_task`) and don't block on it. A running exploration is an unsettled prerequisite — only questions downstream of it wait. Ask the rest of the frontier now.

The _decisions_ are the user's — put each to them and wait.

### Completion

The session is done when the frontier is empty: every branch visited, nothing left silently assumed.

**Do not act** on the resolved tree until the user confirms: "We have reached a shared understanding. Ready to proceed?"

## Hermes-Specific Notes

- Use `clarify` for simple yes/no confirmations — grilling is for design trees
- For codebase exploration during grilling, use `delegate_task` to avoid flooding context
- Respect the user's time: batch frontier questions into one round, don't ask one-by-one

## Common Pitfalls

1. **Asking fact-finding questions.** "What does the git log show?" — your job, not the user's. Use tools.
2. **Diving one branch to exhaustion.** Stay breadth-first: ask the whole frontier before drilling deeper on any branch.
3. **Recommending without reasoning.** Every ➡️ must include _why_ you recommend it.
4. **Skipping the confirmation.** Don't start building until the user confirms shared understanding.
5. **Premature completion.** If you can still ask "but what about...?", the frontier is not empty.

## Verification Checklist

- [ ] Design tree fully mapped — no branch silently assumed
- [ ] Every frontier question was asked and answered
- [ ] All fact-finding was done by the agent (not delegated to the user)
- [ ] User confirmed shared understanding before any action taken
- [ ] Recommended answers included reasoning

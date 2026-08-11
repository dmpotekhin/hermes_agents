---
name: grill-me
description: "Use when the user says 'grill me', 'проясни задачу', 'проверь мой план', or wants a relentless interview to sharpen a plan or design before implementation. User-invoked entry point for the grilling interview."
version: 1.0.0
author: Hermes Agent (adapted from mattpocock/skills)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [grilling, interview, planning, design-review, user-invoked]
    related_skills: [grilling, brainstorming, writing-plans]
---

# Grill Me

## Overview

Get relentlessly interviewed about a plan, design, or idea until every branch of the decision tree is resolved. This is the user-facing entry point — it immediately delegates to the `grilling` skill.

The interview covers three layers in order:
1. **Business & Domain** — problem, users, value, stakeholders, constraints
2. **System & Integration** — data flows, dependencies, boundaries, scale, security
3. **Implementation** — tech choices, error strategy, edge cases, deployment

Most AI-coding failures happen because agents jump straight to layer 3. By the time layer 1 questions surface, code has already been written against wrong assumptions. Grilling forces the conversation to start at the top.

Use this _every_ time you're about to build something non-trivial. The grilling session forces you to think through edge cases, surface assumptions, and settle design decisions _before_ code is written. It's the single highest-leverage skill for avoiding misalignment between you and the agent.

## When to Use

- Before implementing any non-trivial feature
- When you have a rough idea but haven't thought through details
- When a previous implementation went wrong due to missed requirements
- User says: "grill me", "interview me", "проясни", "разбери мой план", "проверь"

**Don't use for:**
- Trivial one-line changes
- When you already have a detailed, reviewed spec
- Emergency hotfixes where speed > design quality

## Process

1. **Acknowledge:** "Starting grilling session. What are we building?"

2. **Load grilling skill:** The `grilling` skill contains the full interview algorithm. Follow it exactly:
   - Map decisions as a design tree
   - Work in rounds: ask the whole frontier, wait for answers, recompute
   - Never ask the user for facts you can look up yourself
   - Format each question as `❓ Q<N> — <title>: <body> ➡️ <recommendation>`

3. **Continue until frontier is empty** — every branch visited, nothing left silently assumed.

4. **Confirm:** "We have reached a shared understanding. Ready to proceed?"

5. **Do NOT start building** until the user explicitly confirms.

## Integration with Developer Profile

After a grilling session completes:
- **If this was a feature kickoff** → use `discuss` to write CONTEXT.md from the resolved design tree (grilling covered all 3 layers, discuss captures the implementation subset)
- **If this was design exploration** → use `domain-modeling` to update CONTEXT.md
- **If this produced a spec** → use `to-spec` to publish it
- **Then** → `project-state` update: phase status → plan, decisions recorded

### Grill vs Discuss

| | grill-me | discuss |
|---|---|---|
| **Глубина** | Все 3 слоя (бизнес→система→реализация) | Фокус на implementation (слой 3) |
| **Формат** | Интерактивное интервью, много раундов | 5 вопросов, один проход |
| **Когда** | Перед крупными фичами, новый проект, сложный домен | Перед каждой feature (автоматически) |
| **Кто инициирует** | Пользователь: «grill me» | Агент: автоматически перед planning |
| **Результат** | Полный design tree | CONTEXT.md с decisions |

**Правило:** если фича крупная или домен незнакомый — grill-me вместо discuss. Если фича стандартная — достаточно discuss.

## Common Pitfalls

1. **Skipping grilling because "it's simple".** Simple ideas hide assumptions. Grill anyway.
2. **Letting the agent dive deep on one branch.** Insist on breadth-first: the whole frontier before drilling.
3. **Not giving recommended answers.** The agent's recommendation anchors the discussion — even if the user disagrees, they now know what to disagree with.
4. **Treating grilling as a one-question confirm.** It's a session — expect 3-7 rounds depending on complexity.

## Verification Checklist

- [ ] Grilling session completed with empty frontier
- [ ] User confirmed shared understanding
- [ ] Design tree decisions are documented (mentally or in notes)
- [ ] Next action decided: plan, spec, or direct implementation

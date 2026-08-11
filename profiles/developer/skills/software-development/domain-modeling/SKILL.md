---
name: domain-modeling
description: "Use when the user wants to pin down domain terminology, build a ubiquitous language, record an architectural decision (ADR), or when another skill needs to maintain the domain model. Actively challenges terms and stress-tests with edge cases."
version: 1.0.0
author: Hermes Agent (adapted from mattpocock/skills)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [domain-modeling, ubiquitous-language, ddd, glossary, adr]
    related_skills: [grill-me, codebase-inspection, improve-codebase-architecture]
---

# Domain Modeling

## Overview

Actively build and sharpen a project's domain model as you design. This is the **active** discipline — challenging terms, inventing edge-case scenarios, and writing the glossary and decisions down the moment they crystallize.

Merely _reading_ CONTEXT.md for vocabulary is not this skill — that's a one-line habit. This skill is for when you're **changing the model**, not just consuming it.

The goal: a shared, precise language (ubiquitous language) that both the agent and the developer use consistently. This concision pays off session after session: variables, functions, and files are named consistently, the codebase is easier to navigate, and the agent spends fewer tokens on thinking.

## When to Use

- User uses a term ambiguously — "account" might mean Customer or User
- A new concept emerges during discussion that needs a canonical name
- A design decision is made that future readers will find surprising
- After a grilling session that resolved domain questions
- During code review when you notice inconsistent terminology

**Don't use for:**
- Every minor naming decision — only when ambiguity matters
- Decisions that are self-evident to future readers (skip the ADR)
- One-off variable names inside a function

## File Structure

Most projects use a single context:

```
/
├── CONTEXT.md          ← domain glossary
├── docs/
│   └── adr/
│       ├── 0001-<decision-slug>.md
│       └── 0002-<decision-slug>.md
└── src/
```

If a `CONTEXT-MAP.md` exists at the root, the project has multiple bounded contexts. The map points to where each one lives:

```
/
├── CONTEXT-MAP.md
├── docs/
│   └── adr/                              ← system-wide decisions
├── src/
│   ├── ordering/
│   │   ├── CONTEXT.md                    ← ordering context glossary
│   │   └── docs/adr/                     ← ordering context decisions
│   └── billing/
│       ├── CONTEXT.md
│       └── docs/adr/
```

Create files lazily — only when you have something to write. If no `CONTEXT.md` exists, create one when the first term is resolved.

## During the Session

### Challenge Against the Glossary

When the user uses a term that conflicts with the existing language in `CONTEXT.md`, call it out immediately:

> "Your glossary defines 'cancellation' as X, but you seem to mean Y — which is it?"

### Sharpen Fuzzy Language

When the user uses vague or overloaded terms, propose a precise canonical term:

> "You're saying 'account' — do you mean the Customer or the User? Those are different things."

### Stress-Test with Concrete Scenarios

When domain relationships are being discussed, stress-test them with specific edge-case scenarios. Invent scenarios that probe the boundaries between concepts:

> "What happens when a Customer has zero Orders but tries to cancel? Is that a Customer cancellation or an Order cancellation?"

### Cross-Reference with Code

When the user states how something works, check whether the code agrees. If you find a contradiction, surface it:

> "Your code cancels entire Orders, but you just said partial cancellation is possible — which is right?"

### Update CONTEXT.md Inline

When a term is resolved, update `CONTEXT.md` right there. Don't batch these up — capture them as they happen.

`CONTEXT.md` format:

```markdown
# Domain Glossary

## <Term Name>
<Precise definition. No implementation details.>

## <Another Term>
<Definition.>
```

`CONTEXT.md` should be totally devoid of implementation details. It is a glossary, not a spec, scratch pad, or repository for implementation decisions.

### Offer ADRs Sparingly

Only offer to create an ADR when **all three** are true:

1. **Hard to reverse** — the cost of changing your mind later is meaningful
2. **Surprising without context** — a future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

If any of the three is missing, skip the ADR. Don't create ADRs for self-evident decisions.

ADR format:

```markdown
# ADR-000N: <Title>

## Status
Accepted

## Context
What was the situation? What forces were at play?

## Decision
What did we decide and why?

## Consequences
What becomes easier? What becomes harder?
```

## Hermes-Specific Notes

- Read `CONTEXT.md` with `read_file` before any domain-sensitive work
- Use `delegate_task` for cross-referencing code against domain claims (avoids context pollution)
- When creating the first ADR, also create `docs/adr/` directory
- The `improve-codebase-architecture` skill feeds into domain modeling when it discovers unnamed concepts

## Common Pitfalls

1. **Creating ADRs for everything.** Only when all three criteria are met. Most decisions don't need an ADR.
2. **Putting implementation details in CONTEXT.md.** It's a glossary. "Customer: a person who places orders." Not "Customer: stored in PostgreSQL with columns id, name, email."
3. **Batching glossary updates.** Update inline — by the time you batch, you've forgotten the nuance.
4. **Not challenging the user.** The value is in the friction. If the user says "account" and you know they might mean two things, say so.
5. **Skipping cross-reference with code.** The code is ground truth. If code and user disagree, surface the contradiction.

## Verification Checklist

- [ ] CONTEXT.md exists and uses precise, implementation-free definitions
- [ ] All terms used in the current session are consistent with CONTEXT.md
- [ ] Fuzzy terms were challenged and sharpened
- [ ] Edge-case scenarios were stress-tested
- [ ] Cross-reference with code completed (no contradictions found or surfaced)
- [ ] ADRs created only when all three criteria met
- [ ] Glossary updates were inline, not batched

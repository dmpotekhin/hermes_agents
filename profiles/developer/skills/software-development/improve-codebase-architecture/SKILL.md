---
name: improve-codebase-architecture
description: "Use when the user says 'review architecture', 'improve design', 'глубокие модули', or wants to find deepening opportunities. Scans a codebase for architectural friction, presents candidates as a visual HTML report, then grills through the chosen one."
version: 1.0.0
author: Hermes Agent (adapted from mattpocock/skills)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [architecture, refactoring, deep-modules, code-quality, design-review]
    related_skills: [grilling, domain-modeling, codebase-inspection, two-axis-code-review]
---

# Improve Codebase Architecture

## Overview

Surface architectural friction and propose **deepening opportunities** — refactors that turn shallow modules into deep ones (a lot of behavior behind a small interface, placed at a clean seam, testable through that interface).

Run this every few days on your codebase. It is a **survey**, not a rescue: it finds candidates, presents them visually, and lets you pick which to explore. It does not untangle the mud for you.

## When to Use

- User says: "review architecture", "improve design", "find deep modules", "глубокие модули", "архитектура"
- After several features have been added — to catch emerging shallowness
- After a bug that was hard to fix because of poor test seams (post-mortem from `systematic-debugging`)
- During regular codebase maintenance (every few days)

**Don't use for:**
- Code review of a specific PR — use `two-axis-code-review`
- Debugging a specific bug — use `systematic-debugging`
- Greenfield design — use `grill-me` + `domain-modeling`

## Architecture Vocabulary

Use these exact terms (don't drift into "component", "service", "API", "boundary"):

| Term | Definition |
|------|-----------|
| **Module** | A unit of code with an interface and an implementation |
| **Interface** | What a module exposes — the contract callers depend on |
| **Depth** | Ratio of behavior to interface complexity. Deep = lots of behavior, small interface |
| **Seam** | A place where behavior can be varied or tested without changing the module |
| **Adapter** | Code that connects a module at a seam. One adapter = hypothetical seam, two = real |
| **Leverage** | How much behavior a small interface change unlocks |
| **Locality** | Whether understanding a piece of code requires reading distant code |

Key principles:
- **The deletion test:** would deleting this module concentrate complexity, or just move it? "Concentrates" is the signal.
- **The interface is the test surface:** if the interface is testable, the module is testable.
- **One adapter = hypothetical seam, two = real.** Don't abstract until you have at least two real use cases.

## Process

### 1. Scope

**Scope before you scan.** Deepening a module pays off by making future changes easier — put extra weight on parts that have recently changed.

- If the user named a direction (module, subsystem, pain point) — take it
- Otherwise: walk recent git history to find hot spots
- If changes are scattered with no clear hot spot, widen to the whole codebase

Read `CONTEXT.md` and relevant ADRs first — they name the seams and record past decisions.

### 2. Explore

Spawn a sub-agent (`delegate_task`) to walk the codebase. Don't follow rigid heuristics — explore organically and note friction:

- Where does understanding one concept require bouncing between many small modules?
- Where are modules **shallow** — interface nearly as complex as the implementation?
- Where have pure functions been extracted just for testability, but real bugs hide in how they're called (no **locality**)?
- Where do tightly-coupled modules leak across their seams?
- Which parts are untested, or hard to test through their current interface?

Apply the **deletion test** to anything you suspect is shallow.

### 3. Present Candidates as HTML Report

Write a self-contained HTML file to the OS temp directory. Resolve via `$TMPDIR`, falling back to `/tmp`. Write to `<tmpdir>/architecture-review-<timestamp>.html`.

Open it for the user: `open <path>` on macOS, `xdg-open` on Linux.

The report uses **Tailwind via CDN** for styling and **Mermaid via CDN** for diagrams. Each candidate gets a card with:

- **Files** — which files/modules are involved
- **Problem** — why the current architecture causes friction
- **Solution** — plain English description of what would change
- **Benefits** — in terms of locality, leverage, and testability improvements
- **Before/After diagram** — side-by-side, showing the shallowness and the deepening
- **Recommendation strength** — badge: `Strong`, `Worth exploring`, or `Speculative`

End with a **Top recommendation** section: which candidate you'd tackle first and why.

Use CONTEXT.md vocabulary for the domain. Don't propose interfaces yet — that comes in the grilling phase.

### 4. Grilling Loop

Once the user picks a candidate, run the `grilling` skill to walk the decision tree:

- Constraints and dependencies
- Shape of the deepened module
- What sits behind the seam
- What tests survive the refactor

Side effects happen inline as decisions crystallize:

- **New concept named?** Add it to CONTEXT.md via `domain-modeling`
- **Fuzzy term sharpened?** Update CONTEXT.md immediately
- **User rejects candidate with a load-bearing reason?** Offer an ADR: "Want me to record this so future reviews don't re-suggest it?"
- **Exploring alternative interfaces?** Use `two-axis-code-review` to evaluate options

## HTML Report Structure

The report should be visually rich and self-contained. Key sections:

1. **Header** — project name, scan date, scope
2. **Hot Spot Map** — which parts of the codebase were scanned and why
3. **Candidate Cards** — one per finding (usually 3-7 candidates)
4. **Top Recommendation** — which to tackle first
5. **Next Steps** — how to proceed with the chosen candidate

Tailwind classes for badges:
- `Strong` → `bg-green-100 text-green-800`
- `Worth exploring` → `bg-yellow-100 text-yellow-800`
- `Speculative` → `bg-gray-100 text-gray-600`

## Integration with Developer Profile

- Run this **every few days** during active development
- After `systematic-debugging` Phase 6 (post-mortem), feed architectural findings here
- Use `codebase-inspection` for quantitative metrics (LOC, file count) before the scan
- The grilling phase feeds into `writing-plans` for implementation

## Common Pitfalls

1. **Not scoping first.** Scanning the entire codebase when only 3 files changed is wasteful. Use git history.
2. **Proposing interfaces too early.** The HTML report should describe problems and solutions in plain English. Interface design happens in the grilling phase.
3. **Creating ADRs for everything.** Only when the decision is hard to reverse, surprising, and the result of a real trade-off.
4. **Skipping the grilling phase.** The HTML report is discovery. The grilling is where architecture actually improves.
5. **Using wrong vocabulary.** "Module", not "component". "Seam", not "boundary". Be precise.

## Verification Checklist

- [ ] Scope correctly targeted (hot spots or user-specified area)
- [ ] CONTEXT.md and ADRs read before scan
- [ ] Exploration sub-agent completed with friction points noted
- [ ] HTML report written to temp directory and opened for user
- [ ] Candidates classified with recommendation strength badges
- [ ] Top recommendation clearly stated with reasoning
- [ ] User selected a candidate → grilling session started
- [ ] Domain model updates applied inline during grilling
- [ ] ADRs offered only when all three criteria met

---
name: to-spec
description: "Use when the user says 'write a spec', 'create a spec', 'задокументируй требования', or when a conversation has settled on a feature and needs a formal spec. Synthesizes the current conversation into a spec without additional interviewing."
version: 1.0.0
author: Hermes Agent (adapted from mattpocock/skills)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [spec, requirements, documentation, synthesis]
    related_skills: [grilling, brainstorming, writing-plans, domain-modeling]
---

# To Spec

## Overview

Take the current conversation context and codebase understanding and produce a **spec**. Do NOT interview the user beyond what's already been discussed — this skill synthesizes, not discovers.

The output is a structured markdown document that captures: problem statement, solution, exhaustive user stories, implementation decisions, testing strategy, and out-of-scope items.

## When to Use

- User says: "write a spec", "create a spec", "make this into a spec", "задокументируй"
- A grilling session just finished and decisions need formalizing
- A feature discussion has crystallized enough to write down

**Don't use for:**
- Vague ideas that haven't been discussed at all — use `grill-me` first
- Bug reports — use `systematic-debugging`
- Trivial changes that fit in a commit message

## Process

### 1. Gather Context

- Read the project's `CONTEXT.md` if it exists — use domain vocabulary throughout the spec
- Check ADRs in `docs/adr/` to avoid contradicting previous decisions
- Review the current conversation for all decisions, constraints, and requirements already discussed

### 2. Identify Test Seams

Sketch out the seams at which you're going to test the feature:
- Prefer existing seams (test files, API endpoints, CLI entry points)
- Use the highest-level seam possible — integration > unit
- If new seams are needed, propose them at the highest practical point
- Ideal: one seam for the whole feature

**Check with the user** that these seams match their expectations before writing the spec.

### 3. Write the Spec

Use the template below. Every section must be filled — no "TBD" or placeholders.

### 4. Save and Confirm

Save the spec to the project (suggest: `docs/specs/<feature-slug>.md` or wherever the project keeps specs). Tell the user the path.

## Spec Template

```markdown
# <Feature Name>

## Problem Statement

The problem the user is facing, from the user's perspective. No implementation details here — just the pain.

## Solution

The solution to the problem, from the user's perspective. What changes for them? Still no implementation details.

## User Stories

A LONG, numbered list of user stories. Each in the format:

1. As a <actor>, I want a <feature>, so that <benefit>

This list should be extremely extensive and cover all aspects of the feature. Every edge case, every role, every interaction. Aim for 10-30 stories depending on feature size.

## Implementation Decisions

A list of decisions made during discussion. Include:

- The modules that will be built or modified
- The interfaces of those modules
- Technical clarifications from the developer
- Architectural decisions
- Schema changes
- API contracts
- Specific interactions between components

Do NOT include specific file paths or code snippets — they become outdated quickly.

Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it within the relevant decision. Trim to the decision-rich parts only.

## Testing Decisions

- What makes a good test for this feature (test behavior, not implementation)
- Which modules will be tested and at what seam level
- Prior art — similar tests already in the codebase to use as patterns

## Out of Scope

Explicitly list what is NOT included. Prevents scope creep and clarifies boundaries.

## Further Notes

Any additional context, constraints, or observations.
```

## Integration with Developer Profile

- Before writing the spec, ensure the feature has been grilled (`grill-me`) if non-trivial
- Use `domain-modeling` vocabulary from CONTEXT.md throughout the spec
- After saving, the spec can feed into `writing-plans` for implementation planning

## Common Pitfalls

1. **Interviewing the user.** This skill synthesizes — don't ask new questions. If the conversation is too vague, say so and suggest `grill-me` first.
2. **Sparse user stories.** "As a user, I want the feature" is not enough. Think through every role, every edge case, every interaction.
3. **Skipping test seams.** The testing strategy is as important as the implementation. Don't leave it for later.
4. **Including file paths.** They rot. Talk about modules and interfaces, not specific files.

## Verification Checklist

- [ ] Problem and Solution stated from user's perspective (no implementation details)
- [ ] User stories are exhaustive (10+ for non-trivial features)
- [ ] Implementation decisions are clear and actionable
- [ ] Testing seams identified and user-confirmed
- [ ] Out of Scope explicitly stated
- [ ] Spec saved to project at an appropriate path
- [ ] Domain vocabulary from CONTEXT.md used consistently
- [ ] No new questions asked of the user (pure synthesis)

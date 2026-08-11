---
name: two-axis-code-review
description: "Use when the user says 'review this', 'code review', or when finishing implementation work. Two-axis review of the diff: Standards (coding standards + code smells) and Spec (faithfulness to originating issue/spec), run as parallel sub-agents."
version: 1.0.0
author: Hermes Agent (adapted from mattpocock/skills)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [code-review, quality, standards, spec-check]
    related_skills: [requesting-code-review, systematic-debugging, test-driven-development]
---

# Two-Axis Code Review

## Overview

Review the diff since a fixed point along two independent axes, run as **parallel sub-agents** so neither axis pollutes the other:

- **Standards axis:** Does the code follow the project's coding standards? Are there code smells (Fowler baseline)?
- **Spec axis:** Does the code faithfully implement the originating issue, spec, or ticket?

After both sub-agents report, merge their findings into a single review summary.

This complements `requesting-code-review` (which focuses on the PR workflow). Use `two-axis-code-review` for the actual code inspection discipline.

## When to Use

- Finishing a feature implementation — review before committing
- Before opening a PR — catch issues early
- User says: "review this", "code review", "проверь код", "посмотри дифф"
- As the final step in an `implement` cycle

**Don't use for:**
- PR workflow management (opening, merging, commenting) — use `requesting-code-review`
- Debugging — use `systematic-debugging`
- Architecture-level review — use `improve-codebase-architecture`

## Process

### 1. Determine the Diff Baseline

Identify the fixed point the diff should be measured against:
- If on a feature branch: `git diff main...HEAD`
- If uncommitted changes: `git diff`
- If the user specifies: use their reference (commit SHA, branch, tag)

### 2. Read Project Standards

Before reviewing, check for:
- `CONTEXT.md` — domain vocabulary to verify consistent naming
- `.editorconfig`, `eslint.config.*`, `pyproject.toml`, or similar — coding standards
- `CONTRIBUTING.md` or `docs/contributing.md` — project conventions
- ADRs in `docs/adr/` — don't flag decisions that were intentional

### 3. Spawn Parallel Sub-Agents

Using `delegate_task` with `tasks` array, run both axes simultaneously:

**Standards sub-agent:**
```
Goal: Review the diff for coding standards violations and code smells.
Context: <project standards from step 2>
Diff: <relevant diff or file list>
Check:
- Naming conventions (consistent with CONTEXT.md vocabulary)
- Code organization (file structure, module boundaries)
- Error handling patterns
- Testing patterns
- Fowler-level code smells (duplication, long methods, feature envy, etc.)
- Any linting or formatting issues
Report each finding with: file, line, severity (blocker/major/minor/nit), and suggested fix.
```

**Spec sub-agent:**
```
Goal: Verify the diff faithfully implements the originating spec/issue/ticket.
Context: <spec or issue content>
Diff: <relevant diff or file list>
Check:
- Every user story / acceptance criterion is addressed
- No out-of-scope work crept in
- Edge cases from the spec are handled
- Testing decisions from the spec are followed
- Implementation decisions match the spec
Report each gap with: requirement, whether it's addressed, and evidence from the diff.
```

### 4. Merge Findings

When both sub-agents report back, produce a single review summary:

```markdown
## Code Review Summary

### Standards Review
- **Blockers:** <count> — must fix before merge
- **Majors:** <count> — should fix
- **Minors:** <count> — nice to fix
- **Nits:** <count> — optional

### Spec Fidelity
- **Requirements covered:** X/Y
- **Gaps found:** <list each with severity>

### Verdict
- [ ] Ready to merge
- [ ] Ready after minor fixes (list)
- [ ] Needs significant rework (list)
```

### 5. Present and Act

Show the summary to the user. Don't automatically fix issues — let the user decide what to address and in what order.

## Integration with Developer Profile

- **Before committing:** Run this review as the final step after `test-driven-development`
- **Before PR:** Use this for code inspection, then use `requesting-code-review` for the PR workflow
- **Architecture concerns:** If the review uncovers design issues, suggest `improve-codebase-architecture`

## Common Pitfalls

1. **Single-axis review.** Doing both at once means the spec influences your standards judgment. Parallel sub-agents prevent this.
2. **Reviewing without reading project standards.** Every project has conventions. Find them before judging.
3. **Fixing issues automatically.** The review is for the user. Present findings, let them decide.
4. **Flagging intentional decisions.** Check ADRs before calling something a code smell.
5. **Nits as blockers.** Distinguish severity clearly. A formatting nit is not a blocker.

## Verification Checklist

- [ ] Diff baseline correctly identified
- [ ] Project standards (CONTEXT.md, configs, ADRs) checked before review
- [ ] Both Standards and Spec sub-agents completed
- [ ] Findings merged with severity classification
- [ ] Verdict given with actionable next steps
- [ ] No automatic fixes applied without user confirmation

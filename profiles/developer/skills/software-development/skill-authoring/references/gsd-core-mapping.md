# GSD Core → Hermes Skills Mapping

Reference for the 2026-08-11 adaptation of GSD Core concepts into Hermes skills.

Source: https://github.com/open-gsd/gsd-core (MIT, v1.7.0, 6.7k+ stars)

## Phase Loop Mapping

| GSD Core | Hermes Skill | Artifact |
|----------|-------------|----------|
| Discuss | `discuss` | `.planning/phases/<name>/CONTEXT.md` |
| Plan | `writing-plans` + `plan` | `.hermes/plans/` or `docs/superpowers/plans/` |
| Execute | `executing-plans` + `subagent-driven-development` | code + commits |
| Verify | `verification-before-completion` (with coverage) | coverage checklists |
| Ship | `finishing-a-development-branch` | PR, merged branch |
| State | `project-state` | `.planning/STATE.md` |

## Key GSD Core Concepts Adopted

1. **Fresh context per agent**: heavy work in `delegate_task` subagents with clean context
2. **File-based state**: `.planning/STATE.md` survives sessions, replaces memory tool for project state
3. **Discuss before Plan**: `CONTEXT.md` captures implementation decisions before planning
4. **Coverage verification**: requirement coverage + decision coverage + goal alignment (not just "tests pass")
5. **Acceptance criteria**: explicit AC1, AC2 in CONTEXT.md, verified at completion

## What We Did NOT Adopt

- GSD Core CLI tools (gsd-tools.cjs) — Hermes has its own tool layer
- Multi-runtime orchestration — Hermes IS the runtime
- npm package dependency — zero new dependencies

---
name: skill-authoring
description: Use when creating or patching skills. Avoid common pitfalls.
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [skills, authoring, meta, pitfalls]
    related_skills: [writing-skills, hermes-agent-skill-authoring]
---

# Skill Authoring — Pitfalls and Patterns

Lessons learned from creating and modifying Hermes skills.
Load this before any `skill_manage` operation.

## Pitfall 1: Description Length

`skill_manage(action='create')` rejects descriptions longer than 60 chars.

**Error:** "new skills must fit the 60-char system-prompt budget"

**Fix:** ≤60 chars, trigger-first, one sentence, period at end.

```yaml
# Good (50 chars):
description: Use before any workflow. Manages .planning/STATE.md.

# Bad (129 chars — rejected):
description: Use automatically at start/end of any workflow — maintains ...
```

## Pitfall 2: Patch Deletes Table Rows

When patching a section with a markdown table, both `old_string` and `new_string` need the COMPLETE table. Rows omitted from `new_string` are silently deleted.

**Fix:** copy the full table into `new_string`, add changes, verify row count.

## Pitfall 3: writing-plans vs plan Structure

`plan` (developer profile): numbered steps (Step 1, Step 2).
`writing-plans` (superpowers): named sections, no numbering (Scope Check, File Structure).

When modifying `writing-plans`, insert between sections, not at step numbers.

## Pitfall 4: User-Owned Skills

Skills created during a session are user-owned. Background curator cannot edit them.
Error: "the skill is not curator-managed (no usage record)."
To fix: `hermes curator adopt <name>`

## Importing Skills from External Repos

User's recurring request: "пройдись по репозиторию, посмотри что можно дополнить из скиллов" (audited mattpocock/skills and obra/superpowers so far). Full recipe in `references/external-skill-import.md`. Summary:

1. **Clone shallow** to /tmp, enumerate `skills/*/SKILL.md`.
2. **Compare against local**: `skills_list`; for already-adapted repos grep `author:.*adapted from`; `wc -c` sizes reveal stale bundles.
3. **Classify**: no local analog → candidate; already adapted → skip; harness-specific (Claude Code hooks, `/setup-*` commands) → skip.
4. **Adapt frontmatter to Hermes**: description ≤60 chars (Pitfall 1); strip Claude-only fields (`disable-model-invocation`, `argument-hint`); replace `/setup-<repo>` references with Hermes equivalents; add `author: Hermes Agent (adapted from <repo>)`, license, `metadata.hermes.tags`, `related_skills`.
5. **Copy support files** (template.sh, etc.) via `cp`, then `chmod +x` and validate (`bash -n`).
6. **For git-clone bundles** (superpowers lives at `~/.hermes/skills/superpowers/` as a git clone): check version vs upstream (`git log --oneline -1`), check `git status --short` for local adaptations, preserve them (backup patch) before any fetch/rebase.

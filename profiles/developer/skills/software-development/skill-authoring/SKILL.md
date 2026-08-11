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

# Provenance audit: "какие скиллы пришли из GitHub за всё время"

Use when the user asks for a list of all skills taken/partially taken from repos they
sent over time ("список всех скиллов из GitHub"), or you need to know what came from
where before adapting something new. Do a disk audit — frontmatter `author:` lines are
the source of truth, not memory.

## Commands

```bash
# 1. Every skill with an "adapted from" marker (provenance tags)
grep -rl "adapted from" --include="SKILL.md" ~/.hermes/profiles/developer/skills | sort
# 2. Group by origin repo (author: lines)
grep -rh "author:" --include="SKILL.md" ~/.hermes/profiles/developer/skills | sort -u
# 3. Bundles living OUTSIDE the profile dir are separate sources
ls ~/.hermes/skills/superpowers/skills/          # e.g. the 14-skill superpowers bundle
```

## Markers to grep for

Each repo has a distinctive author line — enumerate by marker, don't guess:

- `adapted from mattpocock/skills` — grilling, grill-me, to-spec, domain-modeling,
  two-axis-code-review, improve-codebase-architecture, resolving-merge-conflicts,
  wizard, handoff, to-questionnaire, to-tickets (11 skills)
- `adapted from obra/superpowers` — systematic-debugging, plan (writing-craft adapted);
  plus the 14-skill bundle at ~/.hermes/skills/superpowers/skills/ (v6.3.0)
- `adapted from gsd-build/get-shit-done` — sketch, spike
- `blader/humanizer` — creative/humanizer (ported)

## Ideas-only repos (produce NO skills)

List them separately ("оценены, идеи реализованы в obsidian-brain"), with concrete ideas:

- akitaonrails/ai-memory — 6 ideas; вариант А (auto-entities frontmatter, commit 873413f),
  вариант В (brain_context recent_activity handoff, commit 4730ba0)
- volcengine/OpenViking — L0/L1/L2 tiering, cursor-based session sync, observable retrieval

## Cross-check with history

`session_search` (query `mattpocock OR superpowers OR github.com`) catches repos the user
sent that left no adapted files — they still belong in the report.

## Living registry

Keep a registry in Obsidian so the next audit is a one-file read:
`Brain/notes/skills/YYYY-MM-DD-skill-sources-registry.md` (vault
`/Users/dmitrypotekhin/Odsidian/obsidians/Obsidian Vault`). Structure: adapted skills by
source repo with on-disk paths, ideas-without-skills, and a "дописывать при адаптации"
reminder. Update it after every adaptation of an external repo.

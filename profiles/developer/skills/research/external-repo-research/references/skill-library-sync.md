# Skill-library sync: importing and updating skills from external repos

Use when the user asks to review a *skills/agents* repository (e.g. mattpocock/skills,
obra/superpowers, akitaonrails/ai-memory) and wants to know what to take ("что можно
использовать", "обновляй"). This is the import/update branch of external-repo-research.

## Three possible outcomes

1. **Import new skills** — repo has standalone skills we lack (mattpocock case).
2. **Update an installed bundle** — repo is already installed locally as a git clone
   (superpowers case: ~/.hermes/skills/superpowers/). The job is fetch + rebase, not create.
3. **Harvest ideas only** — repo is a full application, not skills (ai-memory case: Rust
   memory server conceptually overlapping our obsidian-brain). Recommend NOT installing a
   second tool; propose specific feature ideas for our own stack instead.

Always classify first and tell the user which case it is before proposing work.

## Workflow

1. Clone: `cd /tmp && git clone --depth 1 <url> <name>`
2. Inventory: list `skills/` subdirs; read README.md; read each candidate SKILL.md
   (head -c 1200 is enough to judge).
3. Compare with local set: `skills_list` + `grep -rl "<owner>" ~/.hermes/profiles/developer/skills`
   to find already-adapted skills and near-duplicates (map local analogues explicitly,
   e.g. tdd ≈ test-driven-development, diagnosing-bugs ≈ systematic-debugging).
4. Present candidates with practical value per skill ("что мне дает, как использую").
   Import only after user picks (they chose "топ-5" for mattpocock).
5. Import via skill_manage action=create; copy support files with cp.

## Adaptation checklist (external skill → Hermes)

- **description ≤60 chars** — Hermes index truncates at ~57. Trim long upstream
  descriptions; put the trigger first, end with a period.
- Frontmatter: `name`, `description`, `version: 1.0.0`,
  `author: Hermes Agent (adapted from <owner>/<repo>)`, `license: MIT`,
  `platforms: [...]`, `metadata.hermes.tags`, `related_skills`.
- Strip Claude-specific fields: `disable-model-invocation`, `argument-hint`,
  Claude-Code-only references.
- Replace course/bootcamp-specific links (e.g. mattpocock `/setup-matt-pocock-skills`)
  with our local conventions (`.scratch/`, `docs/specs/`).
- Category assignment: software-development / skills / productivity — match
  existing structure, don't create new categories for one skill.
- Support files: copy them (e.g. `cp .../wizard/template.sh <skill-dir>/template.sh`
  + `chmod +x`), validate with `bash -n` for shell scripts.
- After creation, verify: skill_manage returns success, files exist on disk,
  description parses (frontmatter intact).

## Updating the superpowers bundle (git clone at ~/.hermes/skills/superpowers/)

The bundle is a real git repo with LOCAL adaptation commits on top of upstream releases.
Local commits carry our GSD adaptations (docs/specs/ paths, CONTEXT.md coverage checks in
requesting-code-review / writing-plans / verification-before-completion, phase-context
block in writing-plans). Never reset --hard or re-clone over them.

Update procedure:

```bash
cd ~/.hermes/skills/superpowers
git diff > /tmp/superpowers-gsd-patch-$(date +%Y%m%d-%H%M).patch   # backup local edits
git add -A && git commit -m "GSD adaptations: ..."                 # commit local work first
git fetch origin
git log --oneline HEAD..origin/main | head                         # see what's new
git rebase origin/main                                             # rebase, not merge
```

Then verify:
- `git status --short` clean; `grep -rn "^<<<<<<<\|^=======\|^>>>>>>>" skills/` empty.
- GSD markers still present: `grep -rn "docs/specs/" skills/brainstorming/SKILL.md`;
  `grep -c "CONTEXT.md" skills/requesting-code-review/SKILL.md` etc.
- Frontmatter of every skill parses: loop `sed -n '2p;3p' skills/*/SKILL.md`.
- New upstream references landed (e.g. `test-driven-development/writing-good-tests.md`
  replaced `testing-anti-patterns.md` in v6.3.0).

Result should be HEAD = local adaptation commit directly on top of upstream release tag
(e.g. `0e49fe3 GSD adaptations` above `b36e082 Release v6.3.0`).

Check release notes: `head -100 RELEASE-NOTES.md` to summarize what the user gains
(brainstorming Three Paths, SDD plan-scoped workspace, TDD writing-good-tests, Hermes
support — all landed in v6.x).

## Presenting value to the user

For each upstream change, say what it does in user terms, not release-note prose:
- brainstorming "Three Paths" = ceremony scales to task size (Spike/Bounded/Architectural)
- SDD fixes = plan-scoped workspace, circuit-breaker, resume implementer, batch small tasks
- TDD = positive writing-good-tests catalog + falsifiability discipline
- finishing-a-development-branch = no untracked-file destruction, discard only on request

## Pitfalls

- Local bundle can lag 3+ releases behind (v6.0.3 vs v6.3.0 was ~4 months). Always
  compare versions before concluding "nothing new".
- Do NOT store the current bundle version in memory — it goes stale. The procedure above
  is the durable part.
- Don't install a full external memory/agent server when our stack already has a
  near-equivalent (obsidian-brain vs ai-memory) — propose feature ideas instead
  (entities frontmatter, authority-aware recall, lifecycle auto-capture, handoff injection).

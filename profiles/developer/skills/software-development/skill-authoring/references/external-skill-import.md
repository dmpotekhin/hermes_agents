# External Skill Import — Session Recipes

## mattpocock/skills (2026-08-20)

Repo layout: `skills/{engineering,productivity,misc,in-progress}/<name>/SKILL.md` (+ optional `agents/openai.yaml`, `template.sh`).

Already adapted before this session (grep `author:.*adapted from` in profile skills): grill-me, grilling, domain-modeling, improve-codebase-architecture, to-spec, two-axis-code-review.

Imported 5 new (all `skill_manage create`):
- software-development/wizard — + `template.sh` copied via `cp` from repo, `chmod +x`, `bash -n` OK (204 lines)
- software-development/resolving-merge-conflicts
- skills/handoff
- software-development/to-tickets
- productivity/to-questionnaire

Adaptations applied: descriptions squeezed to ≤60 chars (all 5 first attempts rejected — Pitfall 1); removed `disable-model-invocation`/`argument-hint`; replaced `/setup-matt-pocock-skills` reference in to-tickets with local `.scratch/<feature-slug>/issues/` default; added author/license/tags/related_skills.

Skipped as not portable: setup-matt-pocock-skills, migrate-to-shoehorn, scaffold-exercises (course-specific), git-guardrails-claude-code, claude-handoff (Claude Code-specific). Deferred candidates: teach, triage, wayfinder, writing-beats.

## obra/superpowers (2026-08-20)

Bundle is a git clone at `~/.hermes/skills/superpowers/` (branch main), all 14 skills registered with Hermes' native loader.

Found stale: installed at v6.0.3 (commit 896224c), upstream at v6.3.0 (2026-08-12). Three releases behind.

Notable upstream changes worth having: brainstorming "Three Paths" (spike/bounded/architectural — ceremony scales to task, approval gate never scales down); subagent-driven-development (plan-scoped workspace, 5-round circuit breaker, batch small tasks, Spec: pointer); TDD writing-good-tests.md replaces testing-anti-patterns.md (positive catalog + falsifiability discipline); finishing-a-development-branch (no discard offer, no untracked destruction); using-superpowers slimmed for token cost; official Hermes Agent support.

**CRITICAL — 5 local GSD adaptations exist in the bundle** (`git status --short`): skills/brainstorming/SKILL.md + spec-document-reviewer-prompt.md (docs/superpowers/specs/ → docs/specs/), requesting-code-review/SKILL.md (+CONTEXT.md decision-coverage block), verification-before-completion/SKILL.md (+Coverage Verification C1-C4), writing-plans/SKILL.md (+Phase Context GSD Discuss). Must be preserved (backup patch via `git diff > /tmp/superpowers-local.patch`) before any fetch/rebase; re-apply manually after update.

Update was proposed to user (save patch → fetch+rebase → resolve conflicts → verify with skills_list); not yet executed as of session end.

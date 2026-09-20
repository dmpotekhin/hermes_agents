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

## Pitfall 5: Патч без изменений

`patch(old_string=X, new_string=X)` (или строки, отличающиеся только форматированием) проходит с «success» и ничего не меняет. Дальше код падает на «переменная не определена», хотя «патч применился».

**Fix:** `new_string` обязан реально отличаться; после каждого патча смотри diff/линтер в ответе, а не факт success. Если патч по замыслу должен был что-то добавить, а diff пуст — правка не сделана, повтори с другим `new_string`.

## Importing Skills from External Repos

User's recurring request: "пройдись по репозиторию, посмотри что можно дополнить из скиллов" (audited mattpocock/skills and obra/superpowers so far). Full recipe in `references/external-skill-import.md`. Summary:

1. **Clone shallow** to /tmp, enumerate `skills/*/SKILL.md`.
2. **Compare against local**: `skills_list`; for already-adapted repos grep `author:.*adapted from`; `wc -c` sizes reveal stale bundles.
3. **Classify**: no local analog → candidate; already adapted → skip; harness-specific (Claude Code hooks, `/setup-*` commands) → skip.
4. **Adapt frontmatter to Hermes**: description ≤60 chars (Pitfall 1); strip Claude-only fields (`disable-model-invocation`, `argument-hint`); replace `/setup-<repo>` references with Hermes equivalents; add `author: Hermes Agent (adapted from <repo>)`, license, `metadata.hermes.tags`, `related_skills`.
5. **Copy support files** (template.sh, etc.) via `cp`, then `chmod +x` and validate (`bash -n`).
## Hub-путь: `hermes skills install` (предпочтителен для готовых наборов)

Когда нужен внешний набор скиллов (десятки штук в одном репозитории) — не клонируй: ставь через хаб по идентификатору `skills-sh/<owner>/<repo>/<skill>`.

```
hermes skills search <query>                                   # найти идентификатор скилла
hermes skills install skills-sh/<owner>/<repo>/<skill> --yes  # --yes обязателен в неинтерактивном запуске
hermes skills tap list                                         # подключённые репозитории-источники
```

- Ставь только те 3-6 скиллов, которые реально нужны под задачу: весь набор раздувает выбор скиллов и контекст.
- Профиль назначения задаётся `HERMES_HOME` — сверь `env | grep HERMES_HOME`, прежде чем ставить, чтобы попасть в нужный профиль.
- Хаб прогоняет сканер и печатает вердикт: `SAFE` — ставит; `BLOCKED` (+ N findings) — отказывает. Вердикт BLOCKED не обходи молча; `--force` — только по явному решению пользователя, с показом находок.
- `--force` снимает ТОЛЬКО вердикт сканера. Ошибку скачивания («Could not fetch ... from any source») он не лечит — это лимит/сеть, а не находки; не обещай пользователю, что флаг решит проблему загрузки.
- Прежде чем ставить чужой скилл, прочитай его SKILL.md, а не только вердикт сканера: страница `https://www.skills.sh/<owner>/<repo>/<skill>` отдаёт полный текст — открой её браузером, раскрой контрол «Show more» и читай `document.body.innerText` от маркера `SKILL.md`. Цитировать чеклист скилла в разборе можно и нужно: вердикт сканера говорит про безопасность, а не про пользу.
- Не угадывать путь `raw.githubusercontent.com/<owner>/<repo>/main/<skill>/SKILL.md`: раскладка файлов в репозитории не совпадает с идентификатором скилла в хабе (обычно 404) — путь брать из страницы скилла или из дерева репозитория.
- После установки проверять факт установки файлом: `~/.hermes/profiles/<профиль>/skills/<skill>/SKILL.md`. Хаб кладёт скиллы в корень каталога скиллов, а не в подкаталог категории, поэтому поиск по категориям их не находит.
- Скачивание идёт через GitHub API анонимно (60 запросов/час); при исчерпании установка падает с «Could not fetch ... from any» — это лимит, а не поломка хаба: помогает `GITHUB_TOKEN` в окружении/`.env` либо повтор после сброса лимита.
- Установленные через хаб скиллы — protected: куратор их не патчит (правки только при `hermes curator adopt`).

6. **For git-clone bundles** (superpowers lives at `~/.hermes/skills/superpowers/` as a git clone): check version vs upstream (`git log --oneline -1`), check `git status --short` for local adaptations, preserve them (backup patch) before any fetch/rebase.

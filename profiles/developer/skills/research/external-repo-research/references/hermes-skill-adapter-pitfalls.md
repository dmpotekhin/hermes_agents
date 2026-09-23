# Hermes skill-adapter pitfalls (hit live importing guard-skills / ui-skills)

Hard-won gotchas from adapting third-party skill catalogs (`amElnagdy/guard-skills`,
`ibelick/ui-skills`) into a Hermes profile. Complements the happy-path recipe in
`skill-library-sync.md`; these are the failure modes that actually bite.

## 1. Description hard cap is 60 chars (enforced, not advisory)

- `skill_manage(action='create')` REJECTS any description over 60 chars
  ("new skills must fit the 60-char system-prompt budget"). I got a `212 chars` rejection.
- The skill index truncates at ~57 chars + `...`, so the trigger must be self-contained
  within the first ~57 chars. Keep the capability statement short and front-loaded.
- Trim the long upstream description down to a one-line trigger; move detail into the body.

## 2. A `:` in the description breaks YAML — quote it

- `description: Deslop UI quickly: fix spacing, ...` parses the `: fix spacing` as a
  nested YAML mapping → `ScannerError: mapping values are not allowed here`.
- Fix: wrap the whole value in double quotes:
  `description: "Deslop UI quickly: fix spacing, hierarchy, typography."`
- Quotes do NOT count toward the 60-char limit.

## 3. Token-efficient import: copy the file, patch the frontmatter — don't re-emit the body

For large external SKILL.md bodies, do NOT re-transcribe the whole file through the LLM.
Copy it and edit only the frontmatter:

```bash
BASE="$HOME/.hermes/profiles/<profile>/skills/<category>"
mkdir -p "$BASE/$name"
cp -r /tmp/<repo>/skills/$name/. "$BASE/$name/"
# then skill_manage(action='patch') the frontmatter block only
```
- Check for a `references/` dir before copying — `cp -r <skill>/. dest/` covers it, but
  some skills have references and some don't. Always `ls -1` the skill dir first.
- `improve-ui` had a `references/` dir; `baseline-ui`, `fixing-accessibility`,
  `fixing-motion-performance` had only `SKILL.md`.

## 4. Frontmatter to add when adapting (Hermes shape)

Every adapted skill needs: `name`, `description` (≤60), `version`,
`author` (human/upstream first, then ", Hermes Agent"), `license`, `platforms`,
`metadata.hermes.tags`, `metadata.hermes.related_skills`.

## 5. Strip non-Hermes frontmatter/body conventions

- `triggers:` and `tools:` are NOT Hermes fields (they're opencode/Claude/Cursor
  conventions). Hermes routes on the `description` + catalog category instead.
- `/slash-command` invocation lines (`/improve-ui`, `/baseline-ui`) in the body do not
  work in Hermes — rephrase as prose or leave as descriptive hints only.

## 6. `related_skills` must resolve to REAL existing skills

Cross-link imported skills to actual in-library peers so they load together:
`ui-foundations` ↔ `ui-components` ↔ `ui-animations` ↔ `ui-checklist`, and the imported
`improve-ui`/`baseline-ui`/`fixing-accessibility`/`fixing-motion-performance` wired back
to those. A dangling name does nothing.

## 7. Validate frontmatter programmatically before trusting `skills_list`

`skills_list` shows a skill even when its frontmatter is subtly broken, so validate the
on-disk SKILL.md yourself with a tiny script: check it starts with `---`, closes the
frontmatter, `yaml.safe_load` succeeds, `description` ≤60 and ends with `.`, and the
required fields exist. Wrap each file in try/except — a single malformed pre-existing
skill (e.g. `baoyu-infographic`) crashed a naive whole-directory scan.

## 8. Category choice

Match existing structure (`creative/` for design, `software-development/` for code guards).
Don't invent a top-level category per catalog; fit the skill into the closest existing one.

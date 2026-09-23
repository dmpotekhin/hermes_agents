# GitHub Action auto-refresh of static-site data

Goal: user edits a SOURCE data file (e.g. `города.xlsx`), pushes it, and a GitHub Action
runs a generator script that rebuilds generated `js/*.js` / `data/*.json`, auto-commits the
generated files, and lets GitHub Pages redeploy. The user never touches the generated files.

Live example: `.github/workflows/update-travel-data.yml` in `dmpotekhin.github.io` triggering
`scripts/update_travel_data.py` (regenerates `js/travel-data.js` + `data/visited_countries.geojson`).

## Known-good reference YAML

```yaml
name: Update site data
on:
  push:
    branches: [master]
    paths:
      - 'городa.xlsx'          # <-- SOURCE file only
permissions:
  contents: write
jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install deps
        run: pip install -r scripts/requirements.txt
      - name: Run update pipeline
        run: python3 scripts/update_travel_data.py
      - name: Commit generated data
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add js/travel-data.js data/visited_countries.geojson
          if git diff --cached --quiet; then
            echo "No data changes."
            exit 0
          fi
          git commit -m "Update site data from source file"
          git push
```

## Pitfalls (the real learning — these are easy to get wrong)

1. **The path filter IS the loop guard.** The auto-commit touches ONLY the generated files,
   never the source xlsx. Because the trigger is `paths: [<source>]`, the auto-commit push does
   NOT match the filter, so the workflow does NOT re-trigger itself. Drop the path filter
   (or broaden to `push: [master]`) and the auto-commit push re-triggers the workflow forever ->
   infinite runs/cost. Keep the filter tight on the source file.

2. **Do NOT add `[skip ci]` to the auto-commit message.** `[skip ci]` suppresses ALL CI for
   that push — INCLUDING the GitHub Pages redeploy. Since we rely on the auto-commit push to
   rebuild Pages, `[skip ci]` silently breaks the deploy. The path filter is already the loop
   guard, so `[skip ci]` is both unnecessary and harmful. Leave it out.

3. **The source file MUST be in git.** A workflow runs in a clean container via
   `actions/checkout@v4`; it only sees files tracked in the repo. If the source xlsx is
   `untracked` locally, the workflow never sees it. Commit the source file as part of the
   feature. (Contrast: the common "don't commit the xlsx" habit assumes the generator runs only
   locally. With a refresh Action, the source MUST live in the repo.)

4. **A newly-added workflow file does NOT run on the commit that introduces it.** GitHub
   resolves the workflow definition from the ref AFTER the push, so the commit that first adds
   the `.yml` (even if it also touches the trigger path) does NOT fire the workflow. This is
   EXPECTED, not a bug — it fires on the NEXT push that changes the trigger path. Don't panic
   when the first run doesn't appear in the Actions log.

5. **GITHUB_TOKEN push does not trigger OTHER workflows.** A push made from inside a workflow
   using the default `GITHUB_TOKEN` does not create new workflow runs (GitHub cycle-prevention).
   So the auto-commit push will NOT re-trigger a sibling workflow.
   - If Pages is deployed via a separate `pages.yml` workflow, the auto-commit push will NOT
     redeploy it -> data updates but the site goes stale. Fix: use a PAT (contents: write) as
     the checkout/push credential so the push carries real user authority and DOES trigger
     sibling workflows.
   - If Pages is classic "Deploy from a branch" mode (no `pages.yml`; the only workflow is
     GitHub's builtin `pages-build-deployment`), then ANY push to master — including a
     GITHUB_TOKEN push — triggers a rebuild. This was the case here; no PAT needed.
   Determine which mode: `git ls-files .github/workflows/` — if the only entries are yours plus
   a builtin `pages-build-deployment`, you're in classic mode.

## Verify the workflow is registered (no gh CLI)

`gh` may not be installed. Use the public REST API (public repo; reads need no token):

```bash
# Is the workflow registered & active?
curl -s "https://api.github.com/repos/<owner>/<repo>/actions/workflows" \
  -H "Accept: application/vnd.github+json" | grep -E '"name"|"path"|"state"|"total_count"'

# Did the change actually fire? (check-runs for a commit)
curl -s "https://api.github.com/repos/<owner>/<repo>/commits/<sha>/check-runs" \
  -H "Accept: application/vnd.github+json" | grep -E '"name"|"status"|"conclusion"'

# Is the source / workflow file actually in master?
curl -s -o /dev/null -w "%{http_code}\n" \
  "https://raw.githubusercontent.com/<owner>/<repo>/master/<path>"
```

Confirm the workflow `state` is `active` (not `disabled_manually`). If `total_count` is 0 the
file never reached the repo — the push didn't happen or the path is wrong.

## Generator idempotency contract (so the Action is safe on every push)

- Reuse already-verified data (existing `travel-data.js` values) — geocode only the delta.
- Read the source, diff against current data, compute the delta; zero-new means NO change, and
  the auto-commit `if git diff --cached --quiet; then exit 0` short-circuits.
- Keep any geocoder disk cache in `.gitignore` (never commit it; regenerated each run).
- Be polite to the geocoder: `time.sleep(1.0)` between requests (Usage Policy ~1 req/sec).
- Put Python deps in `scripts/requirements.txt` (openpyxl + requests) so the Action can
  `pip install -r`.

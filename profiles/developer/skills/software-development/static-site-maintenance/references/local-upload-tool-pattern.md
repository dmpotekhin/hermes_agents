# Local Upload Tool for a Static GitHub Pages Site (working example)

Schema built and verified for adding photos to a public static site
(dmpotekhin.github.io travel map) WITHOUT leaking a write path. The same
pattern applies to any static site needing authenticated content edits.

## The core violation to avoid

A static GitHub Pages repo is **public**. Any write UI ("admin page", an upload
form, a JS function that POSTs data, a serverless fn) that lives ON the site
becomes a public write surface — anyone can hit it. The user's reason for the
redirect: "githubpages public может быть утечка". Never put a write endpoint on
a public static site.

## Verified pattern

- **Separate project** outside the public repo, own venv + deps
  (e.g. `~/projects/travel-media-admin` with `flask`, `pillow`).
- **Local Flask app bound to loopback only**: `host=127.0.0.1` (NOT `0.0.0.0`).
  Nobody outside the machine can reach it.
- **Write via git CLI** into a local clone of the site:
  `git pull --rebase` → edit content files → `git commit` → `git push`.
  GitHub Pages redeploys (~30–60s); tell the user to hard-refresh.
- **No PAT / token**: auth is the already-configured SSH key (`git@github.com`).
  The credential never leaves the machine; nothing secret is committed.
  Still run credential-scan on `--staged` before commit.
- **Reuse the site's existing pipeline logic** (translit/slug, image resize,
  merge into the generated JS data file) by importing from the pipeline script
  (`from scripts.process_travel_media import slug, process_photo`) instead of
  duplicating it — one source of truth.

## Project layout (travel-media-admin)

```
app.py            Flask app: routes /api/cities, /upload
uploader.py       core: pull -> resize -> merge travel-media.js + csv -> commit -> push
config.json       {"repo_path": "...", "branch": "master", "host": "127.0.0.1", "port": 8081, "debug": false}
templates/index.html
static/admin.js   fetch('/api/cities') -> dropdown; drop zone -> POST /upload
static/admin.css
requirements.txt
README.md
.gitignore        (.venv/, __pycache__/, *.pyc, .DS_Store)
```

## uploader.py skeleton (the reusable shape)

```python
import json, subprocess, sys
sys.path.insert(0, os.path.join(repo_path, "scripts"))
from process_travel_media import slug, process_photo   # reuse, don't duplicate

def git(*args):            # subprocess ARG LIST, never shell=True
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True)

def upload_photo(city, photo, dry_run=False):
    if dry_run:                       # VALIDATE + PREVIEW ONLY — no writes, no git
        rel, log = process_photo(photo, city, dry_run=True)
        return {"ok": True, "dry_run": True, "city": city, "photo": rel}
    git("-C", repo, "pull", "--rebase")
    rel, log = process_photo(photo, city)            # resize + write photos/<slug>.jpg
    merge_into_js(city, rel)                         # add to js/travel-media.js (keep header)
    append_csv(city, rel)                            # sync media_list.csv
    git("-C", repo, "add", "-A")
    git("-C", repo, "commit", "-m", f"Add travel photo: {city}")   # msg = single argv
    git("-C", repo, "push")
    return {"ok": True, "city": city, "photo": rel}
```

## Hard-won pitfall: dry-run MUST be non-destructive

First version of dry-run wrote the resized photo into the working clone, leaving a
**dirty git tree**. The next REAL upload then failed on `git pull --rebase`
("cannot pull with rebase: unstaged changes"). Fix: dry-run only validates and
previews `process_photo(..., dry_run=True)` — no file writes, no git at all.
Test against a throwaway clone (`/tmp/tma_test_N`) or a pure in-memory preview,
never against the working clone.

## Flask bind + routes

```python
app.run(host=cfg["host"], port=cfg["port"], debug=cfg.get("debug", False))
# host is "127.0.0.1" from config — loopback only. Never pass "0.0.0.0".
```

- `GET /api/cities` → returns the city list parsed from `js/travel-data.js`
  (source of the UI dropdown) + repo sanity.
- `POST /upload` (multipart: file + city) → returns `{ok, dry_run, city, photo}`;
  missing city → 400; unknown handling → 4xx with message.

## Preconditions for first real run

The local clone must be **clean** (`git status --short` empty) so `pull --rebase`
succeeds. Verify with `git -C <repo> status --short` before handing to the user.

## Security self-review already validated

- `grep -rnE "shell=True|os\.system|eval\(|exec\(" app.py uploader.py` → no hits.
- git calls use argument lists, commit message is a single argv element.
- credential-scan on `--staged` → exit 0 (no leaked secrets).
- The only "token-looking" grep hit lived inside `./.venv` (Pillow dependency),
  which is gitignored — not part of the repo.

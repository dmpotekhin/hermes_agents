---
name: travel-media-admin
description: Use when adding travel photos to the dmpotekhin travel map.
version: 1.0.0
author: dmitrypotekhin
license: MIT
metadata:
  tags: [travel, media, github-pages, flask, photo-upload]
  related_skills: [travel-map-verification, github-pages-booknotes]
---

# travel-media-admin

## Overview
A local, loopback-only Flask UI for adding city photos to the GitHub Pages
travel map (dmpotekhin.github.io/travel.html). It writes through the user's
existing SSH key to the site repo (git push) — no PAT/token, no server-side
secret. Public site stays pure static with zero write endpoints.

## When to Use
- Add / replace a photo for a visited city on the travel map.
- Run or debug travel-media-admin itself.
- Reason about why travel photos must NOT be added via a public admin page.

## Quick Reference
```bash
cd ~/projects/travel-media-admin
.venv/bin/python app.py          # serves http://127.0.0.1:8081
open http://127.0.0.1:8081
```
Config: `config.json` → repo_path (local clone of the site), branch, host
(must stay 127.0.0.1), port 8081.

## How It Works
1. UI lists cities from the clone's `js/travel-data.js` (window.TRAVEL_CITIES).
2. Pick city + photo → GET/POST.
3. Server: `git pull --rebase` → resize via Pillow into `photos/<slug>.jpg`
   (+ `photos/<slug>_thumb.jpg`, 160px q70) → add
   `{city:{photo, thumb}}` to `js/travel-media.js` (preserves header) →
   sync `media_list.csv` → `git commit` → `git push`.

## Media format (js/travel-media.js)

`window.TRAVEL_MEDIA = { "<city>": { "photo": "photos/<slug>.jpg", "thumb":
"photos/<slug>_thumb.jpg" } }`. **thumb** is the small sidebar-list image
(160px, q70, ~9KB); **photo** is the full-size (1000px, q80) popup image.
The map sidebar list uses `thumb || photo || poster` with `loading="lazy"`;
the popup keeps the full `photo` (eager). Generate `thumb` via `process_photo_thumb()`
in `scripts/process_travel_media.py` (single source of truth, imported by
`uploader.py`). Cities with only `video`/`poster` still get a `thumb`.
Popups MUST NOT use `loading="lazy"` (MapLibre popup images fail to appear).
4. GitHub Pages redeploys ~30-60s.

## Key Files
These are project files in `~/projects/travel-media-admin/` (NOT files in this
skill directory) — see that project's README for the full doc:

- `app.py` — Flask routes: GET /, GET /api/cities, POST /upload.
- `uploader.py` — core logic (imports `slug`/`process_photo` from the site's
  `scripts/process_travel_media.py` — single source of truth).
- `templates/index.html` + `static/admin.js` + `static/admin.css` — UI.
- `README.md` — full doc.

## Common Mistakes / Pitfalls
- **Never bind 0.0.0.0** (host stays 127.0.0.1). Outer world must not reach it.
- **Dry-run is non-destructive** (writes nothing) so a later real upload's
  `git pull --rebase` sees a clean tree.
- **Real upload needs a clean tree**: `git pull --rebase` fails if the target
  clone has uncommitted changes.
- **Slug is Cyrillic translit** via `process_travel_media.slug()`: "Барселона"
  → `barselona.jpg` (NOT "barcelona"). Filename ≠ English spelling; travel.js
  keys by city name, so it's fine.
- **Do NOT build a public admin.html on Pages** — that is a write-path leak
  surface. This local tool is the private alternative.
- Adding media by hand vs script: if `process_travel_media.py --write` is later
  run, it regenerates `travel-media.js` from imports — keep `media_list.csv` in
  sync so the batch pipeline doesn't wipe admin-added entries.
- **Popup photos must load eagerly**: `loading="lazy"` on an image inserted
  into a MapLibre popup (or a dynamically rebuilt list) can fail to load, so the
  photo appears missing even though the file is deployed. Keep popup-photo and
  list-thumb eager (no `loading="lazy"`).
- **Heart-click popups lose the photo**: MapLibre's `queryRenderedFeatures`
  hands a nested object property (like `media`) back as a JSON STRING, so
  `media.photo` is `undefined` and no `<img>` is rendered — even though the
  sidebar-list path works (there `c.media` is a real object). Fix: normalize in
  `resolveMedia()` — if `media` is a string, `JSON.parse` it; also fall back to
  `MEDIA[props.name]`. Never trust nested object props straight from MapLibre.
- **Stale assets after deploy**: GitHub Pages serves JS with `cache-control:
  max-age=600` (10 min). After pushing, a normal refresh can still show old
  files. Add cache-busting (`?v=<date>`) to the travel script tags in
  `travel.html` on each update, and tell the user to hard-refresh
  (Cmd/Ctrl+Shift+R) — `travel.html` itself is cached too.

## Verification
- After a change, `cd ~/projects/travel-media-admin && .venv/bin/python app.py`
  then curl `/` (200) and `/api/cities` (ok, 255 cities).
- On a real upload, confirm the commit landed (`git -C <repo> log --oneline -1`)
  and the photo file exists at `photos/<slug>.jpg`.

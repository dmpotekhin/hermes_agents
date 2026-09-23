---
name: travel-map-verification
description: Use when verifying the travel-map page and data are correct.
version: 1
author: dmitrypotekhin
license: MIT
---

# Travel Map Verification

Non-destructive check that the travel map on GitHub Pages is wired up correctly:
visited cities (hearts) + visited-country highlight, MapLibre GL + CARTO.
Expected city/country counts are read from the auto-generated header of
js/travel-data.js (currently 255 cities / 50 countries) — not hardcoded — so the
script stays correct after any data refresh.

Run this after building/updating the map, or any time you need to confirm
"всё сделано правильно" before calling it done.

## When to use
- The travel map page (dmpotekhin.github.io/travel.html) is built, updated, or refactored.
- You want to confirm the data, page integration, and deployment are all correct.
- Before committing changes that touch js/travel-data.js, data/visited_countries.geojson,
  js/travel.js, js/travel.css, travel.html, index.html, or books.html.

## Steps

### 1. Data + integration checks (script)
The bundled script checks:
- travel-data.js parses; city count matches the auto-generated header (currently 255);
  all lon/lat numeric & in range; all cc 2-letter; all have name+country.
- Two user-confirmed CHECK cities keep their mapping: Кордоба -> AR, Картахена -> CO.
- visited_countries.geojson is a FeatureCollection; country count matches the header
  (currently 50); all iso_a2 2-letter; all fillColor valid hex.
- Consistency: distinct city cc set == geojson iso_a2 set (1:1).
- travel.html references js/main.js, js/travel-data.js, js/travel.js, css/travel.css.
- index.html and books.html link to travel.html.

Run it:
```
python3 ~/.hermes/profiles/developer/skills/software-development/travel-map-verification/scripts/travel_map_verify.py [repo_dir]
```
(Optional repo_dir defaults to /Users/dmitrypotekhin/Downloads/dmpotekhin.github.io)

Every check prints PASS/FAIL; the script exits non-zero if any check fails.

### 0. Refresh the data (when города.xlsx changed)
To bump the map data after editing `города.xlsx`, run the reusable pipeline —
it diffs against the current `travel-data.js` (verified cache) and only geocodes
the delta, so existing coordinates never change:
```
python3 /Users/dmitrypotekhin/Downloads/dmpotekhin.github.io/scripts/update_travel_data.py
```
It reads the xlsx, geocodes new cities via Nominatim (disk cache to
scripts/nominatim_cache.json), skips known typos (e.g. Хэдань -> Хандань), and adds
missing country polygons from Natural Earth 50m. Idempotent: re-running with no
new cities changes nothing. After it writes, run the verification (step 1), then the
browser check (step 2), then commit the two generated data files (never the source
xlsx or unrelated modified files).

### 2. Browser render check
Open the page in a real browser (Playwright) and confirm it renders:
- Basemap tiles load (CARTO Voyager), land + labels visible.
- Visited countries tinted pink.
- Red cluster circles with counts on the world view; red hearts when zoomed in.
- Clicking a heart opens a popup ("Город / Страна").
- Sidebar: "255 городов · 50 стран" (auto-derived from data), search, country-grouped list, legend.
- No console errors except the benign favicon.ico 404.

Navigation: start `python3 -m http.server 8765` from the repo dir, open
http://localhost:8765/travel.html. Screenshot and inspect with vision.

### 3. Deployment check
After `git push`, wait for GitHub Pages (~30-60s) and confirm 200:
```
curl -s -o /dev/null -w "%{http_code}\n" https://dmpotekhin.github.io/travel.html
curl -s https://dmpotekhin.github.io/ | grep 'href="travel.html"'
```

## Pitfalls
- MapLibre does NOT re-fire `style.load` after `map.setStyle()` — do NOT try to swap the
  basemap on theme toggle (layers get removed and never re-added). Keep the map on CARTO
  Voyager and let the site theme toggle only affect chrome. Add custom layers via `map.on('load', addLayers)`.
- `map.once('idle', ...)` is unreliable for triggering popups after flyTo — open the popup
  immediately (it is anchored to a geographic point and follows the map during flyTo).
- openfreemap's asset endpoint can be flaky/slow (tiles/sprites/fonts time out; a two-font
  text stack requests "A,B" as one font id -> 404). Use CARTO (basemaps.cartocdn.com) and a
  single text-font (e.g. 'Open Sans Regular').
- города.xlsx IS committed to the site repo (it is the CI input: push edits to it and the
  GitHub Action regenerates the data). Do NOT commit an unrelated modified file (e.g. Книги.xlsx).
- Refresh data ONLY via scripts/update_travel_data.py (idempotent, delta-only geocoder with a
  Nominatim disk cache) — or let .github/workflows/update-travel-data.yml do it automatically
  on any push touching города.xlsx. Never hand-edit js/travel-data.js or the geojson.
- GitHub Actions pitfall: a workflow file ADDED by the same commit as its triggering path (e.g.
  adding update-travel-data.yml and города.xlsx together) does NOT fire on that introducing
  commit — GitHub evaluates the workflow from the post-push ref. It fires on the NEXT push that
  changes города.xlsx. Verify with the workflows list / runs API, not by assuming it fired.
- Nominatim geocodes Russian names inconsistently — the FIX/spot-check list (Ла-Пас -> Bolivia,
  Сямэнь -> China, Брест -> Belarus, Халонг -> Vietnam, Чобе -> Botswana, Фурнаш -> Azores,
  Кировск -> Murmansk, Литисия -> Colombia, Ла-Кьяка -> Argentina, Пуно -> Peru,
  France iso_a2 = -99) keeps the map accurate. Re-verify after any re-geocode.

## Verification
The script's PASS on every check + a clean browser render + live 200 = "всё сделано правильно".

---
name: web-map-static-deploy
description: MapLibre and static-site map gotchas — globe v5 gate cache.
---

# Web map on a static site — verified gotchas

Pitfalls confirmed while wiring an interactive map (MapLibre GL JS) into a
GitHub-Pages static site and then pushing a data change through a CI regenerator.
Read "Verify the deploy" before telling a user a deployed map is fixed.

## 1. MapLibre globe projection only exists in v5+

- `map.setProjection({ type: 'globe' })` was introduced in **MapLibre GL JS v5.0.0**.
- The 4.x line exposes `setTerrain` / `setSky` / `setPitch` but **NOT** `setProjection`.
- Detect it on the loaded lib, don't assume:
  `typeof map.setProjection === 'undefined'` (4.x) vs a function (5.x +).
- Don't diagnose "the globe looks broken" before checking the version gate — a
  flat/planar result on a pinned 4.x is expected, not a bug in your terrain code.
- Terrain (`setTerrain`, `raster-dem`) and globe don't necessarily compose: on a v5
  globe with terrain active (exaggerate 1.6) + pitch 70 the terrain still rendered
  flat. Verify each feature (globe alone; then terrain on a flat projection)
  separately before combining.

## 2. Verifying a fresh deploy — the browser can lie to you

After pushing a change to GitHub Pages, the rendered page may show STALE data even
when the deploy is correct, because:

- A Playwright-MCP browser context **persists its cache across `browser_close`** —
  closing the tab/page does not clear cached JS/CSS. A later `browser_navigate`
  reuses the same context and reloads old `travel-data.js` / `travel.css` from cache.
- So the DOM (sidebar counters, rendered numbers) may not reflect what's served now.

Confirm what the server/deploy is really serving before believing a browser screenshot:

- Read the file directly over HTTP, not via the rendered DOM:
  `curl -s <url>/js/travel-data.js | head -1` — read the auto-generated header
  (`N cities / M countries`) and `grep -c` for a marker you expect to be gone.
- Or inside the browser, bypass cache:
  `fetch('/js/travel-data.js', {cache:'no-store'}).then(r=>r.text())`.
- Cross-check on-disk truth: `git show HEAD:<file> | head -1`.
- Only trust the browser's rendered counters after this file-level check agrees.

## 3. Generate-from-source pipelines that only "add the delta" never remove

A generator that diffs source vs current output and only geocodes/inserts new
records will silently KEEP records you deleted from the source. Removing a row
from the source file (e.g. an `.xlsx`) is not enough to remove it from the output.

For a real removal:

1. Delete the row from the source of truth.
2. Add a **reconcile** step to the generator so it drops records no longer in the
   source: keep `name in source_set ∪ correction_values`, and drop any child
   mapping (e.g. a country polygon) whose parent key has no remaining record.
3. Beware a **CI auto-regen** (a GitHub Action that regenerates output on any push
   touching the source file): it can RE-ADD a removed item unless the updated
   generator (with the reconcile) lands in the SAME push as the source removal, and
   it may fire on the *next* relevant push rather than the introducing commit. Commit
   the generator change together with the source change, then verify the regenerated
   header (section 2) — don't trust that the first push "removed" it.

## 4. Map media images: eager sidebar thumbnails vs on-demand popups

A list/sidebar that renders every map entry builds an `<img>` for each one with NO
`loading="lazy"` by default → all media files (usually the full-size photos) are
fetched eagerly at first paint. With N entries × ~300KB, that's tens of MB on page
open. This is the real client-side load; the server/CDN (GitHub Pages) serves it for
free, so "is the server loaded?" is the wrong question — the cost is first-paint on
the client.

Fix (both halves together):
- Add `loading="lazy"` to the list/sidebar thumbnails so only visible ones load.
- Generate a small thumb variant (e.g. 160px, q70 ≈ 9KB vs 305KB) and reference it in
  the list, keeping the full-size image (1000px) for the on-demand popup. This drops an
  all-photos eager pull from ~60MB to ~2.5MB, and (lazy) further to only what's scrolled.

DO NOT put `loading="lazy"` on popup images injected into a MapLibre popup — they can
fail to appear (dynamic popup DOM). Popup photos stay eager/full-size; only the list
thumbs get lazy + the small variant.

## 5. globe.gl (three.js) 3D globe on the map page

Adding an interactive 3D globe alongside the flat map. The classic failure is a
"just a dark screen" hero: an OPAQUE `#globe-loading` overlay (`z-index:4`) that
that is removed only inside globe.gl's `onGlobeReady` callback — which fires only
AFTER the globe texture loads. A cross-origin CDN texture (unpkg) that stalls
leaves the overlay up forever. Robust init: vendor textures locally (assets/),
make the overlay semi-transparent, force-hide it via a `setTimeout` fallback +
`window` error listeners, and write a message if `typeof Globe === 'undefined'`.
The OTHER classic failure is a hard TypeError — `Cannot set properties of
undefined (setting 'autoRotate')` — that is the Kapsule factory: you MUST call
`Globe()(container)`, not `Globe()`. `globe.controls()` / `.pointOfView()` /
`onGlobeReady` are `undefined` until the configurator is invoked with the DOM
element; guard `if (controls)` and bump the `?v=` cache-busting in the HTML when
you edit the JS so a stale cached file isn't re-served.
Build `pointsData` from the SAME city list as the flat map; accent visited
countries by resolving `cc` (ISO_A2) -> ISO_A3 against the same
`visited_countries.geojson` (NOT the unreliable `POSTAL` field). Use
`pointsData` (WebGL points), not `htmlElementsData` with emoji, for many cities.

Full detail + the exact failure transcript: `references/globe-gl-3d-web-globe.md`.
Verify the data/logic path WITHOUT a browser (headless Chrome hangs on the
animated map page, and browser-use may be unavailable) with:
`node scripts/globe-gl-smoke.js <project_dir>`. For the visual WebGL proof, ask
the user to hard-refresh and report a DevTools console error.

## Verify the deploy

```
curl -s -o /dev/null -w "%{http_code}\n" https://<user>.github.io/<page>.html   # 200
curl -s https://<user>.github.io/js/travel-data.js | head -1                     # read header/count
curl -s https://<user>.github.io/js/travel-data.js | grep -c "<gone-marker>"     # 0
git show HEAD:js/travel-data.js | head -1                                        # on-disk truth
```

If the served header/count matches the on-disk file and the gone-marker is absent,
the deploy is correct — even if a stale browser window showed otherwise.

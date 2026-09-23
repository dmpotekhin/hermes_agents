# globe.gl (three.js) 3D globe on the travel map page

Session-verified pitfalls + the robust init pattern for an interactive 3D globe
(globe.gl / three.js) added to the travel page's static map.

## The "just a dark screen" failure

**Symptom:** the globe hero section renders as a plain dark rectangle — no sphere,
no atmosphere, no points. Everything else on the page works.

**Root cause:** a full-screen opaque loading overlay (`#globe-loading`, bg like
`#070a18`, `z-index:4`) that is removed ONLY inside the globe.gl
`onGlobeReady` callback. globe.gl fires `onGlobeReady` only AFTER the globe
texture loads. If the texture URL is a cross-origin CDN fetch (e.g.
`https://unpkg.com/three-globe/example/img/earth-dark.jpg`) that stalls, the
callback never fires and the opaque overlay stays on top forever. The user sees
a dark screen; there is no error in the console, just a loader that never went
away.

## Robust init pattern (do all of these)

1. **Vendor the textures locally** (like the world geojson): download into the
   repo (`assets/earth-dark.jpg`, `assets/earth-topology.png`) and point
   `globeImageUrl`/`bumpImageUrl` at the local path. Removes the runtime CDN
   dependency that stalls `onGlobeReady` — the #1 cause of the dark screen.
2. **Make the loading overlay semi-transparent** (`background: rgba(7,10,24,0.55)`)
   so a lingering overlay can never fully blank the globe.
3. **Add a guaranteed fallback timer** (`setTimeout(..., ~1300ms)`) that
   force-hides the overlay AND sets the start camera, so the section can never
   sit on a blank screen even if `onGlobeReady` never fires. The sphere + points
   render immediately; anything still loading pops in a moment later.
4. **Safety-net listeners** for `window 'error'` and `'unhandledrejection'` that
   also hide the overlay (covers e.g. WebGL-unavailable throwing in `Globe()`).
5. **Handle `typeof Globe === 'undefined'`** (globe.gl script failed to load):
   hide the overlay and write an explanatory message into `.globe-stats` — don't
   leave a silent dark screen.

## The Kapsule factory bug — TypeError: Cannot set properties of undefined

**Symptom:** hero is a dark screen AND DevTools Console shows:
```
Uncaught TypeError: Cannot set properties of undefined (setting 'autoRotate')
    at travel-globe.js:NN:23
```
The failing line is `controls.autoRotate = true` after `var controls = globe.controls()`.

**Root cause:** globe.gl is a Kapsule factory. `Globe()` returns the *configurator*
(a callable that stores config), and the LIVE globe object — the one with
`.controls()`, `.pointOfView()`, `.onGlobeReady()` callbacks — exists ONLY after
you call the configurator with the container: `Globe()(container)`. If you write
`var globe = Globe()....` (no `(container)` call), `globe.controls()` is
`undefined` because the globe was never instantiated against a DOM element.

**Fix — instantiate with the container, then chain:**
```js
var globe = Globe()(container)     // container = the DOM element (#globe)
  .globeImageUrl(DARK_TEX)
  .bumpImageUrl(BUMP_TEX)
  ...;
var controls = globe.controls();
if (controls) {   // guard: some builds / pre-init may still be null — never let it throw
  controls.autoRotate = true;
  controls.autoRotateSpeed = 0.55;
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
}
```

**Why the Node smoke probe did NOT catch this:** the probe mocks `Globe` so every
accessor returns a chainable stub — so `globe.controls()` in the mock returns a
stub whose `.autoRotate` is settable, and the TypeError never throws. A chainable
mock SILENTLY masks real library API misuse. For real-API-only bugs, assert
`globe.controls()` is non-null in the probe, or do one real-browser run.

## Cache-bust the edited file

If the page loads a `.js` bundl(e.g. `travel-globe.js`) with a `?v=` query string,
BUMP the version in the HTML reference whenever you edit the file, then confirm
the served URL is the new one (`curl` it + grep for a marker). If you leave the
old `?v=`, a browser that cached the buggy file under that URL keeps showing the
OLD code even after your fix — the console error URL (`travel-globe.js?v=...`)
reveals the cached version. A new `?v=` forces a fresh fetch without a hard
refresh.

## Single source of truth

Build `pointsData` from the SAME city list the flat map uses
(`window.TRAVEL_CITIES`, `{name, country, cc, lat, lng}`), mapped to
`{city, country, lat, lng}` — don't hand-duplicate.

Accent visited countries by resolving `cc` (alpha-2) -> ISO alpha-3 against the
SAME `data/visited_countries.geojson` the flat map renders (build an
`iso2ToIso3` map from `properties.ISO_A2`/`ISO_A3`). Do NOT match on the Natural
Earth `POSTAL` field — it is unreliable (no RU/IN/DE/JP). `ADM0_A3` is the
reliable per-feature key. One polygon layer (world geometry) with a `__visited`
flag; visited get accent fill/altitude, others near-transparent neutral.

Micronations (Vatican, Singapore) are absent from the 110m world dataset — the
country won't fill as a polygon but the city POINT still renders. Expected.

## Many city points: use pointsData, not htmlElementsData

For N >> ~50 points, use `pointsData` (WebGL points). `htmlElementsData` with
emoji creates one DOM element per point — slow and cluttered at 255 points.
Use `pointLat`/`pointLng`/`pointColor`/`pointRadius`/`pointAltitude`/
`pointLabel` (label = "<b>City</b><br><span>Country</span>" HTML).

## Verify without a browser

`node scripts/globe-gl-smoke.js <project_dir>` — mocks Globe/fetch/DOM, runs the
real IIFE against real data, and asserts pointsData length == cities,
polygonsData length == world features, accent count, autoRotate+damping on, and
that the onGlobeReady/onPointClick callbacks fire. No WebGL needed.
`node --check js/travel-globe.js` for syntax.

## Don't chase browser-screenshot verification on an animated map page

Headless Chrome `--screenshot`/`--virtual-time-budget` HANG on a page whose flat
MapLibre map keeps loading tiles (rAF + network never goes idle), and a
browser-use/browser-harness daemon may be unavailable. Verify the data/logic path
with the Node smoke probe; for the visual WebGL proof, ask the user to hard
refresh (Cmd+Shift+R) and report any DevTools console error.

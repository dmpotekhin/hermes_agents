---
name: map-route-visualization
description: Use when building map/route web apps (FastAPI + MapLibre).
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [fastapi, maplibre, geocoding, routing, here-api, nominatim, maps]
    related_skills: [full-stack-fastapi-react, fullstack-fastapi-react]
---

# Map / Route Visualization Apps

Build a local web app that turns a list of places (cities, stops) into an
interactive map with route lines, colored by transport, an animated marker, and
aggregate analytics (total km, equators, distance-to-moon, per-year/per-transport
breakdown).

Reference project: `~/projects/travel-visualizer` (FastAPI + vanilla JS +
MapLibre GL JS + SQLite). Proven end-to-end: 30 pytest + live curl smoke.

## When to use

- User wants a "map of my trips/routes", route animation, or travel analytics.
- Geocoding cities + computing distances between them.
- A "visualize X on a map" local tool with no external service dependency.

## Architecture: paid API OPTIONAL, free fallback ALWAYS

The single highest-leverage decision: never make the app depend on a paid key
(HERE, Google, Mapbox). Structure it as a ladder and make the fallback the
tested, always-working default:

```
geocode city:  built-in cache → HERE Geocoding → Nominatim
route segment: air → great-circle always
               surface + key → HERE Routing v8 (real geometry) → Matrix API (distance only)
               no key       → Haversine distance + great-circle arc
```

This means the demo works instantly (cache ~60 major cities + Haversine) and the
paid key only upgrades accuracy. The user can register for the key AFTER seeing
the app work. Key lives in `.env` only (gitignored), never in code.

### Built-in city cache

Keep a hardcoded `{name_lower: (lat, lon)}` dict of ~50-60 common cities in both
Cyrillic and Latin forms. Makes the demo route instant and avoids hammering
Nominatim. Add `спб`/`питер` aliases for common abbreviations.

### Nominatim (free) etiquette

- 1 req/sec courtesy limit — track `time.monotonic()` of last call and sleep.
- MUST send a `User-Agent` header; Nominatim rejects generic agents.
- Endpoint: `https://nominatim.openstreetmap.org/search?q=NAME&format=json&limit=1`

### Haversine + great-circle interpolation

Two ~20-line functions you need: `haversine_km(lat1,lon1,lat2,lon2)` and a
spherical slerp returning GeoJSON `[lon,lat]` points along the arc. Use slerp
(not linear lat/lon interpolation) or long-haul flights render as straight lines
that drift from the real great-circle.

## HERE API (when key present)

- Geocode: `GET https://geocode.search.hereapi.com/v1/geocode?q=NAME&apiKey=KEY`
  → `items[0].position.{lat,lng}`.
- Routing v8: `GET https://router.hereapi.com/v8/routes?transportMode=car&origin=lat,lng&destination=lat,lng&return=polyline,summary&apiKey=KEY`
  → `routes[0].sections[0]` has `summary.{length,duration}` (meters/seconds) and
  a `polyline` string. transportMode supports car/bus/bicycle/pedestrian/taxi —
  **not rail or air**.
- Matrix v8: `GET https://matrix.router.hereapi.com/v8/matrix?origin=...&destination=...&transportMode=...&apiKey=KEY`
  → `matrix[0][0].summary` — distance/duration WITHOUT geometry. Use as fallback
  when you don't want to decode polylines.
- The `polyline` field is **flexible-polyline** encoding (NOT Google's). Decoder
  + test vector: see `references/here-flexible-polyline.md`. Decode to real road
  geometry; if decode fails, fall back to great-circle but keep the HERE distance.

## Replaceable routing providers (fallback chain)

When the app may use several routing backends (HERE / OSRM / GraphHopper), make
route calculation depend on an abstraction, never on a concrete API:

- `RoutingProvider` ABC with `supports(transport) -> bool` and
  `route(origin, destination, transport) -> RouteResult` (transport,
  distance_km, duration_min, geometry, provider name, provider_info). A
  `RouteResult.to_dict()` keeps the rest of the pipeline unchanged (backward
  compat).
- Chain factory: order from env (`ROUTING_PROVIDER_ORDER`, "auto" =
  HERE,OSRM,GRAPHHOPPER,GREAT_CIRCLE). Unconfigured providers (missing key/URL)
  are SKIPPED with a log, not an error; a deterministic great-circle provider is
  always appended last so the app works with zero keys.
  `ROUTING_FALLBACK_ENABLED=false` = strict mode (raise instead of silent
  fallback).
- LAZY-import providers inside the factory (`from .osrm import ...` at call
  time) so provider modules can land incrementally without breaking the package.
- **Every provider MUST translate its failures (network, HTTP status, parse,
  "no route") into the shared error hierarchy** (e.g. `ProviderUnavailableError`
  deriving from `RoutingError`). If one provider raises a raw `RuntimeError`,
  the chain's `except RoutingError` misses it and the app crashes instead of
  falling through — this bit us: OSRM/GraphHopper initially raised raw httpx
  errors and the whole chain died.
- Annotate results: each segment dict gets `provider` (who computed it) and, on
  fallback, `provider_fallback` (reasons). GeoJSON properties carry `provider`
  for diagnostics; the frontend just renders it.
- Provider-agnostic API: `POST /api/routes` accepts legs
  `{from:{lat,lon,name?}, to:{...}, transport:"CAR"|"train"}` and returns the
  same route shape as the string-input pipeline. One `coerce_transport()` maps
  enum/uppercase/legacy keys to internal keys (enum values = internal keys for
  DB/GeoJSON compat); unknown → 422.
- Map styling per transport: `line-dasharray` + `['match', ['get','transport'],
  ...]` (rail dash, foot dots, bike dash-dot, air long strokes); white overlay
  dashes get `line-opacity` match → 0 for patterned transports so the two
  patterns don't fight.
- Provider geometry encodings differ: HERE returns **flexible polyline**,
  OSRM/GraphHopper return **Google polyline5** — never share one decoder.
  Endpoints, profile mapping, test vectors, and the Google-vs-flexible
  accumulation rule: `references/polyline-decoders.md`.

## Route-string parsing (the subtle part)

Split a route like `Санкт-Петербург – Москва – Пекин` into segments.

**Hyphen pitfall (bit us):** a bare hyphen-minus `-` must NOT split city names.
Rule: long dashes (`—`, `–`, `−`) and arrows (`→`, `->`) are always separators;
a plain `-` is a separator only when surrounded by spaces. Otherwise
`Санкт-Петербург`, `Нью-Йорк`, `Буэнос-Айрес` get chopped.

```python
_SPLIT_RE = re.compile(r"\s*(?:—|–|−|->|→|=>|>|»)\s*|\s+-\s+")
```

**Transport detection:** per-segment type via inline annotation
`Город [поезд]` / `Город (самолёт)` (marks the segment LEAVING that city), else
global keyword detection over the raw string (`на поезде`, `самолётом`, `на авто`),
else a default (`car`). Strip global transport phrases (`на поезде`, `паромом`,
`пешком`, ...) from the text BEFORE splitting, or they pollute the last city name
(`"Берлин на поезде"`). Keyword list must be ordered specific-first (e.g.
`авиа` before `air`). Keep a speed table per transport for time estimates
(air 850, rail 80, car 90, bus 70, ferry 35, bike 18, foot 5 km/h).

## GeoJSON shape

One FeatureCollection; each segment a LineString Feature with
`properties: {from, to, transport, transport_name, distance_km, duration_min, color}`.
Add Point features for city labels. This single shape feeds both the map and the
animation, and can be reconstructed from SQLite (store segments as JSON, incl.
geometry) so `/map/{id}` works without recomputation.

## MapLibre GL JS (no key, no build step)

- Serve tiles from OSM raster (free, no token) via an inline style:
  `sources.osm = {type:'raster', tiles:['https://tile.openstreetmap.org/{z}/{x}/{y}.png'], tileSize:256, attribution:'© OpenStreetMap contributors'}`.
- Color each segment by a feature property: `'line-color': ['get','color']`.
- Animated marker: flatten LineString coords → cumulative haversine lengths →
  `interpolate(coords, cum, frac)` → `marker.setLngLat()` in `requestAnimationFrame`.
  Use a DOM-element `maplibregl.Marker` (no sprite needed on raster tiles).
- No `icon-image` symbol icons on OSM raster style — use a `circle` layer for
  dots + a `symbol` layer with `text-field` for labels.
- CDN: `https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.{js,css}`.

## MapLibre GL JS v4 — cinematic FX + style switcher pitfalls (bit us)

- `line-gradient` + `line-progress` (gradient along the line) require
  `lineMetrics: true` on the GeoJSON **source** options, NOT inside the GeoJSON
  feature properties (the docs phrasing is misleading). Merge all segments into
  ONE LineString for a full-route gradient, else `line-progress` resets per feature.
- `map.setStyle()` fires `styledata` (several times), NOT `style.load`. To re-add
  custom sources/layers after a style switch, poll
  `if (map.isStyleLoaded() && !map.getSource('route')) addRouteLayers()` via
  `setTimeout` (~120 ms) — deterministic and beats racing the event. The
  `getSource(...)` guard keeps it idempotent against the frequent `styledata`
  fired by `source.setData()` (e.g. an animating trail layer).
- A `symbol` layer with `text-field` but NO `text-font` makes MapLibre request the
  DEFAULT font stack ("Open Sans ...") from the style's glyphs endpoint — 404s on
  styles that only host "Noto Sans". Always set `text-font` explicitly.
- Free vector basemap styles, no API key: Carto
  `https://basemaps.cartocdn.com/gl/{voyager,positron,dark-matter}-gl-style/style.json`
  and OpenFreeMap `https://tiles.openfreemap.org/styles/{liberty,bright}`. AVOID
  `openmaptiles.github.io/*/style-cdn.json` — it embeds a dead MapTiler demo key
  and returns 403.
- Smooth "running light" along a line: animate `line-gradient` stops around a
  moving center (`['interpolate',['linear'],['line-progress'], ...]`) — native and
  smooth. There is NO native dash-offset, so `line-dasharray` alone cannot march.

## Client-side video/GIF export of a MapLibre animation

- The WebGL map canvas needs `canvasContextAttributes: { preserveDrawingBuffer: true }`
  in the `new maplibregl.Map(...)` options, else `canvas.captureStream()` /
  `new VideoFrame(canvas)` captures black.
- Composite onto a plain 2D canvas: `ctx.drawImage(map.getCanvas(), ...)` cover-cropped
  to the target resolution, then draw watermark/title overlays. Capture the 2D
  canvas (not the WebGL one) so overlays are included.
- Format matrix: WebM = `MediaRecorder` (VP9/VP8); MP4 = native `MediaRecorder`
  `video/mp4` on Safari, else WebCodecs `VideoEncoder` (`avc1.42001f`,
  `avc:{format:'avc'}`) + `mp4-muxer` (global `Mp4Muxer.Muxer`); GIF = `gif.js`.
- Vendor `mp4-muxer.min.js`, `gif.js`, and `gif.worker.js` into `frontend/vendor/`
  and lazy-load them — gif.js with a cross-origin `workerScript` can silently hang
  at progress 0. Full recipe + the `select.value`→NaN debug path in
  `references/maplibre-cinematic-and-export.md`.

## Hybrid 2D (MapLibre) / 3D (CesiumJS) + route-video constructor

When the app grows into a mult.dev-style "route video constructor" (a step
wizard + a 2D↔3D animation/export studio), keep it **additive** — new
`wizard.html` / `studio.html` pages, never rewrite `/`, `/animate`, `/upload`,
`/map/{id}`. Hand the project wizard→studio via `localStorage` (photos as
compressed base64 data URLs stay client-side; no re-upload on every edit).

CesiumJS top gotchas (full recipe in `references/cesium-3d-globe.md`):
- CDN via jsdelivr + set `window.CESIUM_BASE_URL` to the same `Build/Cesium/`
  dir **before** the script tag, or its workers/assets 404.
- `new Cesium.Viewer(el, { baseLayer: false, contextOptions: { webgl:
  { preserveDrawingBuffer: true } }, ... })` — `baseLayer:false` stops Cesium
  auto-creating the default Ion imagery (which 401s with an empty token);
  `preserveDrawingBuffer` is required to `drawImage`/capture the globe canvas.
- No Ion token needed for imagery: `UrlTemplateImageryProvider` with OSM / Carto
  raster (light/dark) or Esri World Imagery (satellite). Terrain needs Ion —
  flat ellipsoid is fine for route visuals.
- Sync: ONE shared `state.frac` + ONE `requestAnimationFrame` loop drives both
  views; the 2D↔3D toggle just shows/hides containers (+ `map.resize()` /
  `viewer.resize()`), so a switch at any moment is at the current position.
  Update Cesium entities every frame but call `viewer.render()` only when 3D is
  active (hidden canvases waste GPU).
- Transport icon on the globe: `BillboardGraphics` with `image =
  canvas.toDataURL()` emoji, swapped per segment.

Track/URL input (GPX / KML / KMZ / GeoJSON, Google-Maps links) — stdlib only
(`xml.etree.ElementTree` + `json`), no gpxpy/togeojson. Two pitfalls:
- **Namespace wildcard does NOT work in `iter()`**: `root.iter("{*}trkpt")`
  matches nothing. Use `el.tag.rsplit("}", 1)[-1]` to compare local names.
- Long tracks → hundreds of segments. Douglas-Peucker `simplify_to(coords,
  max_points=24)` before `coords_to_segments`, or the transport UI/animation
  explode. See `backend/track.py` in the reference project.

## FastAPI + vanilla-JS pitfalls (this class)

- Register ALL routers BEFORE `app.mount("/", StaticFiles(html=True))` or `/api/*`
  and `/health` return 404 (mount shadows them).
- `StaticFiles(html=True)` serves `/index.html` at `/` but does **NOT** map
  `/wizard` → `wizard.html` — that path 404s. For clean URLs add an explicit
  `@app.get("/wizard")` → `FileResponse(FRONTEND_DIR / "wizard.html")` route
  (before the mount). Same for `/studio`.
- Avoid naming a route function the same as an imported router module (e.g.
  `async def studio()` vs `from .routers import studio`) — shadows the module
  and breaks `include_router(studio.router)`.
- SQLite path: compute absolute from `__file__` (relative `./data/` resolves from
  CWD, not project root).
- Read the map HTML template lazily (on first render), not at import time, so the
  app imports cleanly before the template exists. Inject route data by replacing a
  `__ROUTE_CONFIG__` token with `json.dumps(...).replace("</", "<\\/")`.
- `POST /animate` returning a full HTML page: simplest UX is a normal form
  `action="/animate" method="POST"` (browser navigates to the returned HTML).
  `/upload` (multipart) returns JSON → handle with `fetch` + render inline.
- `.env` via write_file can mangle lines with `***`+newlines — use terminal
  heredoc for `.env`, or just never put `***` in the file.
- On macOS without Xcode CLT, prefer plain `uvicorn` over `uvicorn[standard]`
  (avoids native uvloop/httptools/watchfiles builds).

## CSV/Excel upload parsing

- Match columns by header keyword (case-insensitive), not position:
  route→`маршрут`/`route`, year→`год`/`year`, note→`примечан`/`note`,
  distance→`расстоян`/`км`/`distance`. Survives renamed/reordered columns.
- CSV: `utf-8-sig` decode (BOM), sniff `;` vs `,` delimiter. Excel: openpyxl
  `read_only=True, data_only=True`; skip `.xls` (unsupported).
- Return per-row `declared_km` vs `computed_km` so the user sees their own
  figure against the routed one.

## Verification

- Use FastAPI `TestClient(app)` with a monkeypatched `config.DB_PATH` pointing at
  a tmp file (isolate DB per test) — the demo route resolves from the built-in
  cache so tests never touch the network.
- pytest covers: parsing, transport detection, haversine, decoder, analytics,
  CSV/Excel, and full API e2e. Prefer `python -m pytest` (and script files) over
  inline `python -c` when running checks.
- **`pytest -q 2>&1 | tail` masks the exit code** (tail exits 0), so
  `... | tail && git commit` commits WITH FAILING TESTS — bit us twice in one
  session. Before any commit gate run `set -o pipefail`, or don't pipe at all;
  also confirm the last pytest line says "N passed" in the captured log.
- **Local run recipe (this class):** `.venv/bin/python -m uvicorn backend.app:app
  --host 127.0.0.1 --port 8765` in background (watch for "Uvicorn running"), then
  curl `/health`, `/` (wizard), `/studio`, and a `POST /animate` — all 200 —
  before handing the URL to the user. Without a HERE key, `/health` reports
  `here_api_key:false` and routes fall back to great-circle: expected, tell the
  user, don't chase it.
- **Browser smoke: prefer the playwright MCP toolset** (`mcp__playwright__browser_navigate` /
  `browser_console_messages` / `browser_evaluate`). If the built-in browser tool
  errors at launch (e.g. transient npx cache corruption), don't retry it
  repeatedly — switch to playwright MCP; same capabilities, separate runtime.
  Useful assertions without full DOM dumps: `document.querySelectorAll('canvas').length`
  (map rendered), `#info-rows` / legend innerText, and console-error count == 0.
- **After an architecture refactor, prove the abstraction landed with graphify**
  (skill `graphify-knowledge-graph`): run code-only extraction + `cluster-only
  --no-label`, then read the God Nodes list. The new abstractions (provider
  classes, error hierarchy, chain factory) should dominate the top hubs — cheap
  structural confirmation alongside green tests.

## Reference files

- `references/here-flexible-polyline.md` — exact decoder algorithm + known test
  vector for HERE flexible-polyline.
- `references/polyline-decoders.md` — Google polyline5 vs HERE flexible
  (accumulation rule, test vectors), OSRM/GraphHopper endpoints + profile
  mapping, error-wrapping reminder for provider chains.
- `references/maplibre-cinematic-and-export.md` — gradient/lineMetrics, running
  light, style-switcher poll, free basemap styles, canvas video/GIF export
  (WebM/MP4/GIF), and the `select.value`→NaN debugging trap.
- `references/cesium-3d-globe.md` — full CesiumJS hybrid 3D recipe: CDN +
  `CESIUM_BASE_URL`, `baseLayer:false` (avoids the 401-without-token), free
  imagery providers, emoji billboard marker, shared-frac sync, canvas capture.

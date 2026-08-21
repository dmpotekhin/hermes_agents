# MapLibre cinematic FX + client-side video export

Detail for the v2 upgrade of the map/route app. All verified in Playwright against
`~/projects/travel-visualizer` (WebM 2 MB, MP4 5 MB, GIF 4.5 MB actually produced).

## Gradient line (line-gradient + lineMetrics)

`line-gradient` colors a line by `line-progress` (0..1 along the feature). It only
works when the SOURCE has line metrics enabled — and that flag lives on the
GeoJSON source OPTIONS, not inside the GeoJSON data:

```js
map.addSource('route-gradient', {
  type: 'geojson',
  lineMetrics: true,                         // <-- here, not in the Feature
  data: { type: 'Feature', properties: {},
          geometry: { type: 'LineString', coordinates: mergedCoords } },
});
map.addLayer({
  id: 'route-gradient', type: 'line', source: 'route-gradient',
  layout: { 'line-join': 'round', 'line-cap': 'round' },
  paint: { 'line-color': ['interpolate', ['linear'], ['line-progress'],
             0, '#3b82f6', 0.5, '#8b5cf6', 1, '#ef4444'],
           'line-width': 5 },
});
```

Merge ALL segments into one LineString (dedupe consecutive identical endpoints) so
`line-progress` spans the whole route, not each segment.

## Running light (moving pulse) — there is no dash-offset

MapLibre has no native dash-offset, so `line-dasharray` cannot "march". Instead
animate `line-gradient` stops around a moving center `p` (0..1). Enforce strictly
increasing stop positions (drop duplicates) or MapLibre throws:

```js
function pulsePaint(frac) {
  const w = 0.05, head = Math.min(Math.max(frac, 0), 1);
  const stops = [[0, 'rgba(255,255,255,0)']];
  const a = Math.max(0, head - w), b = Math.min(1, head + w);
  if (a > 0) stops.push([a, 'rgba(255,255,255,0)']);
  stops.push([head, 'rgba(255,255,255,0.95)']);
  if (b < 1) stops.push([b, 'rgba(255,255,255,0)']);
  stops.push([1, 'rgba(255,255,255,0)']);
  const clean = []; let last = -1;
  for (const [t, c] of stops) { const tt = Math.min(Math.max(t, 0), 1); if (tt <= last) continue; clean.push(tt, c); last = tt; }
  return { 'line-color': ['interpolate', ['linear'], ['line-progress'], ...clean], 'line-width': 6 };
}
// each frame: map.setPaintProperty('route-pulse', 'line-color', pulsePaint(frac)['line-color'])
```

A static dashed texture on top (`line-dasharray: [1.5, 2.5]`, low opacity) reads as
"пунктир" while the moving pulse is the "огонёк".

## Style switcher (re-add layers after setStyle)

`map.setStyle(url)` in MapLibre v4 emits `styledata` (multiple times) but NOT
`style.load`. Polling is deterministic and survives the event race:

```js
sel.addEventListener('change', (e) => {
  map.setStyle(e.target.value);
  const attempt = () => {
    if (map.isStyleLoaded() && !map.getSource('route')) { addRouteLayers(); bindPopups(); return; }
    setTimeout(attempt, 120);
  };
  attempt();
});
```

`addRouteLayers()` must start with `if (map.getSource('route')) return;` so the
poll and any duplicate `styledata` (e.g. from `source.setData()` on the trail)
stay idempotent. DOM markers (`maplibregl.Marker`) survive a style switch — only
sources/layers need re-adding; keep trail coords in a JS array and re-set them on
the recreated source.

## text-font pitfall

A symbol layer without `text-font` requests the DEFAULT font stack ("Open Sans
Regular, Arial Unicode MS Regular") from the style's glyphs endpoint. On styles
whose glyphs host only "Noto Sans" (OpenFreeMap) that 404s. Always set
`'text-font': ['Noto Sans Regular']` explicitly. (OpenFreeMap hosts Noto Sans
Regular/Bold/Italic only.)

## Free vector basemap styles (no API key)

- Carto (free, attribution): `https://basemaps.cartocdn.com/gl/{voyager,positron,dark-matter}-gl-style/style.json`
- OpenFreeMap (free): `https://tiles.openfreemap.org/styles/{liberty,bright}`
- OpenFreeMap vector tiles: `https://tiles.openfreemap.org/planet`; glyphs
  `https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf`; sprite
  `https://tiles.openfreemap.org/sprites/ofm_f384/ofm`.
- DO NOT use `https://openmaptiles.github.io/{positron,dark-matter}-gl-style/style-cdn.json`
  — it embeds a dead MapTiler demo key → 403.

## Video/GIF export (all client-side)

Map options must include `canvasContextAttributes: { preserveDrawingBuffer: true, antialias: true }`.

Composite onto a 2D canvas so watermark + intro/outro titles are captured too:

```js
const composite = document.createElement('canvas'); composite.width = W; composite.height = H;
const ctx2d = composite.getContext('2d');
function drawComposite(frac, elapsed, totalMs) {
  ctx2d.fillStyle = '#000'; ctx2d.fillRect(0, 0, W, H);
  const src = map.getCanvas(); const scale = Math.max(W / src.width, H / src.height);
  ctx2d.drawImage(src, (W - src.width * scale) / 2, (H - src.height * scale) / 2, src.width * scale, src.height * scale);
  // watermark + titles here
}
```

Drive the animation deterministically: pause the live loop, reset `frac = 0`, then
a `requestAnimationFrame` loop advancing `frac = Math.min(1, elapsed * speedFactor / DURATION)`
and calling the SAME `update(frac)` used for live playback. Capture at the target
fps (`if (elapsed - lastCapture >= 1000 / fps)`).

- WebM: `composite.captureStream(fps)` → `MediaRecorder` with
  `['video/webm;codecs=vp9','video/webm;codecs=vp8','video/webm']` (first supported).
- MP4 on Safari: `MediaRecorder` with `['video/mp4;codecs=avc1','video/mp4']`.
- MP4 on Chrome/Edge: WebCodecs — `new VideoFrame(composite, { timestamp })` per
  frame into `VideoEncoder` configured `{ codec:'avc1.42001f', width, height,
  bitrate, framerate, avc:{format:'avc'} }`; mux with
  `new Mp4Muxer.Muxer({ target:new Mp4Muxer.ArrayBufferTarget(), video:{codec:'avc',width,height}, fastStart:'in-memory' })`;
  then `await encoder.flush()` → `muxer.finalize()` → `muxer.target.buffer`.
- GIF: `new GIF({ workers:2, quality:10, width, height, workerScript:'/vendor/gif.worker.js' })`,
  `gif.addFrame(composite, { copy:true, delay:1000/fps })` per frame, `gif.render()`,
  `gif.on('finished', blob => ...)`. Cap width ~640 to keep the file sane.

Vendor the libs locally (`frontend/vendor/`) and lazy-load on first export:
`mp4-muxer.min.js` (global `Mp4Muxer`), `gif.js` (global `GIF`), `gif.worker.js`.
gif.js with a cross-origin `workerScript` can hang at progress 0 — a same-origin
vendor copy fixes it.

## Debugging pitfall that cost an hour: select.value + parseInt

Setting `<select id="exp-fps">` to a value that is NOT one of its `<option>`s
(e.g. `select.value = '10'` when options are 15/30/60) silently makes `.value`
equal `""`. Then `parseInt(select.value, 10)` → `NaN` → `interval = 1000/NaN = NaN`
→ the capture branch `elapsed - lastCapture >= interval` never fires → 0 frames
recorded, but the loop still completes (frac uses speedFactor/DURATION, not fps).
Result: "finished" with an empty output and the start button stuck disabled
(disabled buttons swallow click events, so retries silently no-op).

Guards: `const fps = parseInt(sel.value, 10) || 30;` and re-enable the start button
in a `finally` / every completion path. When debugging "0 frames", log
`fps`/`interval` FIRST — it was NaN, not a timing bug.

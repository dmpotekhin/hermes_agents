# CesiumJS hybrid 3D globe (2D/3D route studio)

Proven recipe for adding a 3D CesiumJS globe alongside a MapLibre 2D map, with a
single shared animation state so a 2D↔3D toggle never loses position. Verified
against Cesium 1.117 loaded from CDN with **no Ion token**.

## CDN load (order matters)

```html
<link href="https://cdn.jsdelivr.net/npm/cesium@1.117.0/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
<script>
  window.CESIUM_BASE_URL = 'https://cdn.jsdelivr.net/npm/cesium@1.117.0/Build/Cesium/';
</script>
...
<script src="https://cdn.jsdelivr.net/npm/cesium@1.117.0/Build/Cesium/Cesium.js"></script>
```

`CESIUM_BASE_URL` must be set BEFORE the `Cesium.js` script tag or its
workers/assets 404 (the globe renders but imagery/geometry workers fail). Pin a
full `x.y.z` version on jsdelivr — `@1` resolves to an unknown newer minor and
can change the API under you.

## Viewer construction (the two lines that bite)

```js
Cesium.Ion.defaultAccessToken = window.CESIUM_ION_TOKEN || '';
const viewer = new Cesium.Viewer('globe-3d', {
  baseLayerPicker: false, geocoder: false, homeButton: false, sceneModePicker: false,
  navigationHelpButton: false, animation: false, timeline: false, fullscreenButton: false,
  infoBox: false, selectionIndicator: false,
  baseLayer: false,   // <-- KEY: don't create default Ion imagery (else 401 with empty token)
  contextOptions: { webgl: { preserveDrawingBuffer: true, antialias: true } },  // <-- KEY for canvas capture
});
```

- Without `baseLayer: false`, Cesium constructs its default Bing/Ion imagery and
  immediately fires `GET https://api.cesium.com/v1/assets/2/endpoint?access_token=`
  → **401** + an `Eq`-style exception from the Cesium bundle. `removeAll()` after
  the fact does not stop the initial async fetch. Add `baseLayer:false` and
  supply your own imagery.
- `preserveDrawingBuffer: true` is required to `ctx.drawImage(viewer.scene.canvas, …)`
  or `captureStream()` — otherwise the captured globe is black (same rule as
  MapLibre's `canvasContextAttributes`).

## Free imagery (no Ion token)

```js
const STYLES_3D = [
  { id: 'dark',  name: 'Тёмный',      url: 'https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png' },
  { id: 'light', name: 'Светлый',     url: 'https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png' },
  { id: 'sat',   name: 'Спутниковый', url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}' },
];
viewer.imageryLayers.addImageryProvider(new Cesium.UrlTemplateImageryProvider({ url: url }));
```

- Carto dark/light raster + Esri World Imagery all work keyless. Real terrain
  (`createWorldTerrainAsync`) requires Ion — flat ellipsoid is enough for route
  animation.

## Route entities

```js
const flat = coords.flatMap(c => [c[0], c[1]]);          // coords are [lon,lat]
viewer.entities.add({ polyline: { positions: Cesium.Cartesian3.fromDegreesArray(flat),
  width: 2.5, material: Cesium.Color.fromCssColorString('#3b82f6').withAlpha(0.85) } });
traveledEntity = viewer.entities.add({ polyline: { positions: [], width: 4,
  material: Cesium.Color.fromCssColorString('#ffffff').withAlpha(0.9) } });
markerEntity = viewer.entities.add({ position: Cesium.Cartesian3.fromDegrees(lon, lat),
  billboard: { image: emojiUrl('🚗'), scale: 0.6, verticalOrigin: Cesium.VerticalOrigin.CENTER } });
```

Emoji billboard (Cesium has no emoji sprite): draw the emoji to a canvas and feed
`toDataURL()` as the billboard image; recreate per segment transport.

```js
function emojiUrl(emoji) {
  const c = document.createElement('canvas'); c.width = 96; c.height = 96;
  const ctx = c.getContext('2d');
  ctx.font = '72px "Apple Color Emoji","Segoe UI Emoji",sans-serif';
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText(emoji, 48, 54);
  return c.toDataURL('image/png');
}
```

## Shared-state sync (the whole point)

One `state.frac` + one `requestAnimationFrame` loop drives BOTH views. Both
`renderMap(frac)` and `renderGlobe(frac)` read the same frac, so toggling 2D↔3D
at any moment is already at the correct position. Update Cesium entity positions
every frame (cheap) but call `viewer.render()` only when 3D is active — hidden
Cesium canvases burn GPU for nothing.

```js
function renderGlobe(frac) {
  const pos = interpolate(coords, cum, frac);           // same interpolate as 2D
  markerEntity.position = Cesium.Cartesian3.fromDegrees(pos[0], pos[1]);
  // traveled trail: coords[0..i] + current pos
  traveledEntity.polyline.positions = Cesium.Cartesian3.fromDegreesArray(trailFlat);
  if (state.follow) viewer.trackedEntity = markerEntity;  // camera follow
  if (state.mode === '3d') viewer.render();
}
```

On 2D↔3D switch: hide/show containers, then `viewer.resize()` (or `map.resize()`)
after the container becomes visible — a canvas that was `display:none` has 0 size
and needs a resize to render correctly.

## Capture for export

Cesium's canvas is WebGL too — draw it onto a 2D composite canvas (cover-cropped
to the target aspect) AFTER `viewer.render()`, then stamp watermark/titles, exactly
like the MapLibre path. With `preserveDrawingBuffer:true` the `drawImage` is not
black. In 2D mode the DOM `maplibregl.Marker` is NOT in the canvas (re-draw it),
but in 3D mode the Cesium billboard marker IS in the canvas — no re-draw needed;
gate on `mode === '2d'`.

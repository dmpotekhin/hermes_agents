# MapLibre GL: clusters, always-visible markers, per-feature fill

Notes from building a visited-countries travel map (dmpotekhin.github.io/travel.html).
These bite every time; captured as a class-level recipe.

## 1. Marker clustering HIDES individual points at low zoom

The standard pattern — a `cluster: true` GeoJSON source + a `symbol` layer filtered
`['!', ['has','point_count']]` — shows NO individual markers until the clusters
break apart at high zoom. Users report exactly this: "heart/point markers only appear
when I zoom in a lot."

FIX: two sources sharing the same FeatureCollection, one dataset:

```js
source('cities',      { type:'geojson', data, cluster:true })  // ONLY for cluster circles
source('cities_flat', { type:'geojson', data })                // cluster:false, for markers

// layer order (addClusterLayers AFTER addMarkerLayer as needed):
addLayer(cluster-circle)  ->  addLayer(markers on 'cities_flat')  ->  addLayer(cluster-count)
```

- Markers come from `cities_flat` → always visible at EVERY zoom (world + city view).
- The clustered `cities` source drives only the pink cluster circles.
- Drop the `['!',['has','point_count']]` filter on the marker layer entirely.

## 2. Cluster counts get buried under the markers

If the marker `symbol` layer is added AFTER the count layer, markers overlap the
count numbers. Add in this order: `cluster-circle → markers → cluster-count`, so the
counts render on top of the marker sea. Keep the counts legible with a text halo:

```js
'text-color': '#ffffff', 'text-halo-color': '#c2103f', 'text-halo-width': 1.5
```

## 3. Per-feature fill (flag-colored countries)

Add a `fillColor` hex property to each GeoJSON feature at build time, then:

```js
'fill-color': ['get','fillColor'], 'fill-opacity': 0.6,
// outline same color:
'line-color': ['get','fillColor'], 'line-width': 1.1, 'line-opacity': 0.9
```

## 4. Google-Maps-style custom marker (crisp at retina)

Draw the marker on a canvas → `canvas.getContext('2d').getImageData(...)` and register
with `pixelRatio: 2` so it's sharp on retina displays. Use a `symbol` layer with
`icon-image`. Interpolate `icon-size` by zoom so markers shrink at world zoom and
don't blob into a sea:

```js
map.addImage('heart', makeHeartImage(), { pixelRatio: 2 })
'icon-size': ['interpolate',['linear'],['zoom'], 1, 0.42, 6, 0.62]
```

## 5. Data-driven styling requires the property, not just the geometry

For fill-by-flag you need the data pipeline to emit `fillColor` per country in the
GeoJSON (derived from a lookup, e.g. a JSON mapping ISO_A2 -> flag hex). The map layer
just reads it with `['get','fillColor']`.

## 6. GitHub Pages / CDN cache lag after push

The edge CDN keeps serving the OLD JS for ~40-90s after a push. A browser screenshot
(even a fresh browser context) can show the stale file. VERIFY the deployed artifact by
fetching it and probing for a version marker, and only then trust the render:

```python
# stdlib urllib — probe deployed JS for a feature only present in the new build
js = urllib.request.urlopen('https://SITE/travel.js').read().decode()
assert 'text-halo-color' in js and 'cities_flat' in js   # new build is live
# loop until the marker appears; only then screenshot
```

Also use a brand-new browser context (not the shared one) to bypass the browser's own
HTTP cache when taking the verification screenshot.

## 7. JS data files that are not strict JSON

A JS-array data file with bare object keys and trailing commas (e.g.
`window.TRAVEL_CITIES = [{ cc:'AR', name:'Córdoba', ..., },]`) is valid JS but NOT
valid JSON. To load it from Python, quote the keys and strip the trailing comma:

```python
arr = re.sub(r"([A-Za-z_]\w*):", r'"\1":', arr)      # quote bare keys
arr = re.sub(r",\s*]", "]", arr)                       # drop trailing comma before ]
```

## 8. Theme toggle: don't swap the basemap style

`map.setStyle()` then re-creating layers from `style.load` is unreliable in this
MapLibre build (it loses layers). Keep the basemap fixed (CARTO Voyager) and theme
only the chrome (header/sidebar), re-adding custom layers on the guaranteed `load`
event. See the main SKILL.md "setStyle" pitfall.

# Travel-map click fix (case study)

Context: `dmpotekhin.github.io/travel.html` — maplibre-gl 4.7.1, CARTO Voyager style. Layers:
- `visited-fill` / `visited-border` — country polygons (GeoJSON source)
- `clusters` (circle) + `cluster-count` (symbol) — clustered city points (source `cities`, `cluster:true, clusterMaxZoom:5, clusterRadius:36`)
- `hearts` (symbol, icon 'heart') — all cities always visible (source `cities_flat`, unclustered)

## Symptom
Clicking a heart opened "N городов" (the whole country's aggregate) instead of that one city. Also, clicking a cluster did nothing (no expansion), so cities couldn't be reached when zooming.

## Root cause (confirmed, not guessed)
At a heart's pixel, `map.queryRenderedFeatures(pt).map(f => f.layer.id)` returned:
`['hearts','hearts','hearts','hearts','visited-fill']`
So the `hearts` click handler AND the `visited-fill` click handler BOTH fired; the fill popup rendered last and won.

Separately, `map.getSource('cities').getClusterExpansionZoom(id, cb)` never called `cb` across multiple tries (a window var stayed `null` after ~1.5s, no error thrown). That is why clusters never expanded.

## Fix (replaced 3 per-layer click handlers with one priority dispatch)
```js
function openCountryPopup(props, lngLat) {
  var cc = props && props.ISO_A2 ? props.ISO_A2 : '';
  var list = cities.filter(function (c) { return c.cc === cc; });
  var html = '<div class="travel-popup"><div class="popup-city">' + (props && (props.NAME || cc)) + '</div>' +
    '<div class="popup-country">' + (list.length ? '📍 ' + list.length + ' ' + (list.length === 1 ? 'город' : 'городов') : '') + '</div></div>';
  new maplibregl.Popup().setLngLat(lngLat).setHTML(html).addTo(map);
}
map.on('click', function (e) {
  var pt = e.point;
  var cluster = map.queryRenderedFeatures(pt, { layers: ['clusters'] });
  if (cluster.length) { map.easeTo({ center: cluster[0].geometry.coordinates, zoom: 6 }); return; } // 6 = clusterMaxZoom(5)+1; getClusterExpansionZoom unreliable
  var heart = map.queryRenderedFeatures(pt, { layers: ['hearts'] });
  if (heart.length) { openPopup(heart[0].properties, heart[0].geometry.coordinates); return; }
  var fill = map.queryRenderedFeatures(pt, { layers: ['visited-fill'] });
  if (fill.length) { openCountryPopup(fill[0].properties, e.lngLat); }
});
```
Note: keep the `mouseenter`/`mouseleave` cursor handlers on `hearts` as-is (cursor only).

## Verification
- Heart click -> popup text became the single city ("Агинское / Россия"), not a count.
- Cluster click -> zoom moved to 6, no country popup.
- Hearts render at all zooms (Europe zoom 6 -> 7 hearts; Moscow zoom 8 -> 1); over the ocean it is legitimately 0.
- Confirm the exact popup that opened with `document.querySelector('.maplibregl-popup').textContent`.

## Related note (different class: data pipeline)
The travel-data generator produced data from `города.xlsx` and was delta-only (only ADDS, never removes). Removing a city from the xlsx left the stale city in generated data. Fix: a reconcile step that drops cities/geojson polygons not present in the wanted set, with a `SKIP_TYPOS` map to preserve typo-corrected names. Keep this in mind when auto-generated data won't shrink.

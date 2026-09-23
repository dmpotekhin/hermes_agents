# MapLibre click / cluster / cache recipes

Copy-paste building blocks. Verified on maplibre-gl@4.7.1 in a marker/cluster travel map.

## 1. One click handler with layer priority (fixes "click opens the wrong popup")

Problem: you have three separate layer click handlers
`map.on('click','hearts',...)`, `map.on('click','clusters',...)`,
`map.on('click','visited-fill',...)`. A heart sitting over a country fill triggers BOTH the
hearts handler and the fill handler, so the country "(N городов)" popup replaces the city popup.
MapLibre fires each layer-bound handler independently — they don't cancel each other.

Fix: a single handler that picks the topmost meaningful layer at the click point.

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
  // 1) cluster -> expand to reveal the cities inside it (do NOT rely on getClusterExpansionZoom)
  var cluster = map.queryRenderedFeatures(pt, { layers: ['clusters'] });
  if (cluster.length) { map.easeTo({ center: cluster[0].geometry.coordinates, zoom: 6 }); return; }
  // 2) single heart/pin -> city popup
  var heart = map.queryRenderedFeatures(pt, { layers: ['hearts'] });
  if (heart.length) { openPopup(heart[0].properties, heart[0].geometry.coordinates); return; }
  // 3) bare country fill -> aggregate count
  var fill = map.queryRenderedFeatures(pt, { layers: ['visited-fill'] });
  if (fill.length) { openCountryPopup(fill[0].properties, e.lngLat); }
});
```

Keep `map.on('mouseenter'/'mouseleave','hearts', ...)` for the pointer cursor — that's separate.

## 2. Cluster expansion that actually works

`map.getSource('cities').getClusterExpansionZoom(cluster_id, cb)` did NOT fire its callback
on maplibre-gl@4.7.1 (source loaded=true, cluster_id valid, callback stayed pending for seconds).
Any code inside that callback silently never runs. Use a fixed zoom just past `clusterMaxZoom`:

```js
// clusterMaxZoom = 5, so zoom 6 renders every city as an individual pin
if (cluster.length) map.easeTo({ center: cluster[0].geometry.coordinates, zoom: 6 });
```

If you keep the expansion-zoom call, surround it so the failure can't block navigation:
```js
map.easeTo({ center: cluster[0].geometry.coordinates, zoom: 6 }); // always lands on cities
```

## 3. Playwright MCP: force a non-cached reload when the page looks stale

The Playwright/MCP browser uses a persistent context that caches js/css across navigations —
even after `browser_close` (which only closes the tab, not the context). You can see an old
city count or old behaviour after editing files. Two fixes:

(a) Trust the server first — confirm what is actually served:
```bash
curl -s http://localhost:PORT/js/travel.js | grep -c "__map"   # if 0, your edit isn't served
```

(b) Hard-reload in the browser via CDP (in `mcp__playwright__browser_run_code_unsafe`):
```js
async (page) => {
  const client = await page.context().newCDPSession(page);
  await client.send('Network.setCacheDisabled', { cacheDisabled: true });
  await client.send('Network.clearBrowserCache');
  await page.goto('http://localhost:PORT/travel.html?v=1', { waitUntil: 'networkidle' });
  return await page.evaluate('!!window.__map');
}
```

## 4. Probing the live map to confirm behaviour (instead of trusting screenshots)

Temporarily expose the map (`window.__map = map;` — remove before ship), then read layer state
and which layer is on top at a marker:

```js
const m = window.__map;
const layers = {};
['visited-fill','clusters','hearts'].forEach(id => {
  const l = m.getLayer(id);
  layers[id] = l ? (l.layout.visibility || 'visible') : 'MISSING';
});
// which layers overlap at a heart's pixel (a heart over a fill => BOTH, the bug)
const f = m.querySourceFeatures('cities_flat')[0];
const pt = m.project(f.geometry.coordinates);
const hitLayers = m.queryRenderedFeatures(pt).map(x => x.layer.id);
// zoom-in rendering check
m.zoomTo(6, {duration:100}); await new Promise(r=>setTimeout(r,1500));
const hearts = m.queryRenderedFeatures({layers:['hearts']}).length;
```

Notes:
- `map.getSource(id)` exposes `loaded()`, `_data` (GeoJSON), and cluster props; `cluster` /
  `clusterMaxZoom` are NOT readable on the source object (they're internal).
- "no hearts at high zoom" often means the map centered over empty ocean after a world
  `fitBounds`; probe by flying to a known city, not by trusting an arbitrary zoom-9 centre.
- `queryRenderedFeatures(pt,{layers:[...]})` is how you decide the topmost interactive layer.

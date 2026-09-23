---
name: maplibre-interactive-map
description: "Use when debugging MapLibre maps: clicks, clusters, popups."
version: 1
author: hermes-curator
license: MIT
---

# MapLibre Interactive Map

Patterns and pitfalls for MapLibre GL JS maps that combine clustered markers, area fills, and popups (e.g. a travel map with city "hearts", visited-country fills, and cluster circles). Learned on dmpotekhin.github.io/travel.html, maplibre-gl 4.7.1.

## When to use
- Adding or debugging clickable markers, clusters, or area fills.
- Popups show the wrong thing on click; clusters won't expand; markers seem missing at some zooms.
- Considering globe or terrain projection.

## Core pattern: ONE click handler with layer priority
Binding separate `map.on('click', layerId)` handlers for a marker layer AND a fill layer underneath is a trap: a click on a marker sitting on the fill fires BOTH handlers, and the last one (fill) wins — you get the aggregate popup instead of the specific marker.

Fix: bind one `map.on('click', function (e) {...})` and dispatch by priority using `map.queryRenderedFeatures(e.point, {layers:[...]})`:
1. cluster -> expand
2. marker/heart -> its own popup
3. bare area fill -> aggregate popup
Return after the highest-priority match, and put cluster BEFORE marker so clicking a cluster circle reveals cities rather than the marker underneath.

## getClusterExpansionZoom may never call its callback
In some builds `map.getSource('s').getClusterExpansionZoom(id, cb)` never fires `cb` (verified: a window var stayed null after ~1.5s; no error thrown). Don't rely on it. Reliable fallback: zoom just past the cluster threshold:
```
var cluster = map.queryRenderedFeatures(e.point, {layers:['clusters']});
if (cluster.length) map.easeTo({ center: cluster[0].geometry.coordinates, zoom: CLUSTER_MAX_ZOOM + 1 });
```
(e.g. clusterMaxZoom 5 -> zoom 6). At that zoom every city renders as an individual marker.

## Diagnose interactions without guessing
```
var pt = map.project(coord);
var hit = map.queryRenderedFeatures(pt).map(f => f.layer.id); // e.g. ['hearts','hearts','visited-fill']
```
If both a marker and the fill appear at the same pixel, you have the overlap bug (see Core pattern).

## Globe / terrain projection — version gate
- 3D globe (`map.setProjection('globe')`) was added in MapLibre GL JS **5.0.0**. In 4.7.1 `setProjection`/`getProjection` are undefined; only `setTerrain`/`setSky` exist.
- Terrain (`setTerrain` + raster-dem) works in 4.7.1; free AWS elevation tiles: `https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png` with `encoding:'terrarium'`.
- To use globe you must upgrade to maplibre-gl >= 5. Globe + terrain both supported there.
- Pitfall: a world-wide fitBounds can center the map over the ocean, so scroll-zoom shows water. Navigate via click (marker/cluster) to reach land.

## Testing these maps
- Temporarily expose the map for tests: `window.__map = map;` in init; remove before shipping.
- Inspect state via `window.__map.queryRenderedFeatures` / `getZoom` / `getSource`.
- Popups are DOM: `document.querySelector('.maplibregl-popup').textContent` to assert what opened.
- A marker query returning 0 over the ocean is correct, not a bug — always check you're over land with cities.

## References
- `references/travel-map-click-fix.md` — exact reproduction, the one-click-handler code, and verification for the travel-map case.

---
name: maplibre-web-maps
description: Use when building or fixing MapLibre web map features.
version: 1
author: hermes-developer
license: MIT
---

# MapLibre Web Maps

Class-level guidance for building and debugging interactive maps with MapLibre GL JS —
especially maps that show many city/POI markers, cluster them at low zoom, and open popups
on click. Covers both the happy path and the pitfalls that silently break marker maps.

## When to use
- You are adding markers/hearts/pins, clustering, popups, or click handlers to a maplibre-gl map.
- A map interaction misbehaves (click opens the wrong thing, clusters don't expand, markers vanish
  on zoom, popup shows an aggregate instead of the item you clicked).
- A marker/popup build on a GitHub Pages or Vite/React site.

## Recommended structure (markers up to a few hundred points)
Use TWO sources so you can cluster in one view and still show every individual pin:
- `cities` GeoJSON source with `cluster:true, clusterMaxZoom:N, clusterRadius:R`.
  Backs the `clusters` (circle, `filter:['has','point_count']`) and `cluster-count` layers.
- `cities_flat` GeoJSON source (same data, NO clustering). Backs a `hearts`/`pins` symbol
  layer (`icon-allow-overlap:true, icon-ignore-placement:true`) that is ALWAYS visible.
  This is what makes individual pins render at any zoom.

Layers are added once in `map.on('load', addLayers)`. Keep markers on one basemap (CARTO
Voyager is reliable; openfreemap tiles/sprites/fonts are flaky). A single text-font stack
(e.g. `'Open Sans Regular'`) avoids the "two fonts -> one id -> 404" problem.

## Pitfalls
- **Overlapping layer click handlers BOTH fire.** If a heart sits over a country/polygon fill,
  clicking it triggers BOTH the hearts handler AND the fill handler, and the fill popup (e.g.
  "N городов") replaces the one you wanted. Fix: ONE `map.on('click')` handler that prioritises
  `map.queryRenderedFeatures(e.point,{layers:[...]})` in visual/importance order
  (cluster > pin > fill). Recipe: `references/click-and-cluster-recipes.md`.
- **`getClusterExpansionZoom()` may never fire its callback.** Observed on maplibre-gl@4.7.1:
  source loaded, valid `cluster_id`, but the callback stays pending (no error, no zoom). Don't
  make expansion depend on it. Expand a cluster by `map.easeTo({center, zoom: <just past
  clusterMaxZoom>})` (e.g. zoom 6 when clusterMaxZoom is 5) so every city in the cluster renders
  as an individual pin. If you must use it, keep a "zoom > clusterMaxZoom" fallback outside the
  callback (the callback never running is the failure mode).
- **Globe vs terrain: version matters.** `map.setProjection({type:'globe'})` (3D globe) requires
  MapLibre v5+ (globe shipped in 5.0.0); v4.x has no `setProjection`. Terrain works in v4
  (`setTerrain` + raster-dem, e.g. AWS terrarium). Check the installed version before promising
  a globe.
- **Don't hand-edit generated data.** If markers come from a build step (xlsx -> JS), treat the
  source file as the only truth and regenerate; never hand-edit the generated JS/geojson.
  Pipeline must also be able to REMOVE entries (not only add) or your removals never stick.
- **Playwright MCP browser cache can fool you.** The persistent context caches js/css across
  navigations — even after `browser_close` (which only closes the tab, not the context). A stale
  file can show an old count/behaviour. Trust the server: `curl` the file to confirm what is
  served, or force a hard reload with CDP `Network.setCacheDisabled` + `Network.clearBrowserCache`,
  or fetch with `{cache:'no-store'}`. Recipe: `references/click-and-cluster-recipes.md`.
- **Verifying a map in the browser.** Don't rely purely on screenshots; programmatically probe
  the map: temporarily expose `window.__map = map;` (remove before ship), then in Playwright read
  layer visibility, `queryRenderedFeatures` at a projected marker pixel, and `querySourceFeatures`.
  Use `queryRenderedFeatures(pt,{layers:[...]})` to pick which layer is on top at a click point.

## References
- `references/click-and-cluster-recipes.md` — copy-paste recipes: the single click-handler with
  layer priority, the reliable cluster-expansion zoom, the Playwright cache-bypass reload, and the
  map-probe snippet. Reuse these rather than re-deriving them.

---
name: static-map-visualization
description: "Static map page from place data: geocode, markers, popups."
---

# Static Map Visualization (MapLibre GL, no API key)

Build a self-contained interactive map page from a list of places (cities/stays):
point markers, a filled highlight of visited regions/countries, popups, clustering,
a searchable sidebar, deployed as a single static page on GitHub Pages. No backend,
no API keys — free vector styles + client-side GeoJSON.

The hard part is NOT the map library — it is turning messy place data into correct
coordinates (geocoding), then QA-ing that geocoding. Everything else is a data-prep
pipeline plus a MapLibre page.

## Pipeline overview

1. Read the source list (xlsx/CSV). `.xlsx` parses with stdlib `zipfile` + `xml.etree`
   with NS `{'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}` and
   `data_only=True` values — no openpyxl dependency needed.
2. Geocode each entry to lat/lon. Use Nominatim (OpenStreetMap) — free, no key. See
   `references/geocoder-and-maplibre-notes.md` for the recipe and the QA trap list.
3. QA every result (see Pitfall 1) — this is the step that matters most.
4. Emit a JS data file (e.g. `window.TRAVEL_CITIES = [ ... ]`) for the points, and a
   GeoJSON of region/country polygons for the highlight fill.
5. Build the page: MapLibre GL + a free vector style; a symbol layer for markers
   (heart icon via `addImage`), a `cluster` source for low-zoom counts, a fill+line
   layer for the country highlight, popups on click. Add a sidebar with stats,
   search, and a country-grouped list.
6. Verify in a real browser (Pitfall 6), then commit + push; GitHub Pages picks it up
   in ~30-60s (verify with curl, retry).

## Critical pitfalls

- **Pitfall 1 — Geocoding wrong COUNTRY (biggest risk).** Nominatim with Russian
  names mis-matches often: «Лапас» -> a village in Russia (not La Paz, Bolivia),
  «Брест» -> Brest, France (not Brest, Belarus), «Сямень» -> North Korea (not Xiamen),
  «Чобе» -> Bosnia (not Chobe, Botswana), «Ха Лонг» -> Russia (not Ha Long, Vietnam),
  «Фурнаш» -> Brazil (not Furnas, Azores), «Кировск» -> Leningrad oblast (not Kirovsk,
  Murmansk), «Литисия» -> Ukraine (not Leticia, Colombia), «Ла киака» -> Georgia
  (not La Quiaca, Argentina). ALWAYS print name -> country -> lat/lon for every row and
  eyeball each one; pin the failures manually (lat/lon + country + cc keyed by query).
- **Pitfall 2 — Natural Earth ISO codes.** In admin_0 GeoJSON, multi-part countries
  (France) have `ISO_A2="-99"` and `ISO_A3="-99"`. Match countries by `ADM0_A3`
  instead, and derive the 2-letter code via a `cc -> ISO_A3` lookup (reverse it) —
  never read the raw `ISO_A2`/`ISO_A3` for matching.
- **Pitfall 3 — `setStyle()` wipes custom layers.** `map.setStyle(...)` removes ALL
  `addSource`/`addLayer` output, and MapLibre does NOT re-fire `'style.load'` or
  `'load'` after it (and `'idle'` can be unreliable). Swapping the basemap live on a
  theme toggle therefore breaks the map. Keep ONE stable style and add custom layers
  once on `map.on('load', addLayers)`.
- **Pitfall 4 — cluster-count multi-font stack 404s.** A `text-font: ['Noto Sans
  Regular','Open Sans Regular']` is joined into ONE font id and the glyph server
  returns 404. Use a single font name that the target style's glyph server actually
  serves (CARTO uses `Open Sans Regular`).
- **Pitfall 5 — `map.addImage` heart.** Render a colour emoji `❤️` to a canvas with
  `ctx.fillText`, then `map.addImage('heart', canvas.getImageData())` — a free,
  asset-less heart icon for a `symbol` layer.
- **Pitfall 6 — verify in a real browser.** Headless network can be flaky; open the
  page via a browser tool, screenshot, and `vision_analyze` it to confirm tiles,
  markers/clusters, country fill, and sidebar all render. A "blank/grey map" is
  usually a style/tile delivery failure (free providers can time out under load) —
  check the console for `ERR_*` on the tile host; switching to CARTO
  (`basemaps.cartocdn.com/gl/voyager-gl-style/style.json`, free, keyless) is a
  reliable default. On the real site a transient provider hiccup may not recur.
- **Pitfall 7 — deploy timing.** GitHub Pages can 404 for ~30-60s after push. Use a
  short retry loop on `curl -s -o /dev/null -w "%{http_code}" <url>` before treating
  a 404 as a deploy failure.

## Files

- `references/geocoder-and-maplibre-notes.md` — concrete session detail: the
  geocoding recipe (Nominatim + normalization + disk cache + manual pins), the
  wrong-country QA list, the working MapLibre style/CDN URLs, and the Natural Earth
  extraction approach.

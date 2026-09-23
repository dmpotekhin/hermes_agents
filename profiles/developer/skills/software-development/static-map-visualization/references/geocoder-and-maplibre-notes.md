# Geocoding + MapLibre session notes (travel-map build)

Concrete detail from building dmpotekhin.github.io/travel.html — a static
249-city / 46-country map from `/Users/dmitrypotekhin/Downloads/города.xlsx`,
using MapLibre GL (no API key), deployed to GitHub Pages.

## Reading a .xlsx without openpyxl

```python
import zipfile, xml.etree.ElementTree as ET
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(path) as z:
    root = ET.fromstring(z.read('xl/sharedStrings.xml'))
vals = [ ''.join(t.text or '' for t in si.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'))
         for si in root.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si') ]
# then map <c r="A1"><v>idx</v></c> cell refs -> vals[idx] for the column of interest
```
`read_file` on a .xlsx also auto-extracts text rows (handy for a quick eyeball), but a
python loop over the sheet is cleaner for bulk. No `openpyxl` needed.

## Nominatim geocoding recipe

- Endpoint: `https://nominatim.openstreetmap.org/search?format=jsonv2&limit=n&q=...`.
  Send a `User-Agent` header (Nominatim requires it) and keep to ~1 request/sec.
  Do it from a plain `urllib.request` — no SDK needed.
- Normalize messy names first: «Питер» -> «Санкт-Петербург», «Шеньчжень» -> «Шэньчжэнь»,
  «Калиниград» -> «Калининград», non-city items («Телецкое озеро», «Кижи»,
  «Кападокия», «Хибины») as-is (Nominatim handles many of them).
- Cache results on disk keyed by the normalized query string (e.g.
  `/tmp/travel_geo_cache.json`) so re-runs are cheap; also store the `q` you sent so
  manual overrides can key off it.
- Batch with a per-call item budget (e.g. ~90) to stay inside an execution timeout;
  keep a `PINS` dict of manual lat/lon + country + cc for anything unmatchable or
  mis-matched, keyed by the query.

## Wrong-country QA list (the real gotcha)

Print `name -> country -> lat/lon` for EVERY row and eyeball each. Found & fixed
(mis-match -> correct):
- Лапас -> Russia -> **La Paz, Bolivia**
- Брест -> France -> **Brest, Belarus**
- Сямень -> North Korea -> **Xiamen, China**
- Чобе -> Bosnia -> **Chobe, Botswana**
- Ха Лонг -> Russia -> **Ha Long, Vietnam**
- Фурнаш -> Brazil -> **Furnas, Azores, Portugal**
- Кировск -> Leningrad oblast -> **Kirovsk, Murmansk**
- Литисия -> Ukraine -> **Leticia, Colombia**
- Ла киака -> Georgia -> **La Quiaca, Argentina**
- Пуно -> (wrong) -> **Puno, Peru**

Also dedupe obvious transcription duplicates (e.g. «Хэдань» / «Хандань»). Keep a small
`FIX` dictionary keyed by the query to force a lat/lon + country + cc.

## Natural Earth country polygons

- Get admin_0 from `https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson`.
  Use 50m (`ne_50m_admin_0_countries.geojson`) if tiny countries (Vatican, Singapore)
  are missing from 110m.
- **France has `ISO_A2="-99"` and `ISO_A3="-99"`** in some versions. Match by
  `ADM0_A3` (stable 3-letter code), and derive the display 2-letter code from a
  `cc -> ISO_A3` map (reverse it) — do NOT read the raw `ISO_A2`/`ISO_A3` for matching.
- Match precisely by code (no substring matching on names — `"india"`/`"oman"`
  substrings produced false hits like IN -> British Indian Ocean Territory, OM ->
  Romania).
- Lighten the output: drop all properties except the cc and round coordinates to
  reduce size (589 KB for 46 countries is fine).

## Working MapLibre style / CDN URLs (free, keyless)

- CARTO Voyager (light): `https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json`
- CARTO Dark Matter: `https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json`
- OpenFreeMap Liberty: `https://tiles.openfreemap.org/styles/liberty` (can time out on
  tiles/sprites/glyphs under load in some headless Chromium — CARTO is the reliable default).

## Key MapLibre behaviours observed

- `map.on('load', addLayers)` is the reliable place to add sources+layers once. Neither
  `'load'` nor `'style.load'` re-fire after `setStyle()`; `'idle'` can be flaky. So DON'T
  swap the basemap live on a theme toggle — it silently drops all custom layers.
- Cluster-count `text-font` must be a single served font (CARTO: `Open Sans Regular`); a
  two-element stack is joined into one id and 404s, so the cluster layer renders nothing.
- Cluster `queryRenderedFeatures(...,{layers:['clusters']})` returns 0 both when layers
  are absent AND when the source hasn't loaded; a blank map + 0 clusters + `hasClusterIndex:false`
  on a correctly-clustered source usually means the tile/style host isn't serving → check
  console `ERR_*` and switch the style host.
- `map.addImage('heart', canvas.getImageData())` from a `canvas` filled with `fillText('❤️')`
  gives a free symbol icon (no asset file).

## Deploy + verification

- Static GitHub Pages: commit the HTML/CSS/JS/GeoJSON directly, push, wait ~30-60s, then
  retry-curl `https://<user>.github.io/<page>.html` until `200`.
- Verify rendering with a browser tool: navigate to the page, screenshot, `vision_analyze`
  the PNG to confirm tiles, markers/clusters, country fill and the sidebar all appear.
- Only stage files that belong to THIS feature; leave unrelated working-tree changes
  (your spreadsheet, source data) and pre-existing modifications out of the commit.

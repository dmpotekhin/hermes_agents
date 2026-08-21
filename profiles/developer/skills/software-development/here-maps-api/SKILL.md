---
name: here-maps-api
description: "HERE Maps API: geocode, route, decode flexible polylines."
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [here, geocoding, routing, maps, polyline, matrix, location, travel]
    category: software-development
---

# HERE Maps API

Location intelligence via HERE's developer APIs (free tier) for local apps:
geocoding, road routing with geometry, matrix distance/duration, and the
"flexible polyline" geometry encoding HERE uses.

## When to use

- Geocoding a place name to lat/lon with a real API (better address coverage
  than Nominatim, but needs a key).
- Real road/rail distances, durations, or route geometry for travel/map apps.
- Decoding a HERE "flexible polyline" string (from Routing/Map APIs) into
  coordinates.

## Auth

Free-tier key at https://developer.here.com/. Pass it as a **query param**
`apiKey=<key>` on every request — NOT a header or bearer token. Store in
`.env`, never hardcode. App should degrade gracefully when the key is absent
(see fallback pattern below).

## Endpoints

| Purpose | URL | Notes |
|---|---|---|
| Geocoding | `https://geocode.search.hereapi.com/v1/geocode` | GET, params `q`, `apiKey`, `limit`. Response: `items[0].position.{lat,lng}` |
| Routing v8 | `https://router.hereapi.com/v8/routes` | GET, params `transportMode`, `origin=lat,lng`, `destination=lat,lng`, `return=polyline,summary`, `apiKey`. Response: `routes[0].sections[0].polyline` (flexible) + `.summary.length` (m) + `.summary.duration` (s) |
| Matrix v8 | `https://matrix.router.hereapi.com/v8/matrix` | GET, params `origin`, `destination`, `routingMode=fast`, `transportMode`, `apiKey`. Response: `matrix[0][0].summary.{length,duration}` — distance/duration ONLY, **no geometry** |

## transportMode mapping

| App type | HERE `transportMode` |
|---|---|
| car | `car` |
| bus | `bus` |
| bike | `bicycle` |
| foot | `pedestrian` |

`rail`, `air`, and `ferry` are **not supported** by Routing v8 (no rail/airline
geometry). For those, fall back to great-circle (haversine) distance + geodesic
arc, or use Matrix in `car` mode if you only need a distance estimate.

## Flexible polyline decoder

HERE returns geometry as a "flexible polyline" (compact 6-bit base64-ish
string). Decode it with the function below (2D only — skips the optional third
dimension). Returns `[lng, lat]` pairs in GeoJSON order.

Verified against the official heremaps/flexible-polyline test vector:
`"BFoz5xJ67i1B1B7PzIhaxL7Y"` decodes to
`(50.1022829, 8.6982122), (50.1020076, 8.6956695), (50.1006313, 8.6914960),
(50.0987800, 8.6875156)`.

```python
FORMAT_VERSION = 1

# maps (ord(char) - 45) -> 6-bit value; -1 = invalid char
_DECODING_TABLE = [
    62, -1, -1, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, -1, -1, -1, -1, -1, -1, -1,
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21,
    22, 23, 24, 25, -1, -1, -1, -1, 63, -1, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35,
    36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51,
]

def _decode_char(char):
    value = _DECODING_TABLE[ord(char) - 45]
    if value < 0:
        raise ValueError("Invalid encoding")
    return value

def _to_signed(value):
    if value & 1:
        value = ~value
    value >>= 1
    return value

def _decode_unsigned_values(encoded):
    result = shift = 0
    for char in encoded:
        value = _decode_char(char)
        result |= (value & 0x1F) << shift
        if (value & 0x20) == 0:
            yield result
            result = shift = 0
        else:
            shift += 5
    if shift > 0:
        raise ValueError("Invalid encoding")

def decode_polyline(encoded):
    last_lat = last_lng = 0
    decoder = _decode_unsigned_values(encoded)
    version = next(decoder)
    if version != FORMAT_VERSION:
        raise ValueError("Invalid format version")
    value = next(decoder)
    precision = value & 15
    value >>= 4
    third_dim = value & 7
    factor = 10.0 ** precision
    coords = []
    while True:
        try:
            last_lat += _to_signed(next(decoder))
        except StopIteration:
            break
        try:
            last_lng += _to_signed(next(decoder))
        except StopIteration:
            raise ValueError("Invalid encoding. Premature ending reached")
        if third_dim:
            next(decoder)  # skip z component
        coords.append([last_lng / factor, last_lat / factor])
    return coords
```

## Encoding pitfalls (writing your own encoder / test vectors)

When generating polyline test vectors with a throwaway encoder, two bugs bit us:

1. **The alphabet is NOT `chr(value + 45)`.** Flexible polyline maps 6-bit values
   through `"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"`
   (`value → alphabet[value]`). `chr(value+45)` produces chars like `2` that the
   decoding table marks INVALID.
2. **The header is TWO unsigned values, not one.** First emit the version (`1`),
   THEN `precision | (third_dim << 4) | (third_dim_precision << 7)`. Emitting
   only the precision gives "Invalid format version".

Encoding recipe (delta-encoded, precision 5, no third dim):
- signed: `n = v << 1; if n < 0: n = ~n`
- 5-bit chunks low-bits-first: `while n >= 0x20: emit(alphabet[0x20 | (n & 0x1F)]); n >>= 5`, then `emit(alphabet[n])`
- header: `emit(alphabet[1]); emit(alphabet[5])`
- per point: lat delta, lng delta (input coords `[lng, lat]` in GeoJSON order)

`scripts/encode_polyline_vectors.py` has working flexible AND Google encoders —
use it to mint test-vector constants or cross-check a decoder round-trip.

## Google polyline (OSRM) ≠ flexible polyline (HERE)

OSRM returns Google polyline (alphabet = `chr(63..126)`, i.e. `?@A...~`,
`ord(char) - 63`); HERE returns flexible. Do NOT reuse one decoder for both: a
Google decoder written with flexible-style bit accumulation produced NEGATIVE
lat/lon (the tell: coordinates negative where positive expected). Both formats
OR-accumulate 5-bit chunks from 0 (`result |= (b & 0x1F) << shift`) and unpack
sign identically (`~(v>>1)` if odd else `v>>1`); they differ in alphabet, header
(flexible has version+precision, Google none) and precision. Always cross-check
a decoder against an INDEPENDENT encoder or an official test vector.

## Fallback-by-default pattern

When `HERE_API_KEY` is unset, degrade to a keyless path so the app still works:

1. **Geocoding**: Nominatim `https://nominatim.openstreetmap.org/search` with
   params `q`, `format=json`, `limit=1` and a `User-Agent` header. Throttle to
   ~1 req/s. Cache results in-memory. A small built-in dict of common cities
   makes demos work offline and instantly.
2. **Distance**: haversine (great-circle). For air segments this is the only
   sane option anyway.
3. **Geometry**: geodesic great-circle interpolation (slerp) into ~64 points for
   smooth map lines.

## Pitfalls

- `apiKey` is a query param, not a header.
- Matrix v8 has no geometry — use Routing v8 when you need a polyline.
- Nominatim requires a `User-Agent` header and ~1 req/s courtesy limit.
- The flexible-polyline first byte encodes the version (must be `1`) plus a
  header-continuation count; the second value packs precision + third-dimension
  flags. Don't strip the header before decoding.
- `summary.length` is meters, `summary.duration` is seconds — divide by 1000/60
  for km/min.

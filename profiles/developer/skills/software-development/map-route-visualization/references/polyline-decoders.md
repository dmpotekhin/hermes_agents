# Polyline decoders across routing providers (Google vs HERE flexible)

Routing APIs return geometry in TWO incompatible polyline encodings. Pick the
decoder per provider — mixing them silently produces wrong (often lat/lon
swapped or sign-flipped) coordinates, e.g. Moscow rendered as -Moscow.

| Provider | Encoding |
|---|---|
| HERE Routing v8 / Matrix v8 | HERE **flexible polyline** (header char encodes version+precision) |
| OSRM (`/route/v1/{profile}`) | **Google polyline5** (precision 5 = 1e5) |
| GraphHopper (`/route` ?point=...) | **Google polyline5** |

## One-line memory rule (bit us in T3)

- **Google polyline5**: accumulator starts at **0**, bits are **OR-ed in**
  (`acc |= chunk << shift`) with an explicit shift counter.
- **HERE flexible polyline**: accumulator starts at **1**, chunks are
  **added** (`acc += chunk`) with a running shift.
Implementing one style with the other's accumulation gives garbage; that's
exactly what produced `[[-37.61731, -55.75581], ...]` instead of Moscow when a
Google decoder was first written flexible-style.

## Google polyline5 decode (Python, stdlib only)

```python
_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
_LOOKUP = {c: i for i, c in enumerate(_ALPHABET)}

def decode_google_polyline(enc, precision=5):
    coords, lat, lng, i = [], 0, 0, 0
    scale = 10 ** precision
    while i < len(enc):
        lat += _decode_value(enc, lambda a, v, s: a | (v << s), i)[0]  # OR style
        # full impl: read 5-bit chunks while 0x20 set, OR into acc, then zigzag
        ...
```

(Full working implementation lives in `backend/routing/osrm.py` of the
reference project — copy from there. The zigzag sign handling is
`(acc >> 1) if acc & 1 else -(acc >> 1)`.)

## Known test vectors (verify decoders with these)

- HERE flexible: `BF45p0KkkzlH8GwHsT8nC` ↔
  `[[37.6173, 55.7558], [37.6185, 55.7569], [37.63, 55.76]]`
- Google polyline5 (OSRM): `wxhsIccrdF{EoFkR{fA` (Moscow area)

## OSRM + GraphHopper integration facts

- OSRM: `GET {OSRM_BASE_URL}/route/v1/{profile}?coordinates={lon,lat};{lon,lat}&overview=full&geometries=polyline`
  Profiles: `driving` (car/bus/ferry), `cycling` (bike), `walking` (foot).
  air/rail → raise `UnsupportedTransportError` (no honest fallback inside the
  provider; the chain moves on to great-circle).
- GraphHopper: `GET {GRAPHHOPPER_BASE_URL}/route?point={lat},{lon}&point={lat},{lon}&profile={car|bike|foot}&key={API_KEY}`
  Profiles: `car` (car/bus/ferry), `bike`, `foot`; air/rail → unsupported.
- **Every provider must wrap network/HTTP/parse failures into
  `ProviderUnavailableError`** (or the shared hierarchy) — a raw `httpx` error
  escapes the chain's `except RoutingError` and kills the whole fallback chain
  instead of falling through (this bit us for both OSRM and GraphHopper in T4).
- Both APIs return `routes[0].distance` (meters) / `duration` (seconds) — no
  need for matrix fallback like HERE.
- Public demo servers (router.project-osrm.org, graphhopper.com) have no SLA —
  document self-hosting for production.

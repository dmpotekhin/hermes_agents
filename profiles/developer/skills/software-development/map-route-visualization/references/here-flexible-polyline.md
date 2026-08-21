# HERE Flexible Polyline — decoder (2D)

HERE Routing v8 returns route geometry as a `polyline` string in **flexible
polyline** encoding (https://github.com/heremaps/flexible-polyline). It is NOT
Google's polyline. Here is a minimal, tested 2D decoder (3rd dimension skipped).

## Decoding table

Maps `ord(char) - 45` → 6-bit value. `-1` = invalid char. Copy verbatim:

```python
_DECODING_TABLE = [
    62, -1, -1, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, -1, -1, -1, -1, -1, -1, -1,
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21,
    22, 23, 24, 25, -1, -1, -1, -1, 63, -1, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35,
    36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51,
]
```

## Algorithm

1. Iterate chars → 6-bit values. Each value: lower 5 bits are payload, bit 0x20
   (`value & 0x20`) set means "more 5-bit groups follow" (little-endian,
   `shift += 5`). A cleared 0x20 terminates the unsigned varint.
2. First unsigned varint = version (must be 1).
3. Second = header byte: `precision = v & 15`, `v >>= 4`, `third_dim = v & 7`,
   `third_dim_precision = (v >> 3) & 15`.
4. Then read pairs (lat, lng) of signed deltas, accumulating onto running totals.
   Signed decode `to_signed(v)`: if `v & 1` then `v = ~v`; then `v >>= 1`.
5. Divide accumulated values by `10.0 ** precision`. If `third_dim`, consume one
   more delta per pair (skip it for 2D).

```python
def _decode_char(c):
    v = _DECODING_TABLE[ord(c) - 45]
    if v < 0:
        raise ValueError("invalid char")
    return v

def _unsigned(encoded):
    result = shift = 0
    for c in encoded:
        v = _decode_char(c)
        result |= (v & 0x1F) << shift
        if v & 0x20:
            shift += 5
        else:
            yield result
            result = shift = 0
    if shift:
        raise ValueError("invalid encoding")

def _to_signed(v):
    if v & 1:
        v = ~v
    return v >> 1

def decode_polyline(encoded):
    last_lat = last_lng = 0
    values = _unsigned(encoded)
    version = next(values)
    if version != 1:
        raise ValueError("bad version")
    v = next(values)
    precision = v & 15
    v >>= 4
    third_dim = v & 7
    factor = 10.0 ** precision
    coords = []
    while True:
        try:
            last_lat += _to_signed(next(values))
        except StopIteration:
            break
        try:
            last_lng += _to_signed(next(values))
        except StopIteration:
            raise ValueError("truncated")
        if third_dim:
            next(values)  # skip z
        coords.append([last_lng / factor, last_lat / factor])  # [lng, lat]
    return coords
```

## Known test vector (verify your implementation)

```
encoded = "BFoz5xJ67i1B1B7PzIhaxL7Y"
decoded (lat, lng):
  (50.1022829, 8.6982122)
  (50.1020076, 8.6956695)
  (50.1006313, 8.6914960)
  (50.0987800, 8.6875156)
```
(decoder returns `[lng, lat]` order.)

## Usage in HERE Routing v8

`GET /v8/routes?return=polyline,summary` → `routes[0].sections[0]`:
- `summary.length` (meters), `summary.duration` (seconds) — use directly for
  distance/time even if you skip geometry.
- `sections[0].polyline` — decode for real road geometry.

If decode fails (e.g. a 3rd-dimension edge case), fall back to great-circle
geometry but KEEP the HERE `summary` distance — the numbers stay accurate, only
the line shape degrades to straight.

# Hard-won Python lessons in travel-blog-app

These are durable, environment-independent gotchas hit while building this project.
Each is reproducible; they are NOT "tool X is broken" claims.

## 1. aiosqlite tests hang on shutdown if the connection isn't closed

**Symptom:** a pytest / asyncio script that hits an `assert` failure (or any early
return) before `await db.close()` runs exits fine on main() but the process hangs at
the very end — the shell reports "Command timed out after Ns" even though the traceback
prints. Exit code looks like a timeout (124), not the assertion error.

**Root cause:** aiosqlite runs one worker thread per connection. If the connection is
never closed, `asyncio.run()` waits forever for that thread while tearing down the
loop, so the process never terminates.

**Fix:** always close in a `finally`:

```python
db = Database(str(tmp / "t.db"))
await db.connect()
try:
    ... assertions ...
finally:
    await db.close()
```

For pytest, use a fixture that yields and closes in `finally`:

```python
@pytest.fixture
async def db_and_queue():
    ...
    await db.connect()
    try:
        yield db, queue
    finally:
        await db.close()
```

**Why it matters:** a failed assertion silently looks like a generic timeout, which
misleads you into chasing the wrong thing. Always wrap async DB tests in try/finally.

## 2. A mutable stats dict on a service object leaks across calls

**Symptom:** the same `Scanner.scan()` reported different aggregate `new`/`folders`
counts between calls that should be identical (e.g. second incremental run showed
`new: 5` when it should be 0, and `folders: 6` when there were only 3).

**Root cause:** `self.stats` is initialized once in `__init__` and mutated with `+=`
inside `scan()`. A second `scan()` starts by inheriting the first call's counters and
adds on top, so the second run reports accumulated totals. The incremental "skip
unchanged" logic was actually correct; only the counter was wrong.

**Fix:** reset the dict at the start of every run method:

```python
async def scan(self, ...):
    self.stats = {"folders": 0, "total_files": 0, "new": 0, "updated": 0,
                  "skipped": 0, "failed": 0, "duplicate": 0, "missing": 0}
    ...
```

**Lesson:** any method on a long-lived service object that returns per-run counters
must re-initialize them at entry, not at construction.

## 3. EXIF + GPS via Pillow (replaces the abandoned `exifread`)

Read EXIF with `Image.getexif()`; GPS lives in IFD `0x8825`, decodes via `ExifTags.GPSTAGS`:

```python
from PIL import Image
from PIL.ExifTags import GPSTAGS

with Image.open(path) as im:
    exif = im.getexif()                       # top-level tags
    gps_ifd = exif.get_ifd(0x8825)            # GPS IFD
    gps = {GPSTAGS.get(k, k): v for k, v in gps_ifd.items()}
lat_ref, lon_ref = gps.get("GPSLatitudeRef"), gps.get("GPSLongitudeRef")
lat = _dms_to_decimal(gps["GPSLatitude"], lat_ref)    # DMS tuple -> signed decimal
lon = _dms_to_decimal(gps["GPSLongitude"], lon_ref)
```

- Prefer `DateTimeOriginal` (0x9003) over `DateTime` (0x0132) for capture time.
- Corrupted / non-image files: `PIL.Image.open` raises. Swallow it, set a `_valid =
  False` flag in the returned dict, and have the caller mark that row `failed` instead
  of treating it as a valid photo (so a bad file never silently enters the pipeline).
- `reverse_geocoder` needs a native build. It may be absent — design a folder-name /
  filename fallback for city detection so the pipeline runs either way (see
  `scanner.CityDetector`). Don't hard-fail when geocoding is unavailable.

## pytest-asyncio config

`pytest.ini` at project root:
```
[pytest]
asyncio_mode = auto
pythonpath = .
testpaths = tests
```
`asyncio_mode = auto` lets you write plain `async def test_*` without decorating every
test (or use `@pytest.mark.asyncio` explicitly). `pythonpath = .` makes `from core…`
/ `from modules…` resolve without an editable install.

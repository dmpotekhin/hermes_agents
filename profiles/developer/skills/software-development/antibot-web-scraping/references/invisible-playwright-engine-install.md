# invisible_playwright — install & engine seeding

Antidetect Playwright wrapper: C++-patched Firefox with deterministic
fingerprint profile (seeded), humanized cursor, 100% Playwright API
compatibility. Requires Python ≥3.11, playwright 1.55–1.61.

## Normal install

```bash
pip install --user invisible-playwright   # pulls invisible-core (pinned), maxminddb, etc.
```

First run of any `InvisiblePlaywright()` context downloads two things into
`~/Library/Caches/invisible-playwright/`:
1. GeoIP mmdb (~122 MB) under `geoip/<date>/` — from `daijro/geoip-all-in-one`
   GitHub releases (latest-tag permalink, never pinned).
2. The patched Firefox engine (~237 MB macOS) from
   `https://github.com/feder-cr/firefox_antidetect_patch/releases/download/{tag}/{asset}`.

Built-in downloader is `requests`-based with a 30-min wall deadline
(`INVISIBLE_DOWNLOAD_DEADLINE`) — on slow/trickle links it hangs for ~30 min
then dies with a deadline error; on a flaky link it can stall indefinitely
(the per-read timeout never trips when bytes trickle). Do NOT sit through that;
kill it and pre-seed the cache with curl (below).

## Engine metadata (read from the installed package)

Everything needed lives in `seal.json` inside the installed core:

```bash
cat ~/Library/Python/3.11/lib/python/site-packages/invisible_core/seal.json
```

Keys of interest: `tag` (e.g. `firefox-20`), `upstream_version` (`151.0`),
`assets` — per platform/arch with `sha256`, `size`, `build_id`,
`entry_rel` (`Firefox.app/Contents/MacOS/firefox` on darwin).

Cache dir name = `{tag}_{upstream_version}_{build_id}` under
`~/Library/Caches/invisible-playwright/`, so for the example above:
`firefox-20_151.0_20260817150639/`. The entry binary sits at
`<cache_dir>/Firefox.app/Contents/MacOS/firefox`.

## Robust engine seeding (slow/unstable network)

```bash
# 1. Download with resume + stall-abort + retry (use exact asset name from seal.json)
curl -L -C - --speed-limit 1024 --speed-time 60 --retry 10 --retry-all-errors \
  -o /tmp/firefox-151.0-stealth-macos-x86_64.tar.gz \
  "https://github.com/feder-cr/firefox_antidetect_patch/releases/download/firefox-20/firefox-151.0-stealth-macos-x86_64.tar.gz"

# 2. Verify sha256 against seal.json value
shasum -a 256 /tmp/firefox-151.0-stealth-macos-x86_64.tar.gz

# 3. Extract straight into the expected cache dir
mkdir -p ~/Library/Caches/invisible-playwright/firefox-20_151.0_20260817150639
tar -xzf /tmp/firefox-151.0-stealth-macos-x86_64.tar.gz \
  -C ~/Library/Caches/invisible-playwright/firefox-20_151.0_20260817150639

# 4. macOS hygiene (ad-hoc signed; exec'd directly so Gatekeeper prompt doesn't apply)
xattr -dr com.apple.quarantine ~/Library/Caches/invisible-playwright/firefox-20_151.0_20260817150639
chmod +x ~/Library/Caches/invisible-playwright/firefox-20_151.0_20260817150639/Firefox.app/Contents/MacOS/firefox

# 5. Verify the cache is accepted (no download on next run)
python3 -c "from invisible_core.download import engine_status; print(engine_status())"
```

Why this works: `ensure_binary()` checks `_adopt_existing_cache()` before
downloading — a tree already at the content-keyed dir whose entry passes
`verify_engine()` (application.ini / platform.ini / juggler markers, and the
sealed `omni.ja` sha256 on darwin) is adopted and stamped, no download.
A wrong sha256 in step 2 or a corrupted tree will be rejected by verification —
verify before extracting, and re-check with `engine_status()`.

## Usage

```python
from invisible_playwright import InvisiblePlaywright

with InvisiblePlaywright(seed=42, headless=True, locale="ru-RU") as browser:
    page = browser.new_page()          # note: patched new_page adds ~0.4s settle
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(8000)        # let price widgets render
    print(page.title())
    print(page.locator('[data-widget="webPrice"]').first.inner_text())
```

- `seed=` → deterministic fingerprint; `humanize=True` (default) → cursor
  travels along a seeded path instead of jumping.
- Engine runs headless fine (that is the point of the C++ patches); `headless=False`
  opens a visible window if a site needs it.

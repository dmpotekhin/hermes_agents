# invisible_playwright engine preload (slow network)

Session-verified 2026-08-19: macOS x86_64, Python 3.11.7, invisible-playwright 0.7.2 / invisible-core 20.15.0.

## Problem

`InvisiblePlaywright()` first launch auto-downloads the engine binary (~237 MB) from GitHub Releases via `requests`. On slow/flaky RU networks the connection can stall indefinitely: the per-socket timeout does not trip (data trickles), and the 30-min wall-clock deadline (`INVISIBLE_DOWNLOAD_DEADLINE`, default 1800 s) eventually kills the run with zero progress. The download goes to a temp dir, so a killed run leaves nothing reusable in the cache.

Symptoms of a stalled engine download:
- `lsof -p <pid> | grep ESTAB` shows one established socket to github.com, no growth
- `du -sh ~/Library/Caches/invisible-playwright` shows only the GeoIP mmdb, no version dir

## Fix: preload with curl + adopt

Everything about the engine is described by the installed package's seal:

```
~/Library/Python/3.11/lib/python/site-packages/invisible_core/seal.json
```

Key fields (example, tag firefox-20):

```json
{
  "assets": {
    "firefox-151.0-stealth-macos-x86_64.tar.gz": {
      "arch": "x86_64", "build_id": "20260817150639",
      "entry_rel": "Firefox.app/Contents/MacOS/firefox",
      "sha256": "390c43e08ab04c9f78e9bdfb6ec62c43f24e3f72a58b075244c7664e25e4c0f5",
      "size": 237005113, "platform": "darwin"
    }
  },
  "tag": "firefox-20", "upstream_version": "151.0"
}
```

Download URL template (constants.py): `https://github.com/feder-cr/firefox_antidetect_patch/releases/download/{tag}/{asset}`

Commands:

```bash
curl -L --retry 10 --retry-delay 5 --retry-all-errors -C - \
  --speed-limit 1024 --speed-time 60 \
  -o /tmp/firefox-151.0-stealth-macos-x86_64.tar.gz \
  "https://github.com/feder-cr/firefox_antidetect_patch/releases/download/firefox-20/firefox-151.0-stealth-macos-x86_64.tar.gz"

shasum -a 256 /tmp/firefox-151.0-stealth-macos-x86_64.tar.gz   # compare to seal.json

# cache dir is cache_root()/f"{tag}_{upstream_version}_{build_id}"
VDIR=~/Library/Caches/invisible-playwright/firefox-20_151.0_20260817150639
mkdir -p "$VDIR"
tar -xzf /tmp/firefox-151.0-stealth-macos-x86_64.tar.gz -C "$VDIR"
xattr -dr com.apple.quarantine "$VDIR"
chmod +x "$VDIR/Firefox.app/Contents/MacOS/firefox"
```

`ensure_binary` has an adopt path: if the version dir exists and the engine verifies (sha256/omni check), it writes the stamp and proceeds without downloading. Verified: the first scraper run after preload went straight to the browser (no download).

Also fetched on first launch (small, harmless): GeoIP mmdb from `daijro/geoip-all-in-one` → `~/Library/Caches/invisible-playwright/geoip-aio-all.mmdb`.

## Notes

- Engine cache persists — check `~/Library/Caches/invisible-playwright/` before re-downloading anything.
- The `requests` downloader in invisible-core has NO resume; curl with `-C -` does. For flaky networks curl is strictly better.

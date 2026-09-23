#!/usr/bin/env python3
"""Non-destructive verification of the travel map on GitHub Pages.

Checks (each prints PASS/FAIL; exits non-zero if any FAIL):
  1. js/travel-data.js is a valid window.TRAVEL_CITIES array with a city count,
     each city has numeric lon/lat in range, a name, a country and a 2-letter cc.
  2. data/visited_countries.geojson is a FeatureCollection with a country count,
     each feature has properties.iso_a2 (2-letter code).
  3. Consistency: distinct city cc set == geojson iso_a2 set (1:1).
  4. User-confirmed CHECK-city mappings hold (Кордоба -> AR, Картахена -> CO).
  5. travel.html references the required assets.
  6. index.html and books.html link to travel.html.

Usage:
  python3 travel_map_verify.py [repo_dir]
  repo_dir defaults to /Users/dmitrypotekhin/Downloads/dmpotekhin.github.io
"""
import json
import os
import re
import sys

REPO = sys.argv[1] if len(sys.argv) > 1 else "/Users/dmitrypotekhin/Downloads/dmpotekhin.github.io"
# Expected counts are derived from the auto-generated header comment in
# travel-data.js ("(255 cities / 50 countries)") so the script stays correct
# after any data refresh, instead of a hardcoded 249/46 that goes stale.
EXPECTED_CITIES = None
EXPECTED_COUNTRIES = None
# User-confirmed CHECK-city mappings (do not change without the user).
CONFIRMED = {"Кордоба": "AR", "Картахена": "CO"}

failures = []


def check(name, ok, detail=""):
    print(("[PASS] " if ok else "[FAIL] ") + name + (": " + detail if detail else ""))
    if not ok:
        failures.append(name)


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


# 1) cities
cities = []
try:
    src = read(os.path.join(REPO, "js", "travel-data.js"))
    # derive expected counts from the auto-generated header comment
    # e.g. "// Auto-generated: visited cities travel data (255 cities / 50 countries)"
    hdr = re.search(r"\((\d+)\s+cities\s*/\s*(\d+)\s+countries\)", src)
    if hdr:
        EXPECTED_CITIES = int(hdr.group(1))
        EXPECTED_COUNTRIES = int(hdr.group(2))
    m = re.search(r"window\.TRAVEL_CITIES\s*=\s*(\[.*\])\s*;", src, re.S)
    arr = m.group(1) if m else None
    # travel-data.js is JS object literals ({name:"...", lat:1.0}) not strict JSON ->
    # quote the bare keys, then parse as JSON.
    quoted = re.sub(r"([A-Za-z_]\w*):", r'"\1":', arr) if arr else "[]"
    quoted = re.sub(r",\s*]", "]", quoted)  # drop the trailing comma before "]"
    cities = json.loads(quoted)
except Exception as e:  # noqa: BLE001
    check("cities: parse travel-data.js", False, str(e))
else:
    check("cities: count == %d" % EXPECTED_CITIES, len(cities) == EXPECTED_CITIES, str(len(cities)))
    bad_coords = [
        c for c in cities
        if not (isinstance(c.get("lon"), (int, float)) and isinstance(c.get("lat"), (int, float))
                and -180 <= c["lon"] <= 180 and -90 <= c["lat"] <= 90)
    ]
    check("cities: all lon/lat numeric & in range", not bad_coords, "%d bad" % len(bad_coords))
    bad_cc = [c for c in cities if not re.fullmatch(r"[A-Za-z]{2}", str(c.get("cc", "")))]
    check("cities: all cc are 2-letter", not bad_cc, "%d bad" % len(bad_cc))
    missing = [c for c in cities if not c.get("name") or not c.get("country")]
    check("cities: all have name+country", not missing, "%d missing" % len(missing))
    for name, cc in CONFIRMED.items():
        found = [c for c in cities if c.get("name") == name]
        ok = bool(found) and all(str(c.get("cc", "")).upper() == cc for c in found)
        check("cities: confirmed %s -> %s" % (name, cc), ok, str([c.get("cc") for c in found]))

# 2) geojson
gj = None
try:
    gj = json.loads(read(os.path.join(REPO, "data", "visited_countries.geojson")))
except Exception as e:  # noqa: BLE001
    check("geojson: parse", False, str(e))

if gj is not None:
    check("geojson: FeatureCollection", gj.get("type") == "FeatureCollection")
    feats = gj.get("features", [])
    check("geojson: count == %d" % EXPECTED_COUNTRIES, len(feats) == EXPECTED_COUNTRIES, str(len(feats)))
    codes = [f.get("properties", {}).get("ISO_A2", "") for f in feats]
    check("geojson: all iso_a2 2-letter", all(re.fullmatch(r"[A-Za-z]{2}", str(c)) for c in codes), str(len(codes)))
    fills = [f.get("properties", {}).get("fillColor", "") for f in feats]
    check("geojson: all fillColor valid hex (#rrggbb)", all(re.fullmatch(r"#[0-9A-Fa-f]{6}", str(c)) for c in fills), "%d bad" % sum(1 for c in fills if not re.fullmatch(r"#[0-9A-Fa-f]{6}", str(c))))

    # 3) consistency
    city_cc = sorted({str(c["cc"]).upper() for c in cities})
    geo_cc = sorted({str(c).upper() for c in codes})
    check("consistency: distinct city cc == geojson iso_a2 (1:1)", city_cc == geo_cc,
          "cities=%d geo=%d" % (len(city_cc), len(geo_cc)))
    missing_countries = [c for c in codes if str(c).upper() not in city_cc]
    check("consistency: no geojson country absent from cities", not missing_countries, str(missing_countries))

# 5) travel.html assets
try:
    th = read(os.path.join(REPO, "travel.html"))
    for asset in ["js/main.js", "js/travel-data.js", "js/travel.js", "css/travel.css"]:
        check("travel.html references " + asset, asset in th)
except Exception as e:  # noqa: BLE001
    check("travel.html read", False, str(e))

# travel.js content smoke checks (flag-color fill + Google-style heart marker)
try:
    tj = read(os.path.join(REPO, "js", "travel.js"))
    check("travel.js has flag-color fill", "['get', 'fillColor']" in tj)
    check("travel.js has Google-style heart", "drawHeart" in tj)
    check("travel.js hearts always visible (cities_flat source)", "cities_flat" in tj)
    check("travel.js hearts layer un-clustered", "source: 'cities_flat'" in tj or "'source': 'cities_flat'" in tj)
except Exception as e:
    check("travel.js read", False, str(e))

# 6) nav links
for f in ["index.html", "books.html"]:
    try:
        h = read(os.path.join(REPO, f))
        check("%s links to travel.html" % f, 'href="travel.html"' in h)
    except Exception as e:  # noqa: BLE001
        check("%s read" % f, False, str(e))

print("\nRESULT: %d check(s) failed" % len(failures))
sys.exit(1 if failures else 0)

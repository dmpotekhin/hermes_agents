# Verify Books JS — run with: python3 scripts/verify-books.py
# Checks: JSON validity, brace balance, CDN reachability, note coverage

import json, re, os, urllib.request

BOOKS_JS = '/Users/dmitrypotekhin/Downloads/dmpotekhin.github.io/js/books-data.js'
NOTES_JS = '/Users/dmitrypotekhin/Downloads/dmpotekhin.github.io/js/notes-data.js'

errors = []

# 1. books-data.js — valid JSON array
with open(BOOKS_JS, 'r') as f:
    b = f.read()
try:
    arr = json.loads(b[b.index('['):b.rindex(']')+1])
    print(f"[PASS] books-data.js: {len(arr)} entries, valid JSON")
except Exception as e:
    errors.append(f"books-data.js JSON: {e}")
    print(f"[FAIL] books-data.js: {e}")

# 2. No duplicate titles
titles = [e['title'] for e in arr]
dupes = {t: titles.count(t) for t in set(titles) if titles.count(t) > 1}
if dupes:
    print(f"[WARN] books-data.js: {len(dupes)} duplicate titles: {list(dupes.keys())}")
else:
    print(f"[PASS] books-data.js: no duplicate titles")

# 3. notes-data.js — balanced braces
with open(NOTES_JS, 'r') as f:
    n = f.read()
ob, cb = n.count('{'), n.count('}')
if ob == cb:
    print(f"[PASS] notes-data.js: braces balanced ({ob}/{cb})")
else:
    errors.append(f"notes-data.js braces: {ob} open, {cb} close")
    print(f"[FAIL] notes-data.js: braces {ob}/{cb}")

# 4. Note coverage
notes_present = sum(1 for e in arr if e['title'] in n)
notes_missing = len(arr) - notes_present
print(f"[INFO] Books with notes: {notes_present}/{len(arr)} ({notes_missing} without)")

# 5. CDN reachable
for name, url in [('books-data.js', 'https://dmpotekhin.github.io/js/books-data.js'),
                   ('notes-data.js', 'https://dmpotekhin.github.io/js/notes-data.js')]:
    try:
        req = urllib.request.Request(url, method='HEAD')
        resp = urllib.request.urlopen(req, timeout=10)
        print(f"[PASS] CDN {name}: {resp.status}")
    except Exception as e:
        errors.append(f"CDN {name}: {e}")
        print(f"[FAIL] CDN {name}: {e}")

print()
if errors:
    print(f"VERIFICATION: {len(errors)} failures")
    for e in errors:
        print(f"  X {e}")
    exit(1)
else:
    print("VERIFICATION: all checks passed")

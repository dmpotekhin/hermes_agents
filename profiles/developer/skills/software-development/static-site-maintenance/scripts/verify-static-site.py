"""Verification script template for static HTML/CSS/JS sites.
Copy, customize PROJECT and CHECKS, run.
"""
import subprocess, json, os

PROJECT = "/path/to/site"
passed = 0
total = 0

def check(name, ok, detail=""):
    global passed, total
    total += 1
    if ok:
        passed += 1
        print(f"PASS: {name} {detail}")
    else:
        print(f"FAIL: {name} {detail}")

# === JS Syntax Checks ===
for fname in ["js/data.js", "js/app.js"]:
    path = os.path.join(PROJECT, fname)
    if not os.path.exists(path):
        check(f"syntax:{fname}", False, "file not found")
        continue
    r = subprocess.run(['node', '-e',
        f'const fs=require("fs");new Function(fs.readFileSync("{path}","utf8"));console.log("OK");'
    ], capture_output=True, text=True)
    check(f"syntax:{fname}", r.returncode == 0, r.stderr[:80] if r.returncode else "")

# === Data Integrity (for generated data files) ===
data_file = os.path.join(PROJECT, "js/data.js")
if os.path.exists(data_file):
    r = subprocess.run(['node', '-e',
        f'const fs=require("fs");'
        f'const a=JSON.parse(fs.readFileSync("{data_file}","utf8").match(/\\[[\\s\\S]*\\]/)[0]);'
        'console.log(JSON.stringify({t:a.length,g:[...new Set(a.map(b=>b.genre||"none"))],'
        'bad:a.filter(b=>!b.genre||!b.title).length}));'
    ], capture_output=True, text=True)
    if r.returncode == 0:
        d = json.loads(r.stdout.strip())
        check("data:count", d["t"] > 0, str(d["t"]))
        check("data:all_fields", d["bad"] == 0, f"incomplete: {d['bad']}")
    else:
        check("data:parse", False, r.stderr[:80])

# === HTML Structure ===
html_file = os.path.join(PROJECT, "index.html")
if os.path.exists(html_file):
    html = open(html_file).read()
    # CUSTOMIZE: add checks for your page
    CHECKS = [
        ("filter_exists", 'id="genre-filter"'),
        ("sort_exists", "genre-asc"),
        ("dynamic_section", 'id="stats-grid"'),
    ]
    for name, pattern in CHECKS:
        check(f"html:{name}", pattern in html)

# === CSS Rules ===
css_file = os.path.join(PROJECT, "css/styles.css")
if os.path.exists(css_file):
    css = open(css_file).read()
    # CUSTOMIZE: add checks for your CSS classes
    CSS_CHECKS = [
        ("new_component", ".book-genre-badge"),
    ]
    for name, pattern in CSS_CHECKS:
        check(f"css:{name}", pattern in css)

# === Summary ===
print(f"\n{'='*40}")
print(f"VERIFICATION: {passed}/{total} passed")
if passed == total:
    print("ALL CHECKS PASSED")
else:
    print("FAILURES DETECTED — fix before claiming completion")

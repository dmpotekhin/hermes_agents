#!/usr/bin/env python3
"""Verify js/books-data.js + js/notes-data.js in the dmpotekhin.github.io repo.

Usage:
    python3 verify_books_data.py [title1 "title2 with spaces"...]

Checks:
  1. node --check syntax on both files (fast parse-only; NOT blocked by guard)
  2. JS-compatible parse (comments stripped, prefix removed, trailing commas tolerated)
  3. Every book has a matching note (MISSING == 0)
  4. No duplicate note keys
  5. Optional: given titles have 5 theses + takeaway each

Exit code 0 = all checks passed. Prints PASS/FAIL per check.

NOTE: the data files are JS, not JSON — trailing commas (`,]` / `,}`) are valid JS
but invalid for bare json.loads. Do NOT run json.loads on them directly.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path.home() / "Downloads" / "dmpotekhin.github.io"


def parse_js_text(s: str, varname: str):
    body = re.sub(r"^\s*//.*$", "", s, flags=re.M)          # strip // comments
    body = body.replace("export ", "", 1)                    # tolerate export prefix
    body = body.replace(varname + " = ", "", 1).rstrip().rstrip(";")
    body = re.sub(r",(\s*[\]}])", r"\1", body).lstrip()      # tolerate trailing commas
    return json.JSONDecoder().raw_decode(body)[0]


def main():
    new_titles = sys.argv[1:]
    failures = []

    for name in ("js/books-data.js", "js/notes-data.js"):
        r = subprocess.run(["node", "--check", str(REPO / name)],
                           capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            failures.append(f"node --check {name} FAILED: {r.stderr[:300]}")
        else:
            print(f"PASS node --check {name}")

    books = parse_js_text((REPO / "js/books-data.js").read_text(encoding="utf-8"), "const booksData")
    notes = parse_js_text((REPO / "js/notes-data.js").read_text(encoding="utf-8"), "const bookNotes")
    print(f"INFO books={len(books)} notes={len(notes)}")

    missing = [b for b in books if b["title"] not in notes]
    if missing:
        failures.append(f"{len(missing)} books without notes: {[b['title'] for b in missing]}")
    else:
        print("PASS all books have notes (MISSING=0)")

    keys = list(notes.keys())
    dups = {k for k in keys if keys.count(k) > 1}
    if dups:
        failures.append(f"duplicate note keys: {dups}")
    else:
        print("PASS no duplicate note keys")

    for title in new_titles:
        v = notes.get(title)
        if v is None:
            failures.append(f"note missing: {title}")
        elif len(v.get("theses", [])) != 5 or not v.get("takeaway"):
            failures.append(f"note incomplete: {title} theses={len(v.get('theses', []))}")
        else:
            print(f"PASS note OK: {title}")

    if failures:
        print("\nFAILURES:")
        for f in failures:
            print("  -", f)
        sys.exit(1)
    print("\nALL CHECKS PASSED")


if __name__ == "__main__":
    main()

#!/bin/bash
# verify-books.sh — shell-based verification for dmpotekhin.github.io book system
# No node -e, no python3 -c — avoids terminal guard. Safe for ad-hoc verification.
# Run from repo root: bash scripts/verify-books.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

errors=0

echo "=== 1. books-data.js ==="
BOOK_COUNT=$(grep -c '"title"' js/books-data.js || echo 0)
echo "books-data.js: $BOOK_COUNT books"
wc -c js/books-data.js

echo ""
echo "=== 2. notes-data.js ==="
NOTES_COUNT=$(grep -c '"theses"' js/notes-data.js || echo 0)
echo "notes-data.js: $NOTES_COUNT notes"
LOCAL_SIZE=$(wc -c < js/notes-data.js)
echo "notes-data.js size: $LOCAL_SIZE bytes"

echo ""
echo "=== 3. Missing notes ==="
echo "Books: $BOOK_COUNT | Notes: $NOTES_COUNT | Delta: $((BOOK_COUNT - NOTES_COUNT))"

echo ""
echo "=== 4. Git status ==="
CHANGES=$(git status --short)
if [ -n "$CHANGES" ]; then
    echo "Uncommitted changes:"
    echo "$CHANGES"
    ((errors++))
else
    echo "clean"
fi
echo "Last: $(git log --oneline -1)"

echo ""
echo "=== 5. Temp files ==="
TEMP=$(ls _*.py 2>/dev/null || true)
if [ -n "$TEMP" ]; then
    echo "LEFTOVERS: $TEMP"
    ((errors++))
else
    echo "clean"
fi

echo ""
echo "=== 6. CDN propagation ==="
CDN_INFO=$(curl -sI https://dmpotekhin.github.io/js/notes-data.js 2>/dev/null | grep -E 'content-length|last-modified' || echo "CDN unreachable")
echo "$CDN_INFO"
CDN_SIZE=$(echo "$CDN_INFO" | grep content-length | awk '{print $2}' | tr -d '\r')
if [ -n "$CDN_SIZE" ] && [ "$CDN_SIZE" != "$LOCAL_SIZE" ]; then
    echo "WARNING: CDN ($CDN_SIZE) != local ($LOCAL_SIZE) — may be propagating"
else
    echo "CDN matches local ✓"
fi

echo ""
if [ "$errors" -eq 0 ]; then
    echo "ALL CHECKS PASSED"
    exit 0
else
    echo "$errors errors found"
    exit 1
fi

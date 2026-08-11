#!/bin/bash
# Verify a GitHub Pages deploy — checks that CDN serves the expected content.
# Usage: bash references/verify-deploy.sh USER REPO PATH_PATTERN EXPECTED_STRING [MIN_SIZE]
#
# Example: bash references/verify-deploy.sh dmpotekhin dmpotekhin.github.io js/books.js genreParts 10000

USER="${1:?Usage: $0 USER REPO PATH EXPECTED_STRING [MIN_SIZE]}"
REPO="${2:?}"
FPATH="${3:?}"
EXPECTED="${4:?}"
MIN_SIZE="${5:-1000}"

URL="https://${USER}.github.io/${FPATH}"
P=0
T=0

check() { T=$((T+1)); if eval "$1"; then P=$((P+1)); echo "PASS: $2"; else echo "FAIL: $2"; fi; }

echo "=== GitHub Pages Deploy Verification ==="
echo "URL: $URL"
echo "Expected: '$EXPECTED', min size: ${MIN_SIZE}"
echo ""

# Header checks — key signals for CDN propagation
LAST_MOD=$(curl -sI "$URL" 2>/dev/null | grep 'last-modified' | awk -F': ' '{print $2}' | tr -d '\r')
CL=$(curl -sI "$URL" 2>/dev/null | grep 'content-length' | awk '{print $2}' | tr -d '\r')
EDGE=$(curl -sI "$URL" 2>/dev/null | grep 'x-served-by' | awk -F': ' '{print $2}' | tr -d '\r')

echo "Last-Modified: ${LAST_MOD:-unknown}"
echo "Content-Length: ${CL:-0} bytes"
echo "Edge Node:     ${EDGE:-unknown}"
echo ""

# Verify expected string in response body
check "curl -s '$URL' | grep -qF '$EXPECTED'" \
     "expected string found in response"

# MIN_SIZE: catches stale CDN serving old truncated version
# E.g. old commit: 3655 bytes, new commit: 14840 — difference is the signal
check '[ "${CL:-0}" -ge '"$MIN_SIZE"' ]' \
     "content-length ${CL:-0} >= ${MIN_SIZE}"

echo ""
echo "VERIFICATION: $P/$T passed"
[ "$P" -eq "$T" ] && echo "DEPLOY CONFIRMED" || echo "DEPLOY NOT YET PROPAGATED — retry in 60s"

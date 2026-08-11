#!/usr/bin/env bash
# verify-deploy.sh — confirm GitHub Pages deploy reached CDN
# Usage: verify-deploy.sh USER REPO PATH EXPECTED_STRING [MIN_BYTES]
# Example: verify-deploy.sh dmpotekhin dmpotekhin.github.io js/books.js genreParts 10000

set -euo pipefail

USER="${1:?Usage: verify-deploy.sh USER REPO PATH EXPECTED_STRING [MIN_SIZE]}"
REPO="${2:?}"
FILE="${3:?}"
EXPECTED="${4:?}"
MIN_SIZE="${5:-5000}"

URL="https://${USER}.github.io/${FILE}"

echo "=== verify-deploy: ${URL} ==="
echo "Expecting string: '${EXPECTED}', min size: ${MIN_SIZE} bytes"
echo ""

# Headers
echo "--- Headers ---"
HEADERS=$(curl -sI "${URL}" 2>/dev/null)
echo "${HEADERS}" | grep -E 'last-modified|content-length|etag|x-served-by|x-cache|age' || true

# Content check
SIZE=$(echo "${HEADERS}" | grep -i content-length | awk '{print $2}' | tr -d '\r')
echo ""
echo "--- Content ---"
CONTENT=$(curl -s "${URL}" 2>/dev/null)

if [ -z "${CONTENT}" ]; then
    echo "FAIL: Empty response"
    exit 1
fi

CONTENT_SIZE=$(echo -n "${CONTENT}" | wc -c | tr -d ' ')
echo "Response size: ${CONTENT_SIZE} bytes (header says ${SIZE:-unknown})"

# Checks
PASS=0
TOTAL=3

if echo "${CONTENT}" | grep -q "${EXPECTED}"; then
    echo "PASS: Found '${EXPECTED}' in response"
    PASS=$((PASS+1))
else
    echo "FAIL: '${EXPECTED}' NOT found — CDN may be stale"
fi

if [ -n "${SIZE}" ] && [ "${SIZE}" -gt "${MIN_SIZE}" ]; then
    echo "PASS: Content-Length ${SIZE} > ${MIN_SIZE} (expected new version)"
    PASS=$((PASS+1))
elif [ -n "${SIZE}" ]; then
    echo "FAIL: Content-Length ${SIZE} <= ${MIN_SIZE} — likely stale"
else
    echo "WARN: No Content-Length header"
    PASS=$((PASS+1))
fi

if echo "${HEADERS}" | grep -q '200'; then
    echo "PASS: HTTP 200"
    PASS=$((PASS+1))
else
    echo "FAIL: HTTP status not 200"
fi

echo ""
echo "VERIFICATION: ${PASS}/${TOTAL}"
if [ "${PASS}" -eq "${TOTAL}" ]; then
    echo "STATUS: ALL CHECKS PASSED"
    exit 0
else
    echo "STATUS: FAILURES — CDN may not have the latest deploy yet (wait 1-2 min and retry)"
    exit 1
fi

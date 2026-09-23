#!/usr/bin/env bash
# Carousel Factory — offline walk of the ten-stage pipeline through `cli.py`.
#
# Usage:  bash scripts/carousel-cli-walk.sh [path/to/source-context.json]
#         (template: templates/carousel-source-context.json)
#
# Safe by construction: every step runs against a FRESH /tmp database, so the app DB is
# never touched, and CarouselConfig defaults to dry_run=True, so `publish` reports `manual`
# with an EMPTY request_id instead of uploading anything. The commands below and their
# outcomes were walked by hand on 2026-09-19 (branch feature/tri-face-carousel-factory,
# every step exit 0). Flag names mirror tests/test_carousel_cli.py; argparse fails loudly if
# one drifts, and every step prints {"error": ...} rather than lying about success.
set -euo pipefail

PROJECT="${PROJECT:-$HOME/projects/travel-blog-app}"
cd "$PROJECT"
FIXTURE="${1:-/tmp/carousel_source_context.json}"
DB="/tmp/carousel_cli_walk_$(date +%s).db"   # fresh path per run — never rm an older one
CLI=".venv/bin/python -m cli carousel --db $DB"
SRC="http://127.0.0.1:8799/cf_article.html"  # the id barely matters: the fixture holds the facts

step() { echo; echo "== $1"; }
job_id_of() { sed -n 's/.*"job_id": *\([0-9]\{1,\}\).*/\1/p' <<<"$1"; }

step "create"
OUT=$($CLI create --source "$SRC" --vertical travel --title "Offline walk")
echo "$OUT"
JOB=$(job_id_of "$OUT")
[ -n "$JOB" ] || { echo "no job_id in create output"; exit 1; }

step "research — facts come from the hand-written fixture, nothing is fetched"
$CLI research --job-id "$JOB" --fixture "$FIXTURE"

step "draft + plan (expect 6 slides)"
$CLI draft --job-id "$JOB"
$CLI plan --job-id "$JOB"

step "render (expect 6 JPG under public/carousels/job_$JOB)"
$CLI render --job-id "$JOB"
TOTAL=$(find "public/carousels/job_$JOB" -name 'slide_*.jpg' | wc -l | tr -d ' ')
echo "slides on disk: $TOTAL"
[ "$TOTAL" = 6 ] || { echo "expected 6 rendered JPG"; exit 1; }

step "verify — read the report, passed should equal checked"
$CLI verify --job-id "$JOB"

step "submit -> approval queue -> approve (human in the middle)"
$CLI submit --job-id "$JOB"
$CLI queue
$CLI approve --job-id "$JOB" --by "offline-walk" --note "offline walk"

step "publish — dry run: two 'manual' rows, EMPTY request_id"
$CLI publish --job-id "$JOB"

step "collect + advice — expect 0 metrics plus a warning; no invented numbers"
$CLI collect --job-id "$JOB"
$CLI advice --vertical travel || true   # refusing to score without metrics IS the honest answer
$CLI status --job-id "$JOB"

echo
echo "done — DB kept at $DB for inspection (remove it yourself when you are finished)"

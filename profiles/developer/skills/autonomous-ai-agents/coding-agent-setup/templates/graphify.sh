#!/bin/bash
# Dependency-graph run. Usage: ./graphify.sh [path]
set -e
PROJECT="${1:-.}"
GRAPHIFY="$HOME/Library/Python/3.11/bin/graphify"
if [ ! -x "$GRAPHIFY" ]; then
  echo "graphify not found at $GRAPHIFY — install: pip3 install --user graphifyy" >&2
  exit 1
fi
"$GRAPHIFY" "$PROJECT" --code-only
echo "Report:  $PROJECT/graphify-out/GRAPH_REPORT.md"
echo "Graph:   $PROJECT/graphify-out/graph.html (open in browser)"

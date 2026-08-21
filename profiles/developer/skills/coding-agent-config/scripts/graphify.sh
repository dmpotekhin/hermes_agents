#!/bin/bash
# Прогон graphify по проекту. Использование: ./graphify.sh [путь]
# Путь по умолчанию — текущая директория.
set -e
PROJECT="${1:-.}"

# Бинарь может быть не в PATH (pip --user на macOS)
GRAPHIFY=""
for cand in "$HOME/Library/Python/3.11/bin/graphify" "$(command -v graphify 2>/dev/null || true)"; do
  if [ -n "$cand" ] && [ -x "$cand" ]; then GRAPHIFY="$cand"; break; fi
done

if [ -z "$GRAPHIFY" ]; then
  echo "graphify не найден. Установка: pip3 install --user graphifyy"
  exit 1
fi
echo "graphify: $GRAPHIFY"
echo "project: $PROJECT"
if [ -z "${DEEPSEEK_API_KEY:-}" ]; then
  echo "WARN: DEEPSEEK_API_KEY не задан — граф будет без LLM-отчётов"
fi

cd "$PROJECT"
"$GRAPHIFY" .
echo "Готово: graphify-out/ (GRAPH_REPORT.md + graph.html)"

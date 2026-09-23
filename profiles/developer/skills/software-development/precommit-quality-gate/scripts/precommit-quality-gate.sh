#!/usr/bin/env bash
# precommit-quality-gate.sh — универсальный качественный pre-commit (для ИИ-агентов).
# Копируй в <repo>/.git/hooks/pre-commit и chmod +x.
#
# Логика:
#  - staged .py  -> py_compile (синтаксис) + ruff check (линт)
#  - staged .js/.jsx/.ts/.tsx -> eslint (линт)
#  - отказоустойчивость: инструмент не установлен -> warn, НЕ блокируем
#  - блокируем только реальный провал синтаксиса/линта
#
# НАСТРОЙКА: при необходимости поменяй JS_DIR на каталог с package.json
# (например "frontend" для монрепо, "." если корень — фронтенд).
# Тяжёлые проверки (pytest, vite build) вынеси в .git/hooks/pre-push — см. скилл.
set -u

# Расширяем PATH для неинтерактивных git-оболочек (gitleaks/ruff/eslint и т.п.)
export PATH="$HOME/bin:$HOME/Library/Python/3.11/bin:$PATH"

RED=$'\033[31m'; YELLOW=$'\033[33m'; GREEN=$'\033[32m'; RESET=$'\033[0m'
BLOCK=0
WARN=0
have() { command -v "$1" >/dev/null 2>&1; }

JS_DIR="frontend"   # <-- правь под репо: "." для чистого фронта, "frontend" для монрепо
JS_EXT='\.(js|jsx|ts|tsx|mjs|cjs)$'

STAGED_PY=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.py$' || true)
STAGED_JS=$(git diff --cached --name-only --diff-filter=ACM | grep -E "$JS_EXT" || true)

# --- 0. Python: синтаксис (нужен только python3) ---
if [ -n "$STAGED_PY" ]; then
  echo "${GREEN}[py-compile] проверяю синтаксис staged .py...${RESET}"
  if python3 -m py_compile $STAGED_PY 2>/tmp/py_compile.log; then
    echo "${GREEN}[py-compile] ok${RESET}"
  else
    echo "${RED}[py-compile] ОШИБКА СИНТАКСИСА — commit заблокирован:${RESET}"
    cat /tmp/py_compile.log
    BLOCK=1
  fi
fi

# --- 1. Python: ruff (линт) ---
if [ -n "$STAGED_PY" ]; then
  if have ruff; then
    echo "${GREEN}[ruff] линт staged .py...${RESET}"
    if ! ruff check $STAGED_PY --output-format=concise 2>&1 | tee /tmp/ruff.log; then
      echo "${RED}[ruff] найдены ошибки линта — commit заблокирован${RESET}"
      BLOCK=1
    else
      echo "${GREEN}[ruff] чисто${RESET}"
    fi
  else
    echo "${YELLOW}[ruff] не установлен — пропуск (pip install --user ruff)${RESET}"
    WARN=1
  fi
fi

# --- 2. JS/TS: eslint ---
if [ -n "$STAGED_JS" ]; then
  ESLINT_BIN="$JS_DIR/node_modules/.bin/eslint"
  if [ -x "$ESLINT_BIN" ]; then
    echo "${GREEN}[eslint] линт staged JS/TS...${RESET}"
    # пути staged относительны корня репо; сдаём их eslint'у из JS_DIR
    if ! (cd "$JS_DIR" && ./node_modules/.bin/eslint $STAGED_JS 2>&1 | tee /tmp/eslint.log); then
      echo "${RED}[eslint] ошибки линта — commit заблокирован${RESET}"
      BLOCK=1
    else
      echo "${GREEN}[eslint] чисто${RESET}"
    fi
  else
    echo "${YELLOW}[eslint] не установлен — пропуск (cd $JS_DIR && npm i -D eslint)${RESET}"
    WARN=1
  fi
fi

# --- 3. Статы ---
if [ "$BLOCK" -eq 1 ]; then
  echo "${RED}==== COMMIT ЗАБЛОКИРОВАН (pre-commit quality gate) ====${RESET}"
  echo "Разрешить осознанно: git commit --no-verify"
  exit 1
fi
[ "$WARN" -eq 1 ] && echo "${YELLOW}==== предупреждения выше — проверь инструменты ====${RESET}"
echo "${GREEN}==== pre-commit quality gate: OK ====${RESET}"
exit 0

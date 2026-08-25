#!/usr/bin/env bash
# Start DeepSeek Harness MCP server (StreamableHTTP) on 127.0.0.1:8090.
# Requires: node >= 22 (default node v14 breaks dsh) and DEEPSEEK_API_KEY in ~/.hermes/.env.
set -euo pipefail

export PATH="$HOME/.nvm/versions/node/v22.23.2/bin:$PATH"

if ! command -v dsh >/dev/null 2>&1; then
  echo "dsh not found — install: npm install -g @deepseek-ai/dsh@0.1.0-rc.8" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source "$HOME/.hermes/.env"
set +a

exec dsh --profile web --no-open

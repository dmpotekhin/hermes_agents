# OpenViking (volcengine/OpenViking) — evaluation notes, 2026-08-20

Repo: https://github.com/volcengine/OpenViking · Clone at the time of study: /tmp/OpenViking (3930 files)
Status: evaluated, NOT adopted. User decision pending («подключить или позаимствовать идеи?» — без ответа).

## What it is

OpenViking — open-source **context database for AI agents** from Volcengine/ByteDance (Rust + Python).
Stores memories, resources, and skills as a virtual filesystem under the `viking://` protocol; agent
browses its own context with `ls`/`tree`/`find` instead of querying a black-box vector store.
Paper: VikingMem, arXiv:2605.29640, VLDB 2026. License: AGPLv3 main; Apache 2.0 for crates/ov_cli and examples.

## Key mechanics (useful as design ideas for obsidian-brain)

- **L0/L1/L2 tiered loading**: every entry processed on write into L0 abstract (~100 tok),
  L1 overview (~2K tok), L2 full detail. Every directory carries `.abstract`/`.overview` files;
  full content read only when needed. Token savings are the selling point.
- **Directory-recursive retrieval**: vector search locates highest-scoring DIRECTORY, then drills
  down layer by layer — results arrive with surrounding context intact.
- **Observable retrieval**: every query preserves its directory-browsing trajectory; wrong result →
  you can see which path produced it.
- **Sessions become memory**: after a session commits, asynchronously extracts user preferences and
  agent experience into long-term memory (cursor-based sync).
- `ov dream` / `ov recall` — manual sync/search commands (example skill `examples/skills/ov_dream/SKILL.md`):
  reads agent sessions.json, syncs eligible chat transcripts, keeps per-session sync cursor.

## Hermes integration (the practical hook)

Hermes has a **built-in memory provider** for OpenViking — no plugin:
```
hermes memory setup openviking   # wizard: cloud API key, or custom URL (default http://127.0.0.1:1933) + API key (empty for local)
hermes memory status
```
Available external providers: honcho, openviking, mem0, hindsight, holographic, retaindb, byterover.
Only one external provider active at a time; built-in MEMORY.md/USER.md always active.
Benchmarks (their blog, repro in ./benchmark): LoCoMo accuracy Hermes 33.38% native → 82.86% with
OpenViking; input tokens −34.3–91.0%; query latency −58.45–66.10%. tau2-bench task success +6.87pp/+11.87pp.

## Other integrations

Claude Code, Codex, OpenClaw, Cursor, TRAE, OpenCode, pi, Agent Plugins 1.0, MCP clients, LangChain/LangGraph,
VikingBot (agent framework on top). Install: `pip install openviking`, `openviking-server init` (wizard: providers,
models, ov.conf), `ov` CLI client. Supports Volcengine, OpenAI, Codex OAuth, Kimi, GLM, local Ollama.

## Architecture (from clone)

- `openviking/` — Python server (parsers: code AST via tree-sitter; storage: vectordb adapters incl. VikingDB, observers)
- `crates/` — Rust: `ov_cli` (CLI), `ragfs` (virtual FS / RAG filesystem), `ragfs-python` bindings
- `agent-plugins/` — Agent Plugins 1.0 package: `mcp.json` stdio proxy (node servers/mcp-proxy.mjs → streamable HTTP :1933),
  skill `openviking-memory` (recall + persist loop); zero npm deps
- `integrations/langchain`, `examples/` (memory plugins for claude-code/codex/cursor/openclaw/opencode/trae/zcode + skills)
- Docs portal docs.openviking.ai is NOT inside the repo — curl with browser UA to read pages

## Verdict for this user

- **Do NOT run as a second memory service** next to obsidian-brain (same reasoning as ai-memory: duplication,
  heavy infra — Python server + Rust + vector DB on :1933, Docker broken on this Mac; AGPLv3).
- **Worth trying as Hermes memory provider** for an experiment week (native install, no Docker; `hermes memory setup openviking`).
- **Ideas worth borrowing into obsidian-brain**: L0/L1/L2 tiering (obsidian-brain is all-L2 today),
  cursor-based session sync (like ov_dream), async post-session preference extraction (currently manual:
  brain_devlog + content-factory topics), observable retrieval trajectories.

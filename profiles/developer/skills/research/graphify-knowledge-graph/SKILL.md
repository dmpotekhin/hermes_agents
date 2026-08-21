---
name: graphify-knowledge-graph
description: "Run graphify to build a knowledge graph from a codebase."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [knowledge-graph, codebase, analysis, graphify, visualization]
---

# Graphify Knowledge Graph

Use when the user asks to run graphify over a project, build a knowledge graph of a codebase,
or visualize module structure / connections of a repo (e.g. "прогони graphify по проекту X").

Repo: Graphify-Labs/graphify. It is a Claude Code skill + standalone Python CLI (and MCP server).
The PyPI package is temporarily named `graphifyy`; the CLI command is `graphify`.

## Install (macOS)

```bash
pip3 install --user graphifyy
```

- Binary lands at `~/Library/Python/3.11/bin/graphify` (plus `graphify-mcp`) — NOT on default PATH.
  Call with the full path or add the dir to PATH.
- graphify can install itself as a skill for many platforms, including Hermes:
  `graphify install --platform hermes`.

## Run (extraction)

```bash
~/Library/Python/3.11/bin/graphify /path/to/project
```

- Code files (.py .ts .js .go .rs .java .c .cpp .rb .cs .kt .scala .php ...) are parsed locally via
  tree-sitter AST — no LLM, free, fast. AST extraction also catches docstrings as node labels.
- md/pdf/image files need an LLM backend. Without a key graphify errors out and suggests either
  `--code-only` (index just code, no key) or setting one of: GEMINI_API_KEY, ANTHROPIC_API_KEY,
  MOONSHOT_API_KEY (kimi), OPENAI_API_KEY, **DEEPSEEK_API_KEY** (deepseek is a first-class backend).
- FLAG ORDER PITFALL: `graphify --code-only <path>` fails with "unknown command". Flags go AFTER
  the path: `graphify <path> --code-only`.
- Output: `graphify-out/` inside the project dir — graph.json, .graphify_analysis.json,
  manifest.json, cache/, GRAPH_REPORT.md.

## Report generation

```bash
~/Library/Python/3.11/bin/graphify cluster-only /path/to/project --no-label          # free, no LLM naming
~/Library/Python/3.11/bin/graphify cluster-only /path/to/project --no-label --no-viz # report only, no html
~/Library/Python/3.11/bin/graphify label /path/to/project --backend deepseek          # LLM community naming
```

- `cluster-only` writes GRAPH_REPORT.md and re-clusters graph.json. WITHOUT `--no-viz` it also
  writes graph.html (interactive vis.js graph, ~400 KB) — rerun to regenerate the html.
- GRAPH_REPORT.md contains: god nodes (architectural hubs by degree), surprising connections,
  import cycles, community breakdown (cohesion + node lists), knowledge gaps (isolated nodes),
  suggested questions (high-betweenness bridges).
- `label` costs LLM tokens (community naming); `--no-label` keeps the whole pipeline free.
- Open graph.html for the user with `open /path/to/project/graphify-out/graph.html`.

## Post-build queries (no re-run needed)

```bash
graphify god-nodes --graph <path>/graphify-out/graph.json
graphify query "<question>" --graph ...    # BFS traversal
graphify explain "NodeName" --graph ...
graphify path "A" "B" --graph ...          # shortest path between nodes
graphify update <path>                     # re-extract changed code files, no LLM cost
```

## Pitfalls

- Flags come after the path argument (argparse order) — `--code-only` before the path errors.
- Without an LLM key, docs/md/images are SKIPPED silently with a warning; use `--code-only` for a
  pure code graph, or export a key (deepseek works).
- Vendor code (bundled libs like gif.js, mp4-muxer) shows up as its own communities and god nodes
  (e.g. GIFEncoder with the most edges) — expected, not your code; mention it when reporting.
- Isolated nodes (e.g. a `start.sh` with no edges) are listed in Knowledge Gaps — flag them as
  possible undocumented components.
- CLI help is command-based (`graphify --help` lists subcommands); the bare run is `graphify <path>`.
- Wiring into coding agents: reference `graphify-out/GRAPH_REPORT.md` from the project's
  `AGENTS.md` (e.g. "read GRAPH_REPORT.md before big refactors, regenerate after structural
  changes") so OpenCode/KiloCode/Claude-Code agents see the dependency map every session.
  See the `coding-agent-setup` skill for the full AGENTS.md pattern.
- For studying a third-party repo before running graphify, see the `external-repo-research` skill.

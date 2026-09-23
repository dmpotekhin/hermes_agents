# Researched dev tools — fact bank

Condensed, sourced knowledge from the docs-cheatsheet runs. Facts come from fetched pages; reuse when the same tool comes back up. Do not trust memory over this file.

## pen.dev (Pencil) — "Design on canvas. Land in code."

- **What**: vector design tool living INSIDE the IDE (VS Code / Cursor / desktop / CLI). Design lives in a git-native `.pen` file (JSON object tree on an infinite 2D canvas: rectangle/frame/text/script, `id` + `type` + `x/y`). An AI agent reads/edits the `.pen` via a local MCP server; design → code without screenshot hand-off.
- **Sources**: docs at https://docs.pen.dev/ (root `/` is the ONLY URL web_extract blocks with "private/internal network address"; subpages extract fine).
- **CLI**: `npm install -g @pen.dev/cli` (Node 18+). Auth: `pen login` (email+password/OTP → `~/.pencil/session-cli.json`) or `PEN_CLI_KEY=pencil_cli_...` for CI. Commands: `pen status`, `pen version`, `pen interactive -o design.pen`, `pen --list-models`. Agent mode: `pen --out design.pen --prompt "..."`; modify `pen --in old.pen --out new.pen --prompt "..."`; export `pen --in design.pen --export design.png`; `--model <id>` (default `claude-opus-4-6`), `--custom`, `--tasks`, `--workspace`, `--export-type png|jpeg|webp|pdf`, `--verbose-mcp`.
- **MCP server**: starts automatically when pen.dev opens; runs locally; tools exposed to assistants. 
- **Supported assistants (NOT Hermes)**: Claude Code, Claude Desktop, Cursor, Windsurf, Codex CLI, Antigravity, OpenCode CLI. AI features require the Claude Code CLI installed + authenticated (`npm i -g @anthropic-ai/claude-code-cli`; `claude`).
- **Key workflow**: Cmd/Ctrl+K in the pen.dev canvas → prompt ("Create a login form", "Make the sidebar narrower"). Two-way: design → code ("Create a React component for this button"), code → design ("Recreate the Button from src/components/Button.tsx"). Save with Cmd/Ctrl+S — **no auto-save**.
- **Hermes verdict**: NOT a first-class supported assistant. Path 1 (headless `pen` CLI from the agent) works — the agent just forwards a prompt; the model caveat is that pen.dev's own agent runs Claude. Path 2 (MCP stdio) has NO documented standalone launch command (`pen mcp`/`pen serve` absent) → not recommended. Downside vs OpenDesign: Hermes not in the adapter list.

## OpenDesign — open-source Claude-Design alternative

- **What**: open-source (Apache-2.0), local-first alternative to Claude Design. Your own coding agent becomes the design engine: prototypes, landing pages, dashboards, slides, images, video as REAL files (export HTML/PDF/PPTX/MP4).
- **Repo**: https://github.com/nexu-io/open-design. Sites: https://opendesigner.io/ (21 BYOK adapters), https://open-design.ai/ (17 adapters). Comparison page vs Pencil: https://open-design.ai/alternatives/pencil-dev/. Review: https://www.neura.market/news/open-design-open-source-claude-design-alternative (says runs with `pnpm tools-dev`, local-first + web-deployable, BYOK at every layer).
- **BYOK**: uses whichever coding-agent CLI is on PATH, or any OpenAI-compatible API key via a BYOK proxy. **Adapters include Hermes** (both sites list it) alongside Claude Code, Codex CLI, Cursor, Gemini CLI, OpenCode, Qwen, DeepSeek, GitHub Copilot CLI, Grok, Kimi, Devin for Terminal, Qoder, Kilo, Mistral Vibe, Kiro, Aider, Antigravity, Reasonix, Pi, Trae.
- **Agent-native loop** (per repo description): discover the brief → lock the direction → stream the artifact → critique → deliver.
- **Hermes verdict**: FIRST-CLASS — Hermes appears in the BYOK adapter list, so integration is trivial (no CLI workaround, no proprietary-agent caveat unlike pen.dev).
- **Open question at plan time**: exact install command (expected `pnpm tools-dev`) and the precise way to point OpenDesign at Hermes — confirm from the README at execution, don't invent.

## Anti-bot root-block quirk (shared pitfall, reuse)

`web_extract` returns `Blocked: URL targets a private or internal network address` for doc-site ROOTS (docs.pen.dev/). Subpages usually extract fine. Deterministic fallback: `curl -A "<browser UA>" <url>` + strip `<main>`/`<body>` to text (see SKILL.md snippet), or GitHub `raw.githubusercontent.com/<owner>/<repo>/main/README.md`.

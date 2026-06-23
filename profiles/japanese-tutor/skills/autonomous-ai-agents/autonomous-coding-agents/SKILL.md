---
name: autonomous-coding-agents
description: "Orchestrate external AI coding agents (Claude Code, Codex, OpenCode) from Hermes — one-shot tasks, interactive sessions, PR reviews, parallel work."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, Claude, Codex, OpenCode, Automation, Code-Review, Refactoring]
    category: autonomous-ai-agents
---

# Autonomous Coding Agents

Delegate coding tasks to external AI coding agent CLIs (Claude Code, Codex CLI, OpenCode) from Hermes.

---

## Section 1: Claude Code (Anthropic)

### Prerequisites
```bash
npm install -g @anthropic-ai/claude-code
claude auth login
```

### Print Mode (Preferred for one-shot)
```bash
claude -p 'Add error handling to all API calls' --allowedTools 'Read,Edit' --max-turns 10
terminal(command="claude -p '...' --max-turns 10", workdir="/project", timeout=120)
```

Key flags: `--output-format json`, `--json-schema`, `--max-budget-usd`, `--bare`, `--model haiku`

### Interactive Mode (via tmux)
```bash
tmux new-session -d -s claude-work -x 140 -y 40
tmux send-keys -t claude-work 'cd /project && claude' Enter
sleep 5 && tmux send-keys -t claude-work 'Refactor auth module' Enter
```

### Additional Features
- CLAUDE.md / .claude/rules/ for project context
- Custom subagents in .claude/agents/
- MCP servers: `claude mcp add github -- npx @modelcontextprotocol/server-github`
- Slash commands: /compact, /review, /plan, /model

---

## Section 2: Codex CLI (OpenAI)

### Prerequisites
```bash
npm install -g @openai/codex
```

### One-Shot
```bash
codex exec 'Add dark mode toggle'
terminal(command="codex exec '...'", workdir="~/project", pty=true)
```

Key flags: `--full-auto` (sandbox auto-approve), `--yolo` (no sandbox)

### Background Mode
```bash
terminal(command="codex exec --full-auto 'Refactor auth'", workdir="~/project", background=true, pty=true)
process(action="poll", session_id="<id>")
```

### Gateway Caveat
Use `--sandbox danger-full-access` when bubblewrap fails in gateway contexts.

---

## Section 3: OpenCode CLI

### Prerequisites
```bash
npm i -g opencode-ai@latest
opencode auth list
```

### One-Shot
```bash
opencode run 'Add retry logic to API calls'
terminal(command="opencode run '...'", workdir="~/project")
```

### Interactive (Background)
```bash
terminal(command="opencode", workdir="~/project", background=true, pty=true)
process(action="submit", session_id="<id>", data="Implement OAuth refresh")
```

Key flags: `--agent` (build/plan), `--model`, `--file`, `--thinking`, `--continue`

### Pitfalls
- `/exit` is NOT valid — use Ctrl+C (`\x03`)
- `opencode run` does NOT need pty; interactive TUI does

---

## Common Patterns

### Quick Code Review
```bash
# Claude
git diff main...HEAD | claude -p 'Review this diff' --max-turns 1
# Codex
codex exec 'Review changes: git diff main...HEAD'
# OpenCode
opencode run 'Review this PR vs main. Report bugs and security risks.'
```

### Rules for Hermes Agents
1. Prefer Claude Code's print mode (`-p`) for single tasks
2. Use `pty=true` for Codex (always required)
3. OpenCode `run` doesn't need pty
4. Always set `workdir`
5. Set `--max-turns` to prevent runaway
6. Clean up tmux sessions when done

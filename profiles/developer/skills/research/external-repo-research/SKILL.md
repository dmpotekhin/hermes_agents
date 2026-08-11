---
name: external-repo-research
description: "Study third-party GitHub repos: clone, explore, analyze."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [research, github, codebase, analysis, third-party, architecture]
---

# External Repo Research

Use when the user asks to study, evaluate, or understand a third-party GitHub repository — its architecture, utility, design decisions, or applicability to their own projects.

## Core workflow

### 1. Clone locally (always — do not rely on web_extract)

`web_extract` and `browser_navigate` frequently fail on GitHub URLs with "Blocked: URL targets a private or internal network address" or npm errors. Skip them entirely. Go straight to local clone:

```bash
cd /tmp && git clone --depth 1 <repo-url> <name>
```

`--depth 1` makes it fast; `/tmp` keeps it out of the project workspace.

### 2. Explore the structure

```bash
search_files("*.md", target="files", path="/tmp/<name>", limit=30)
search_files("*.py", target="files", path="/tmp/<name>", limit=20)
read_file("/tmp/<name>/README.md")
```

Key files to read in order:
- `README.md` — what the project is, how it works
- `docs/ARCHITECTURE.md` — system design (if exists)
- `docs/explanation/*.md` — design rationale
- `docs/COMMANDS.md` or `docs/CONFIGURATION.md` — usage surface
- Source tree overview: `search_files` by extension

### 3. Deep-dive specific areas

Use `search_files` with `file_glob` and content patterns to zero in:

```bash
search_files("context.engineering", path="/tmp/<name>", file_glob="*.md")
search_files("class Thing|def process", path="/tmp/<name>", file_glob="*.py")
```

### 4. Synthesize findings

Structure the output as:
- **What it is** — one-sentence summary
- **Problem it solves** — the pain point addressed
- **How it works** — key mental model (3-5 bullet points)
- **Architecture** — layers, components, data flow
- **Applicability** — how it relates to the user's current projects/tools
- **Gaps and risks** — maturity, dependencies, migration cost
- **Recommendation** — adopt, adapt ideas, or skip

### 5. Save the analysis

Save as a markdown plan/report in `.hermes/plans/` with a timestamped filename.

## Pitfalls

- **web_extract is unreliable for GitHub** — it consistently fails with "Blocked: private/internal network." Don't waste time retrying; clone immediately.
- **`write_file` cwd drift** — after terminal commands that `cd` or `git clone`, the session working directory may have changed. Verify the plan landed in the correct `.hermes/plans/` (not `/tmp/.hermes/plans/`). Use `cp` to fix if needed.
- **GitHub MCP may lack auth** — don't rely on `mcp__github__get_file_contents` unless you've confirmed credentials are set up.
- **Don't over-clone** — for a quick README-only look, `web_search` and search result descriptions may be enough. Clone only when deep understanding is needed.

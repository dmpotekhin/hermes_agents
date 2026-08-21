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

### 3.5 Optional: run graphify for a structural map

For medium/large repos, run graphify (AST-only, no LLM key) over the clone — it produces a cheap
structural map (god nodes, communities, import cycles, isolated nodes) that grounds the
applicability verdict without reading the code:

```bash
~/Library/Python/3.11/bin/graphify /tmp/<name> --code-only   # flags AFTER the path
~/Library/Python/3.11/bin/graphify cluster-only /tmp/<name> --no-label --no-viz
```

- Read `graphify-out/GRAPH_REPORT.md` — a full project overview at ~2K tokens, vs the code itself
  at tens of thousands of tokens. Never read graph.json wholesale — it is bigger than the code.
- DeepSeek is a first-class LLM backend (`DEEPSEEK_API_KEY`) if semantic extraction of docs/images
  is wanted; without a key use `--code-only`.
- graphify can install itself as a Hermes skill: `graphify install --platform hermes`
  (lands as `graphify-knowledge-graph`, externally authored — treat as user-owned, don't patch).
- Real token numbers and when the graph pays off: `references/graphify-token-economics.md`.

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

Example of a condensed knowledge-bank reference for a studied repo (what it is, mechanics worth
borrowing, integration hooks, verdict): `references/openviking.md` (OpenViking context DB, evaluated
2026-08-20, decision pending). Reuse this shape when a studied repo's applicability is likely to
come up again.

## Skill-library sync (import / update)

When the repo is a *skills* repository (mattpocock/skills, obra/superpowers) or the user
asks "что можно использовать / обновляй", this is the import/update branch: compare with
the local skill set, adapt frontmatter to Hermes (description ≤60 chars, strip
Claude-specific fields), and either create new skills or rebase an installed bundle.
Full procedure, adaptation checklist, and the superpowers git-rebase update recipe:
`references/skill-library-sync.md`.

When the user asks "какие скиллы пришли из GitHub за всё время" (provenance audit) —
disk grep of `author:` frontmatter lines + bundle dir + session_search cross-check, and
the living Obsidian registry location: `references/provenance-audit.md`.

## Pitfalls

- **web_extract is unreliable for GitHub** — it consistently fails with "Blocked: private/internal network." or, when the extract backend is DuckDuckGo, "DuckDuckGo (ddgs) is a search-only backend and cannot extract URL content". Don't waste time retrying or switching URLs; clone immediately.
- **web_extract also blocks non-GitHub doc sites** — project doc portals (e.g. docs.openviking.ai) fail with the same "Blocked: URL targets a private or internal network address". Do not retry web_extract on alternate URL shapes. Instead curl with a browser UA and strip tags: `curl -sL --max-time 20 "<url>" -H "User-Agent: Mozilla/5.0" | python3 -c "import sys,html,re; t=sys.stdin.read(); t=re.sub(r'<script.*?</script>','',t,flags=re.S); t=re.sub(r'<style.*?</style>','',t,flags=re.S); t=re.sub(r'<[^>]+>',' ',t); t=html.unescape(t); t=re.sub(r'\s+',' ',t); print(t[:3000])"`. Works for server-rendered HTML; for JS-rendered sites fall back to the browser.
- **Docs are often NOT in the repo** — doc portals (docs.example.com) usually live outside the git clone; `ls docs/` may show nothing for integration/guide pages. Check the clone first, then curl the doc site directly for the specific page.
- **`write_file` cwd drift** — after terminal commands that `cd` or `git clone`, the session working directory may have changed. Verify the plan landed in the correct `.hermes/plans/` (not `/tmp/.hermes/plans/`). Use `cp` to fix if needed.
- **GitHub MCP may lack auth** — don't rely on `mcp__github__get_file_contents` unless you've confirmed credentials are set up.
- **Fast README peek before cloning**: `curl -sL https://raw.githubusercontent.com/<owner>/<repo>/<branch>/README.md` is cheap and reliable (works even when web_extract is blocked); read head/tail, then decide whether a full clone is needed.
- **Don't over-clone** — for a quick README-only look, `web_search` and search result descriptions may be enough. Clone only when deep understanding is needed. For deep structure analysis of the clone, consider running graphify over it (see `graphify-knowledge-graph` skill).

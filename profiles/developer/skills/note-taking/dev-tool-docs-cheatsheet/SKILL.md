---
name: dev-tool-docs-cheatsheet
description: "Use when writing a dev-tool cheatsheet into Obsidian."
version: 1.0.0
author: Hermes Agent
---

# dev-tool-docs-cheatsheet

Recurring class of task: the user hands over a developer tool (pen.dev, OpenDesign, etc.) and wants a **Russian-language, beginner-oriented cheatsheet** saved as an Obsidian note, plus the answer to *"can I use it with Hermes?"*. Ground every fact in real sources — never from memory. The workflow is research → raw text → write → verify, and it is the same whether the final doc is pen.dev or the next tool.

## When to use

- User names a dev tool (a design-to-code tool, CLI, MCP server, framework) and wants a cheat sheet / conspekt / "how to use it" explainer.
- User asks "can I use <tool> with Hermes?" — produce a clear yes/no with the two integration paths (native agent list vs CLI workaround).
- A plan-mode task whose deliverable is a documentation note (not code), so TDD does not apply — validation is grep-based, not tests.

## Target file conventions

- Write to the Obsidian vault: `/Users/dmitrypotekhin/Odsidian/obsidians/Obsidian Vault/Brain/notes/skills/<tool>.md` (adjacent to `pen-dev.md`, `open-design.md`, `2026-08-19-hermes-skills-registry.md`).
- Always the same spelling of the vault path — it is NOT `/Odsidian/.../Obsidian` (that is the top-level folder) but `<vault>/Brain/notes/skills/`. Double-check with `ls` once per session.

## Workflow (proven, reuse verbatim)

1. **Research (grounded)**: fetch the tool's real docs. `web_search` first to find the canonical repo + site + comparison pages. Then `web_extract` the specific pages (batch ≤5 URLs).
2. **Collect raw text** to `/tmp/<tool>_raw/<slug>.md` so progress survives timeouts and you can write the note in sections.
3. **Write the Obsidian note** with the fixed 10-section structure (below). In Russian. `--no-stub` discipline: only facts you actually read; cite the source under each section; secondary sources tagged "(обзор)"; reconcile conflicting numbers by citing BOTH, never averaging.
4. **Verify** with the grep block (below) — not tests.

### Keyboard-shortcut cheatsheets — ground truth is the source, not docs
If the deliverable is a HOTKEYS/shortcut cheatsheet for a tool installed on this machine, read the tool's OWN code (`hotkeys.ts`, `keybindings.json`, README keybinding table). The real map is there, not in secondary blogs or memory. Capture: (a) the platform-modifier branch (macOS = Cmd / Linux+Windows = Ctrl), and (b) editor-specific swallow (e.g. VS Code/Cursor rebinds `Cmd+G` → use `Alt+G`). Full recipe in `references/keybindings-from-source.md`.

## Source-fetching pitfall — the repeatable fix

`web_extract` on many docs sites returns `Blocked: URL targets a private or internal network address` even for public pages. That is a generic anti-bot/SSRF false positive, NOT a real block — do not conclude the site is unreachable. The deterministic fallback:

```bash
# fetch page HTML then strip <main>/<body> to text
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
curl -sL -A "$UA" --max-time 40 <url> | python3 -c "import sys,re,html; s=sys.stdin.read(); m=re.search(r'<main[^>]*>(.*)</main>', s, re.S); b=m.group(1) if m else s; t=re.sub(r'<[^>]+>',' ',b); print(re.sub(r'\\s+',' ',html.unescape(t)))"
```

Other routes that often work when HTML is client-rendered:
- GitHub repos: fetch `https://raw.githubusercontent.com/<owner>/<repo>/main/README.md` (always valid markdown).
- Mintlify/Nextra docs: try `https://docs.example.com/llms.txt` (index of all pages) and `https://docs.example.com/<page>.md`.
- The root `/` is the most-blocked URL; subpages often extract fine via `web_extract` directly.

## Standard 10-section structure (Russian)

1. **Что это** — one sentence: what the tool is and its key differentiator.
2. **Почему не X** — how it differs from the obvious alternative (Figma, pen.dev/Pencil, the proprietary version).
3. **Установка / запуск** — exact, copy-paste commands from the official source (do not invent `pnpm install`/`npm i` if uncertain — verify first).
4. **Концепты** — the native concepts (format, canvas, adapters).
5. **CLI / команды** — exact commands with flags (verbatim from docs).
6. **Возможности** — what it can produce, export.
7. **Интеграция с Hermes (⭐ always asked)** — two paths:
   - **Path 1 (via CLI)**: the tool has a headless CLI the agent can shell out to (`pen --out x.pen --prompt "..."`). State the model caveat honestly: the tool's own agent may be a proprietary model; the calling agent only forwards the prompt.
   - **Path 2 (MCP)**: add to `~/.hermes/config.yaml` `mcp_servers:`, tools become `mcp_<name>_<tool>`. Only viable if the tool exposes a runnable stdio/HTTP MCP server command.
   - **Golden rule**: check whether the tool explicitly lists **Hermes** among its supported agents/adapters — if yes, Path 1 is trivial and first-class; if no, it is a workaround.
8. **Сравнение** — vs the tool the user is moving away from (cite the comparison page, tag "(по странице сравнения)").
9. **Питфолы** — name collisions (pen.dev ≠ Penpot/Pencil Project; "Open Design" is ambiguous — pin the exact repo `owner/repo`), licensing, BYOK cost, local-first, conflicting numbers.
10. **Ссылки** — every URL used.

## Verification (grep block — run after every write)

```bash
F="/Users/dmitrypotekhin/Odsidian/obsidians/Obsidian Vault/Brain/notes/skills/<tool>.md"
test -f "$F" && echo "OK: file exists" || echo "FAIL: no file"
echo "urls=$(grep -oE 'https?://[^) ]+' "$F" | sort -u | wc -l)"
grep -iE "TODO|TBD|заглушк|PLACEHOLDER|FIXME" "$F" && echo "FAIL: placeholders" || echo "OK: no placeholders"
grep -qi "Hermes" "$F" && echo "OK: Hermes section" || echo "WARN: no Hermes"
```
Expect: `OK: file exists`, `urls` ≥ 8, `OK: no placeholders`, `OK: Hermes section`.

## Pitfalls

- Do NOT write "the site is unreachable" or "<tool> is broken" — capture the working fallback (curl/SSR parse), not the transient failure.
- Reconcile conflicting numbers from different sources (e.g. adapter counts 17 vs 21) by quoting both with the source, never picking one.
- Name collisions: pin the exact product (`pen.dev`, `nexu-io/open-design`) and warn about lookalikes (Penpot, Pencil Project, "Open Design" movement).
- The user wants a NEWBIE-level explainer (how to actually start, first-10-minutes path), not an API reference. Lead with a hand-holding walkthrough.
- BYOK / pay-per-token: the tool may be free as software but require the user's own API key or agent — state that explicitly.

## Support files

- `references/tools-notes.md` — condensed knowledge bank of researched tools (pen.dev, OpenDesign): the facts, adapter lists, and integration verdicts found this session. Reuse when the same tool comes up again.

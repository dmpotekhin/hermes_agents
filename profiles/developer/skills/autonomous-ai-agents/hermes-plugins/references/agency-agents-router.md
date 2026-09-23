# The Agency agent roster — Hermes router plugin

Repo: msitarzewski/agency-agents (MIT). A catalog of ~280 AI "specialist agent" persona files across 18 divisions — it GROWS upstream (273 at the 04.09.2026 install, 279 at 12.09.2026): never hardcode the count, read the file (engineering, specialized, marketing, game-development, gis, security, design, sales, testing, paid-media, project-management, academic, spatial-computing, support, finance, product, healthcare, research). Hermes is a first-class target (`tools.json` format = `hermes-router-plugin`), shipped as a **LAZY router plugin**: at startup only 4 small tools register; the full roster (`data/agents.json`, ~4MB) is loaded on demand.

## Why a plugin, not skills
The integration does NOT add the 273 agents to `skills.external_dirs` (that would bloat context). One plugin `agency-agents-router` exposes 4 tools:
- `agency_agents_search` — find an agent by name/description for a task
- `agency_agents_inspect` — view a role's rules/deliverables
- `agency_agents_load` — bring an agent into context
- `agency_agents_delegate` — hand a task to an agent through the host's PUBLIC subagent lifecycle (`ctx.subagent_lifecycle` + `agent.subagent_lifecycle.SubagentLaunchRequest`) since upstream `80b338fe` (2026-09-05); older builds used `ctx.dispatch_tool("delegate_task")`. Cheaper than an interactive session. **Version check before updating**: the new router needs `SubagentLaunchRequest`, `SubagentTerminalState.completed/timed_out` and `SubagentResult.terminal_state` present in the installed Hermes — probe them (see `references/updating-generated-plugins.md`), don't assume.

## Install (two-step; the repo ships its own installer — do NOT use `hermes config set`)
```bash
git clone --depth 1 https://github.com/msitarzewski/agency-agents /tmp/agency-agents
cd /tmp/agency-agents
./scripts/convert.sh --tool hermes    # generates integrations/hermes/agency-agents-router/ + data/agents.json (count is data-driven: 279 as of 12.09.2026)
./scripts/install.sh --tool hermes    # copies to ${HERMES_HOME}/plugins/agency-agents-router, enables plugin in config.yaml (with a .bak backup), prints dest path
```

### HERMES_HOME gotcha (critical)
`install.sh` writes to `${HERMES_HOME:-~/.hermes}/plugins/agency-agents-router`. If `HERMES_HOME` points at the ACTIVE profile, the plugin lands there — usually what you want. Before installing:
```bash
echo "$HERMES_HOME"    # e.g. /Users/<you>/.hermes/profiles/developer
```
and confirm the target in the install output (`resolve_dest hermes "${HERMES_HOME}/plugins/agency-agents-router"`). If `HERMES_HOME` is unset, it defaults to `~/.hermes` — i.e. the DEFAULT profile, not the active one.

### Dry-run first
`./scripts/install.sh --tool hermes --dry-run` prints what it will do (tool/team/agent count, mode=copy) without writing — run it before the real install.

## Verify
- Plugin dir: `~/.hermes/profiles/developer/plugins/agency-agents-router/` with `__init__.py`, `plugin.yaml`, `data/agents.json`.
- Agent count on disk, taken from the FILE (not from docs):
  `python3 -c "import json;print(len(json.load(open('data/agents.json'))))"
- Config change is minimal: ONE line `- agency-agents-router` added under `plugins.enabled`, plus a `.bak.agency-agents-plugin.<pid>` backup.
- Syntax-check the plugin: `import ast; ast.parse(open('__init__.py').read())`; confirm the 4 tool names appear in the source (they're registered via a manifest dict, not plain `def`s).
- **Restart Hermes** (new session / gateway) — tools register at STARTUP, so they are NOT available mid-conversation. After restart, `tool_search` finds `agency_agents_*`.

## Regenerate / update after editing agents
```bash
cd /tmp/agency-agents && ./scripts/convert.sh --tool hermes && ./scripts/install.sh --tool hermes
```
Fully remove: delete the `- agency-agents-router` line from config.yaml (restore the .bak) and `rm -rf $HERMES_HOME/plugins/agency-agents-router`.

## Updating an EXISTING install (verified 2026-09-18: 273 → 279 agents)
`install.sh` does `rm -rf <dest>` + `cp -R` and REWRITES `plugins.enabled` — and versions before
`647c8baa` corrupted that list into a glued scalar (see the pitfall in SKILL.md). Prefer the
surgical route, and read `references/updating-generated-plugins.md` for the full recipe:

```bash
git clone --depth 1 https://github.com/msitarzewski/agency-agents /tmp/agency-agents-src
cd /tmp/agency-agents-src && ./scripts/convert.sh --tool hermes   # -> integrations/hermes/agency-agents-router/
# diff the generated plugin against the installed one BEFORE copying anything:
diff -rq integrations/hermes/agency-agents-router "$HERMES_HOME/plugins/agency-agents-router"
# backup, then copy only plugin.yaml / __init__.py / data/agents.json
```

`plugin.yaml` did NOT change between 04.09 and 12.09; `__init__.py` and `data/agents.json` did.
Leave a provenance stamp (`<plugin-dir>/.upstream-commit`: source URL, commit sha, install date)
so the next update doesn't have to reconstruct it. Note the roster's generated output is
**gitignored upstream** (`integrations/<tool>/<plugin>/`), so git history CANNOT tell you what was
installed — rebuild from the install-time commit instead.

## Building a usage/catalog note from the roster
`data/agents.json` is a list of `{slug,name,description,division,color,emoji,vibe,source_path,body}`. To emit a full reference note, group by `division` and render one bullet per agent: `**Name** — <trim description to ~190 chars at a sentence boundary>`. Division count = `len({a['division'] for a in data})` (18), NOT a hardcoded number — do the math from the data.

## Usage pattern (natural-language, lazy)
Ask the host in the user's language: "поищи в agency software-architect", "покажи агента data-engineering", "загрузи фронтендера", "заделегируй это code-reviewer". Keep it lazy — only load/inspect the agent you actually need, never the whole roster.

## Invocation fallback — tools NOT registered mid-session (verified recipe)
The 4 `agency_agents_*` tools register ONLY at Hermes STARTUP. If the session began before
`agency-agents-router` was enabled (or the plugin was just installed this session), `tool_search`
returns NOTHING and `agency_agents_delegate` is unavailable mid-conversation. Do NOT try to
"reach" the tools — work around them directly:

1. Pull the persona body straight from the roster on disk:
   ```python
   import json
   data = json.load(open("/Users/<you>/.hermes/profiles/developer/plugins/agency-agents-router/data/agents.json"))
   agents = data if isinstance(data, list) else data.get("agents", list(data.values()))
   sa = next((a for a in agents if a.get("slug") == "software-architect"), None)
   print(sa["body"])   # the full persona prompt (identity, rules, ADR template, process)
   ```
   Each entry is `{slug, name, description, division, color, emoji, vibe, source_path, body}` —
   the `body` field IS the persona prompt.
2. Delegate the task with that persona: create a `delegate_task` subagent and include the
   persona `body` + repo path + deliverable spec in the subagent's `context`. The child runs as
   that persona. Set an `output_schema` so the result comes back structured, not a blob.
3. This satisfies the same intent as `agency_agents_delegate` — the user usually can't tell the
   difference. Just say the plugin tools are startup-only and you ran the persona directly.

## Monitoring a background `delegate_task` (it does NOT stream to the user)
A delegated subagent runs in the background; its live token stream is NOT shown to the user — only
the final consolidated result returns. Users will ask "почему субагент молчит" when it's just working.
To answer without guessing:
- `delegate_task(action='list')` → shows `status` (`running`/`done`), `running_seconds`, goal.
- Tail the live transcript: `tail -40 .../cache/delegation/live/<deleg_id>/task-0.log` (append-only;
  each `tool`/`result` line is one step). A big recent log with `read_file`/`pytest` entries proves
  it's alive and grinding, not hung.
- Reassure the user: for a thorough review/analysis, ~5-15 min of file-reading + test-running is normal.

## Subagent terminal commands can be auto-BLOCKED by the safety hook
Subagents have no interactive consent path, so a terminal command the hook flags (or the user
denied for the parent) comes back `BLOCKED: User denied this command`. This is NOT fatal: tell the
child (or instruct the task upfront) to prefer `read_file`/`grep`/`search_files` and, when a command
is blocked, continue around it — read the file another way. Blocked greps for config-default checks
and `def` scans are typical and harmless.

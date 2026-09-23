# Agency Agents (msitarzewski/agency-agents) — knowledge bank

Evaluated 2026-09-04. Verdict: adopt (developer profile). MIT.

## What it is
Catalog of ~273 AI-agent personas across 18 divisions (engineering, design, product,
testing, security, marketing, finance, gis, ...). Each is a `.md` with frontmatter
(name, description, emoji, vibe) + body (Identity/Memory, Core Mission, Critical Rules,
Deliverables, Success metrics). Persona **prompts**, not code / not new capability.

## Hermes integration (why it matters for us)
- Build + install:
  ```bash
  ./scripts/convert.sh --tool hermes   # generate integrations/hermes + data/agents.json
  ./scripts/install.sh --tool hermes   # copy plugin + enable in Hermes config
  ```
- Installs a single **lazy router plugin** `agency-agents-router`; it is NOT added to
  `skills.external_dirs`, so no context bloat. The full roster (273) lives in
  `data/agents.json` and is searched/loaded on demand.
- 4 tools: `agency_agents_search(query, division?, limit?)`, `agency_agents_inspect`,
  `agency_agents_load`, `agency_agents_delegate` (routes through Hermes `delegate_task`,
  so a £specialist can run as a ~15x-cheaper subagent).
- Installer path: `${HERMES_HOME:-~/.hermes}/plugins/agency-agents-router`. On the dev
  profile `HERMES_HOME` is already the profile dir, so it lands in the ACTIVE profile
  with NO env/override needed — check `echo $HERMES_HOME` first.
- Restart Hermes / start a new session after install so the tool schemas load.

## Usage
Natural language in-session: "search the agency for software-architect and load it",
"delegate code-reviewer on this diff", "inspect the gis specialists". Keep routing lazy
— do NOT ask to preload the whole roster as skills.

## Notes / risks
- Persona = process/style (how the agent thinks, what it ships), not new tool access.
- opencode quirk drops >119 agents — irrelevant for Hermes.
- Re-clone / re-run install periodically so tool schemas stay current.

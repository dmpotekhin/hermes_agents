---
name: coding-agent-setup
description: "Configure OpenCode/KiloCode with custom LLM providers."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [opencode, kilocode, deepseek, agents-md, vibe-coding, config]
    related_skills: [opencode, graphify-knowledge-graph, test-driven-development]
---

# Coding Agent Setup (OpenCode / KiloCode)

Use when the user wants to configure CLI coding agents — OpenCode or KiloCode —
for vibe-coding on their own machine / work machine: custom LLM provider
(corporate DeepSeek, OpenAI-compatible gateway), context-window limits, and
project memory via `AGENTS.md` so context survives session restarts.

This is SETUP/config work — distinct from the `opencode` skill, which covers
delegating coding tasks to an already-configured OpenCode CLI.

## When to Use

- "сделай настройки для opencode/kilocode"
- User has a corporate/private LLM endpoint (e.g. DeepSeek 4 Flash, 100K ctx)
  and wants to vibe-code (usually autotests) with it
- User already has an `AGENTS.md` and wants it wired into the agents
- Any request to make context "не терялся" across agent sessions

## Deliverable Shape

Build a portable package in a folder (e.g. `~/work-ai-setup/`):
- `opencode.json` — OpenCode provider + model limits + compaction + instructions
- `kilo.jsonc` — KiloCode rules/instructions
- `AGENTS.md` — project memory: role, TDD, test conventions, Progress/ADR sections
- `graphify.sh` — dependency-graph runner (see graphify-knowledge-graph)
- `README.md` — copy-and-paste checklist for the target machine

Templates for all files live in `templates/` of this skill — copy and modify:
`opencode.json`, `kilo.jsonc`, `AGENTS-java.md` (rename to AGENTS.md),
`graphify.sh`, `README-checklist.md`.

## OpenCode: custom DeepSeek provider

`opencode.json` (project root or `~/.config/opencode/`):

```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "deepseek/deepseek-v4-flash",
  "small_model": "deepseek/deepseek-v4-flash",
  "provider": {
    "deepseek": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "DeepSeek",
      "options": {
        "baseURL": "https://api.deepseek.com/v1",
        "apiKey": "{env:DEEPSEEK_API_KEY}"
      },
      "models": {
        "deepseek-v4-flash": {
          "name": "DeepSeek V4 Flash",
          "limit": { "context": 100000, "output": 8192 }
        }
      }
    }
  },
  "compaction": { "auto": true, "prune": false, "reserved": 20000 },
  "instructions": ["./AGENTS.md"]
}
```

Key points:
- `npm: "@ai-sdk/openai-compatible"` for OpenAI-compatible gateways; use
  `"@ai-sdk/deepseek"` for official DeepSeek API.
- `limit.context` MUST match the real window (e.g. 100000) — compaction
  computes its trigger from it.
- `reserved: 20000` keeps headroom for the response.
- `small_model` = same cheap model so titles/summaries don't burn context.
- `instructions` points at AGENTS.md → project memory injected every session.
- Verify in TUI with `/models` (should show `deepseek/deepseek-v4-flash`).

## KiloCode: provider via UI + kilo.jsonc

- Provider: UI only — Settings → Providers → DeepSeek (paste key), or
  "OpenAI Compatible" for a corporate gateway (baseURL + key).
- `kilo.jsonc` (project root):
```jsonc
{
  "instructions": ["./AGENTS.md", ".kilo/rules/*.md"],
  "compaction": { "threshold_percent": 80 }
}
```
- Kilo auto-discovers instruction files at project root via findUp:
  `AGENTS.md` (primary), `CLAUDE.md` (compat), `CONTEXT.md` (extra context).
- Context condensing is AUTOMATIC; threshold_percent is optional (1–100).
- Docs paths: kilo.ai/docs/customize/custom-rules, /customize/agents-md,
  /customize/context/context-condensing, /ai-providers.

## AGENTS.md — the project memory

AGENTS.md is the piece that survives compaction and session restarts. Structure:

1. **Роль** — one line about the agent's role (e.g. senior Java QA engineer).
2. **TDD-цикл** — RED → GREEN → REFACTOR → COMMIT, forbidden actions.
3. **Конвенции тестов** — language/framework specific (see Java below).
4. **Память между сессиями** — agent must append 1–3 lines to a `Progress`
   section at end of session; read `Progress` + `Решения (ADR)` before big tasks;
   suggest restart when context >70K of a 100K window.
5. **Graphify** — read `graphify-out/GRAPH_REPORT.md` before refactors,
   regenerate after structural changes (wires in the dependency graph).
6. **Стек** — fill-in placeholders: language/version, build tool, test command,
   single-test command, what is covered, what not to touch.

Then literal sections: `## Progress` (comment placeholder) and
`## Решения (ADR)` (key decisions + why).

### Java autotest conventions (user's stack — JUnit 5)

- One test = one scenario; `@DisplayName("...")` for human-readable names.
- JUnit 5: package-private test methods, `@Test`, `@ParameterizedTest` +
  `@MethodSource`, `@Tag("slow")`, `@Timeout`.
- AssertJ (`assertThat(x).isEqualTo(...)`, `assertAll(...)`) over JUnit asserts.
- Mockito (`@ExtendWith(MockitoExtension.class)`, `@Mock`/`@InjectMocks`) for
  boundaries; no real network/timing.
- Testcontainers (PostgreSQL, Kafka, Redis) for integration — never local
  instances or hardcoded ports.
- Maven: `mvn test -Dtest=ClassName#method`; Gradle:
  `./gradlew test --tests "*.ClassName.method"`. Don't run `mvn clean` without
  reason.

## Pitfalls

- web_extract is often blocked on opencode.ai / kilo.ai docs → curl with
  `-A "Mozilla/5.0 ..."` + python3 strip HTML (see external-repo-research).
- Kilo docs navigation is JS-rendered; grep `href="/docs/..."` from the
  raw HTML to find real page paths.
- `kilo.jsonc` validation: strip `//` comments first, then parse as JSON.
- read_file may misdetect UTF-8 README with em-dashes as binary — use
  `file`/`cat -n` via terminal instead.
- DeepSeek corporate endpoints are usually OpenAI-compatible: the
  `@ai-sdk/openai-compatible` route is the safe default.

## Verification

Ad-hoc script (no test runner exists for configs): validate opencode.json as
strict JSON, kilo.jsonc as comment-stripped JSON, `bash -n` on graphify.sh,
`stat` for executable bit. Write the script with write_file (shell printf
escaping mangles `\\n` regexes — that produced a false negative once).

## Related

- `opencode` skill — delegating work to a configured OpenCode CLI.
- `graphify-knowledge-graph` — generating the dependency graph AGENTS.md points at.

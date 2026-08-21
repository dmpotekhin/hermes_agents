# Graphify token economics (measured 2026-08-19)

Real numbers from travel-visualizer (77 files: 49 code, 9 docs, 6 unclassified). Used to answer
"сколько токенов graphify экономит при разработке" honestly — the vendor's 71.5x claim is NOT
the right number to quote for AST-only code graphs.

## Measured sizes

| Artifact | Size | Tokens (≈ chars/4) |
|---|---|---|
| Project code (excl. .venv) | 309 KB | ≈ 77K |
| Average code file | 5.6 KB | ≈ 1.4K |
| graph.json (FULL graph) | 487 KB | ≈ 122K |
| GRAPH_REPORT.md | 9 KB | ≈ 2.2K |
| graph.html | 417 KB | (visual, don't feed to LLM) |

## The critical rule

NEVER read graph.json wholesale into context — at 122K tokens it costs MORE than reading the
whole codebase. Always go through the CLI query commands (`query`, `explain`, `god-nodes`,
`path`, `affected` with `--graph <path>/graphify-out/graph.json`), which return 0.5–2K-token
subgraph slices. The graph pays off only through these queries.

## Savings by scenario (realistic, AST-only)

- Onboarding a project after a gap: 12–25K → 4–8K tokens (3–5x). One-time purchase — graph.json
  persists across sessions, so re-onboarding is ~0.
- Point work (fix/extend function X): 40–70% per lookup (explain instead of reading file + deps).
- Architecture questions ("what connects A to B"): 3–5x (query instead of reading 3–5 files).
- Cross-session: new session answers via query without re-reading code — biggest long-term win.
- Typical dev session (≈100K context): ~30–50% saved, provided the graph is used.

## When it pays off

- Projects ≥ ~15–20 files worked on across sessions with gaps. Marginal on small one-off scripts.
- Vendor benchmark 71.5x is on a mixed corpus (code + papers + images) WITH LLM concept
  extraction — not applicable to `--code-only` runs.

## Verified command quirks (see also graphify-knowledge-graph skill)

- Flags AFTER the path: `graphify <path> --code-only` (not before — errors "unknown command").
- `cluster-only --no-label --no-viz` = report only, no LLM naming, no html. Rerun without
  `--no-viz` to regenerate graph.html (open for the user with `open .../graphify-out/graph.html`).
- Vendors (bundled libs like gif.js, mp4-muxer) appear as their own communities and god nodes —
  expected; mention when reporting so the user doesn't think their code has a GIFEncoder hub.
- `DEEPSEEK_API_KEY` is a first-class backend; without any key use `--code-only` (docs/images
  silently skipped).

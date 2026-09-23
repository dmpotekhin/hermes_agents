# Tri-Face Carousel Factory (ADR-107) — architecture & phase record

Feature goal: one carousel engine, three verticals — **Travel** (photo/route/story),
**QA** (bugs, flaky tests, CI failures, issues/PRs, postmortems), **Vibecoding** (AI
sessions, prompts, local LLMs, "built it in an evening" stack posts). Primary input of
v1 is a **URL or a GitHub item** (repo / issue / PR / discussion) → a 6-slide carousel
(768×1376 JPG, 9:16) for TikTok + Instagram, with human approval before publishing.

## Layering (the part that must not drift)

```
core/models.py      canonical enums + pydantic models  (every layer already imports this)
core/database.py    the ONLY module with SQL (DDL + CRUD + row->model converters)
core/config.py      CarouselConfig / CarouselResolutionConfig / CarouselUrlSourceConfig + Secrets
core/exceptions.py  CarouselError(TravelBlogError), SourceResolutionError, InsufficientSourceDataError
modules/carousels/
  enums.py, models.py       thin re-export facades (feature-flavoured names) + enum_text()
  state_machine.py          transitions + publish guard (require_publish_allowed,
                            can_publish, should_auto_approve, plan_next, describe)
  database_helpers.py       repository facade — only delegates to Database methods
  service.py                CarouselFactory: create_job, get_bundle, transition,
                            approve/reject, ensure_publishable, status_report, edits,
                            research, draft_narrative, plan_slides, render_slides,
                            verify_slides
  sources/                  base, detect, html, url, github, mock, registry
  vertical_profiles.py      per-vertical 6-beat sequence, hook families, tone, text budgets
  fact_guard.py             "does the source actually say this?" (normalised containment)
  hooks/engine.py           candidate hooks, each with source_support
  narrative/planner.py      SlidePlanner: material cursor -> CarouselSlide rows
  render/                   fonts, base (ABCs), pillow_renderer, providers, verification
```

`core` never imports `modules` — that is why the canonical types live in `core/models.py`
and the feature package re-exports them (same reason as the ADR-106 storyboard models).
SQL stays in `core/database.py`; `database_helpers.py` is a naming facade, not a second
SQL layer.

## Schema (10 additive, idempotent tables appended to `_SCHEMA`)

`carousel_jobs` (+ audit columns `approved_by TEXT NOT NULL DEFAULT ''`, `approved_at TEXT`),
`carousel_sources`, `carousel_slides` (quoted `"order"` column), `carousel_hook_candidates`,
`carousel_publications`, `carousel_metrics`, `carousel_learnings`
(unique key `(scope_type, scope_value, metric_name)`), `carousel_templates`, `qa_artifacts`,
`vibecoding_sessions`.

Indexes (assert on these exact names — read them from the DDL, do not invent them):
`idx_carousel_jobs_status|_vertical|_source_type|_created`, `idx_carousel_slides_job`,
`idx_carousel_hooks_job`, `idx_carousel_publications_job`,
`idx_carousel_metrics_publication|_lookup`, `idx_carousel_learnings_scope`,
`idx_carousel_sources_job`.

Dropped/parked name: there is **no** carousel `ready` status and no separate table for
approval audit — approval is recorded on the job row (deterministic, no extra join).
Legacy tables to assert coexistence against: `cities, photos, drafts, published,
 pending_tasks, vibecoding_posts, storyboards, narrative_beats, storyboard_shots`
(the publishing table is `published`, NOT `publications`).

`_CAROUSEL_SOURCE_WRITABLE` whitelists writable source columns; dynamic UPDATEs go through
such a whitelist, never through f-string column names.

## State machine & the human-in-the-loop guard

`_CAROUSEL_TRANSITIONS` + `carousel_transition()` / `carousel_next_states()` in
`core/models.py`; the DB layer calls `m.carousel_transition(...)` and generic updates reject
`status` with `ValueError` (the only way to move a job is the validated transition).
`revision_allowed`: `NEEDS_REVISION → False`, `VERIFYING → True`, `PENDING → False`.

Publishing rules enforced in `modules/carousels/state_machine.py` and exposed on the
service: `require_publish_allowed(job)`, `can_publish(job)`,
`should_auto_approve(mode, *, require_human_approval)` — auto-approval needs
**both** `full_autonomous` AND supervision explicitly switched off. `approve()` writes
`approved_by` + `approved_at` before the transition, so the audit trail cannot be skipped
by a failed transition afterwards.

Pipeline shape: SOURCE → RESOLVER → VERTICAL (detect or user override) → RESEARCH CONTEXT
→ HOOK ENGINE → NARRATIVE → SLIDE PLAN JSON → RENDERER → QA/VERIFY → DRAFT → HUMAN
APPROVAL → UPLOAD-POST → ANALYTICS → LEARNINGS.

## Config & secrets

`CarouselResolutionConfig(width=768, height=1376)`, `CarouselUrlSourceConfig`,
`CarouselConfig(renderer="pillow", dry_run=True)`; `Secrets.uploadpost_token`,
`Secrets.uploadpost_user`, `Secrets.github_token` — env only, values never printed.
Documented in `.env.example` (as `[REDACTED]`) and `config.yaml` (block style!).
`dry_run=True` is the default: later phases placehold Gemini/Upload-Post instead of
calling them (`renderer="html"` is not implemented yet → the factory raises
`CarouselError` rather than silently substituting another renderer).

## Phase record (branch `feature/tri-face-carousel-factory`, all scanned + committed)

| phase | commit | content | suite |
|---|---|---|---|
| baseline | `0b5a536` | before the feature | 131 |
| 1 core | `26d36f5` | enums/models/10 tables/state machine/service skeleton | 204 |
| 2 sources | `01b4b7e` | URL + GitHub resolvers, detection, registry | 272 |
| 3 narrative | `ce93e70` | hook engine, planner, fact guard, vertical profiles | 298 |
| 4 render | `a55eee0` + `0c61393` | Pillow renderer, verifier, targeted regeneration | 326 |
| 5 publish | `ad3e63e` | approval gate, Upload-Post publisher, 15 API routes | 356 |
| 6 analytics | `1d9eeb0` | collectors, rate-based score, learnings, scheduler step | 382 |
| 7 ui+cli | `091ba21` (+ docs `4843dfd`) | Streamlit «🎠 Carousels» tab, `carousel` CLI | 392 |
| docs | `4de7943` | ADR-107 registered in the README ADR table (it had stopped at 106) + stale "130 passed" note refreshed; pushed HEAD | 392 |

Phase 1 tests: `tests/test_carousel_{models,state_machine,database,service}.py`.
Phase 2: `tests/test_carousel_sources_{url,github,detect}.py` + `test_carousel_research.py`
(68 tests, all offline). Phase 3: `test_carousel_{hooks,planner,planning}.py` (26).
Phase 4: `test_carousel_render.py` + `test_carousel_rendering.py` (25).

### Phase 2 — resolvers

`BaseSourceResolver` + `resolve_registry`; URL = `httpx` + stdlib `HTMLParser` (headings,
paragraphs, quotes, code, images, theme colours, canonical URL), GitHub = REST
(repo/issue/PR/release) + GraphQL (discussion). Metrics/diffs come ONLY from the API
response; a discussion without a token yields a warning + `confidence 0`, never invented
content. Unreadable source → `SourceResolutionError` → job FAILED. `sources/mock.py`
returns an empty context with a warning ("honest by construction").

**Testing resolvers offline (do this, never hit the network):** build the resolver with an
injected `httpx.AsyncClient(transport=httpx.MockTransport(handler))`; the handler switches
on `(request.method, request.url.path)`, asserts headers (`Authorization`), and returns
`httpx.Response(200, json=..., request=request)`. 300+ line resolver files were covered
this way with zero network and zero flakiness.

### Phase 3 — deterministic narrative

Hooks exist only when a source line matches the family (`hook_categories_for`); every hook
carries `source_support`. `fact_guard` drops unsupported text with a warning. Profile text
budgets are what protects the bottom 20% at planning time.
`SlidePlanner._next()/_pick()` hand out each source fact **once** before cycling, and the
chosen hook's `source_support` line is reserved up front (`_mark_used`) — otherwise the
hero sentence reappears on slide 3 and the carousel reads as a loop.

### Phase 4 — render + verify

`PillowSlideRenderer`: 768×1376 JPG, gradient/vignette canvas from the source theme colour
(or a local photo / Gemini background when a key exists), per-attempt font auto-shrink,
hard clamp so no text box enters the bottom 20% (TikTok overlay), code drawn line-by-line
in a mono font straight from the snippet, metrics only when `is_verified`, sha256 in the
result plus a `slide_NN.layout.json` sidecar listing every text box and its y-range.

`SlideVerifier` re-opens the produced file with Pillow and checks: exists, 768×1376,
JPEG, bottom-zone, alt text, source refs, minimum font size, code integrity (rendered
lines must match the snippet), fact support. It never trusts in-memory state — the sidecar
is the contract that survives process boundaries. Failures on a subset of slides drive
**targeted** re-render of just those slides, up to `max_regeneration_attempts` (2), then
`NEEDS_REVISION` with the failing slide numbers in the job warnings.

Offline end-to-end proof (travel face, local HTML, no network):
`PYTHONPATH=. .venv/bin/python /tmp/carousel_e2e_demo.py` → `verified`, 6/6 slides passed,
real files in `/tmp/carousel_demo/out/job_1/slide_0N.jpg` (+ `.layout.json`, ~46–68 KB each).
Run an e2e like this per phase — **it found both Phase 4 bugs, the unit tests did not.**

### Phase 5 — approval + publishing

`modules/carousels/publishing/`: `BaseCarouselPublisher.publish(request) -> PublishResult`,
`MockCarouselPublisher` (dry run → `PublicationStatus.MANUAL`, uploads nothing),
`UploadPostPublisher` (`POST /api/upload_photos`, multipart `photos[]` / `platform[]`,
`Authorization: Apikey ***`, retries only on network errors, a status query returns an
empty map rather than rounded-off numbers), selection in `publisher_for(settings, secrets)`
(`base_url` comes from `settings.upload_post.base_url`, which is what makes a loopback
stand-in possible in tests).

Autonomy needs **two** switches: `autonomy.mode=full_autonomous` **and**
`require_human_approval: false` (`test_full_autonomy_needs_two_switches`). Publishing
without approval raises `PublishNotApprovedError` → 409 in the supervised API.

**Idempotency is one publication per `(request_id, platform)`**, not per `request_id`: a
multi-platform Upload-Post answer returns ONE request id for two posts, so a
request_id-only unique index makes the second platform fail. Partial unique index
`idx_carousel_publications_request_id ... WHERE status='published'`; re-publishing reuses
the stored rows. The old index had to be dropped lazily — a `DROP INDEX`/DDL on every start
held the DB lock and broke `test_api.py::test_calendar` ("database table is locked").

### Phase 6 — analytics + learnings

`modules/carousels/analytics/`: `base.py` (`PlatformMetrics`, `is_empty()`),
`collectors.py` (live collector + offline stand-in; parses `1.2K`-style values, invents
nothing), `scoring.py` (weighted sum of **rates**, weight redistributed when a metric is
missing, reject penalty), `learnings.py` (`LearningStore`, `Recommendation`,
`latest_metrics_per_platform`, `cohort_for`). An empty provider response stays empty —
no zeros, no averages (a live E2E asserted a job with a bare status payload keeps 0 metric
rows plus an explicit warning).

**Single source of truth for the score.** `refresh_learnings` first used a cohort that
included the job being scored and a different minimum-sample rule from `score_job`, so the
same carousel showed two different scores (0.2774 in the learnings vs the per-job values).
Fixed by extracting `cohort_for(outcomes, job_id)` (self always excluded) and using it in
both paths; a regression test compares the learnings `carousel_score` row with the mean of
`score_job`. Any "explainable score" feature needs this test.

### Phase 7 — Streamlit page + CLI

`ui/carousel_page.py` (tab «🎠 Carousels»: Hub with the ten stages, per-slide preview,
approval queue where a reject demands a reason, analytics, learnings) registered in
`ui/dashboard.py`; `cli.py carousel <action>` (create/list/status/research/draft/plan/
render/verify/submit/queue/approve/reject/publish/collect/score/refresh/advice/metrics).

Two flags make offline work honest: `--db PATH` walks an isolated database (experiments
never touch the app DB) and `--fixture PATH` feeds a JSON source context to `research` —
facts the operator wrote down, instead of a fetched page pretending to be one. In dry-run
the mock resolver returns an empty context, so `verify` legitimately fails and `submit` is
refused: the honest path through the CLI needs a fixture.

Rendered JPGs land in `public/carousels/` — **gitignore it** (regenerate with
`carousel render`); a CLI walk otherwise commits ~400 KB of demo images.

That whole walk is scripted: `scripts/carousel-cli-walk.sh [fixture.json]` runs create →
research → draft → plan → render → verify → submit → queue → approve → publish → collect on a
fresh `/tmp` DB, asserts 6 JPG landed on disk, and prints each stage's JSON so the honest
dry-run outcomes (`manual` + empty `request_id`, 0 metrics plus a warning, no score without
metrics) are visible rather than asserted from memory. The fixture shape it expects is
`templates/carousel-source-context.json`.

## Pitfalls that cost real time here

1. **`str(enum)` leaks into TEXT columns.** `str(CarouselVertical.QA)` is
   `"CarouselVertical.QA"`, which pydantic then rejects on read. A status-only helper
   (`status_value`) is not enough: store every carousel enum through a generic
   `enum_text(value)` (lowercase value or the `Enum.value`), and keep `SLIDE_TYPE_ALIASES`
   built on top of the canonical map.
2. **Sync renderer + async provider = `RuntimeError: This event loop is already running`**
   (`asyncio.run` inside a running loop, e.g. called from an async service). Split the entry
   points: `BaseSlideRenderer.render_async()` awaits the provider (the service always awaits
   it), while the plain `render()` paints the deterministic fallback and says so in
   `warnings`. Do not paper over it with `run_until_complete`.
3. **A verifier that only inspects in-memory objects verifies nothing.** Re-read the artifact
   from disk (Pillow + the layout sidecar) in the verifier; that is what catches wrong size,
   broken format and text sneaking into the safe zone.
4. **"All text must be source-supported" false-fails the CTA.** The last slide's wording
   comes from the vertical profile by design, so it is explicitly claim-free: the verifier
   skips the support check for it and instead fails if it carries bullets/body that would
   need a source.
5. **A test fixture that omits an optional field hides a whole code path.** A `slide_payload`
   helper without `code_json` meant no code box was ever drawn and the code-integrity check
   silently skipped — two tests failed only after the fixture gained the field. Exercise every
   optional field at least once.
6. **A service method's return type is not uniform — check it, don't assume a job.**
   `plan_slides`/`render_slides`/`publish` return `CarouselBundle`, `verify_slides` returns
   `List[VerificationReport]`, the rest return `CarouselJob`. A CLI/UI layer that does
   `result.status.value` on all of them crashes ("*Bundle has no attribute status"); branch
   on `isinstance(result, CarouselBundle)` / a list.
7. **The analytics honesty rule needs a live test, not just unit tests.** The first E2E that
   published four carousels to a local stand-in and read the numbers back is what caught the
   self-referential cohort. A unit fixture is too tidy for that class of bug.
8. **Long `git commit -F - <<'EOF'` heredocs get truncated in this profile** — two commits
   ended up with a literal `...(truncated)` in the message. Write the message to a file with
   `write_file`, then `git commit -F /tmp/msg.txt`. To repair: `git reset --soft <parent>`,
   then re-commit the same paths (`git commit -F msg.txt -- <paths>`) — verified to leave the
   trees byte-identical (`git diff --stat <old> <new>` empty).
9. **`write_file` with a relative path can land outside the project** (a target was created at
   `.../projects/dmitrypotekhin/projects/travel-blog-app/...`). Always pass an absolute path
   to `write_file`/`patch`; if a bad tree appears, `ls` both paths first, then ask the user for
   consent before `mv` + `rm -rf`.

## Where the feature stands

Phases 1–7 plus the ADR-107 doc fix are committed and **pushed** on
`feature/tri-face-carousel-factory` — 11 commits ahead of `origin/main`, pushed HEAD
`4de7943`, suite **392 passed**.

**Proof of a push is the remote ref, not the push command's exit code.** Read it back and
compare with the local head:

```bash
git rev-parse HEAD
git ls-remote origin refs/heads/feature/tri-face-carousel-factory | cut -f1
```

The two SHAs must be identical (they were: `4de7943725e5698616ad8e62088e7848a9b6f093`), and
`git status -sb` then shows the branch without `[ahead N]`. A PR was NOT opened — offer it,
do not assume consent for a public action. Verified beyond unit tests: an offline CLI walk on an isolated
DB reached `awaiting_approval → approved → published (manual, empty request_id)`, and a live
analytics run over real loopback HTTP (four carousels, a local stand-in of
`api.upload-post.com`) exercised the honest-metrics path and exposed the two-scores defect.
Still open if the user asks for more: an actual `git push` / PR, and exercising the
Streamlit page in a live browser (only the import/step contract is covered by tests).

## Hard rules carried into every phase

- Never invent facts, metrics, code, quotes or dates: every technical pixel comes from a
  source excerpt, otherwise the slide is flagged `low_confidence` and needs human input.
- Gemini may only produce backgrounds/illustrations — never code, numbers, logs, diffs,
  API names or technical diagrams. Those render deterministically (HTML/CSS/Pillow).
- Slides: exactly 6, 768×1376, **JPG** (TikTok rejects PNG), no text in the bottom 20%,
  alt text on every slide.
- QA/Vibecoding: accuracy beats beauty.
- Commit only after a full green suite + `compileall` + `scan_credentials.py --staged` exit 0.

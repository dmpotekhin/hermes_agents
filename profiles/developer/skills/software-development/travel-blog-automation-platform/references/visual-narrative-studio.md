# ADR-106 Visual Narrative Studio — worked example of adding a feature

Verified 2026-09-18 on `/Users/dmitrypotekhin/projects/travel-blog-app`.
Result: 22 files, +3727 / −17, commit `e311956`, full suite **81 → 130 passed**,
`compileall` clean, end-to-end smoke green. Use this as the concrete shape of the recipe in
`extending-content-types.md`.

Goal: a visual-narrative layer between AI photo analysis and platform content — narrative
arc, emotional journey, storyboard (ordered shots, captions, alt-texts, crop/focus, pacing),
accessibility + cultural-sensitivity notes.

## Pipeline placement (backward-compatible)

```
PHOTO SELECTION → AI IMAGE ANALYSIS → [VISUAL NARRATIVE STUDIO] → BASE STORY → PLATFORM CONTENT
```

- No new city status: the step runs inside `process_city` (`modules/content/engine.py`),
  the city machine stays `QUEUED → PROCESSING → DRAFTED/ERROR`.
- `generate_base_story(city, photo_facts, narrative_block: str = "")` appends the rendered
  storyboard block to the existing user prompt (default arg → old callers unaffected).
- The human gate lives on the storyboard's own machine
  (`draft → approved → archived` in `core/models.py`); `visual_narrative.require_approval`
  (default **false**) is the only way to make platform content wait, so the default
  pipeline is unchanged.
- `_build_visual_narrative()` returns `""` when: disabled, `city.id is None`, no photos,
  approval required but missing, or the studio raised — and logs a warning. Never fatal.

## Files

New: `modules/narrative_prompts.py` (prompt text/JSON contract as data),
`modules/narrative_heuristics.py` (pure logic: canonical arc, required beats, pacing,
crop/focus, alt-text validation, `ensure_arc` invariants, offline `local_plan`),
`modules/visual_narrative_studio.py` (service), `ui/storyboard_page.py`,
`tests/test_storyboard_models.py`, `tests/test_visual_narrative_studio.py`,
`tests/test_storyboard_api.py`.

Changed: `core/models.py` (enums + transition table + entities), `core/database.py`
(3 tables + CRUD + converters + whitelists), `core/config.py` + `config.yaml` +
`.env.example`, `core/exceptions.py` (`StoryboardValidationError` carrying `issues`),
`modules/ai/{base,mock,registry}.py`, `modules/content/engine.py`, `app.py`,
`ui/dashboard.py`, docs.

## Surfaces

- AI: `BaseAIProvider.generate_visual_narrative_plan(context, *, max_photos=)` (default
  implementation: build prompt → `generate_text()` → extract JSON object → map to domain
  plan, dropping photo paths that were never analysed) + `analyze_photo_sequence()` reusing
  the pipeline's own analysis prompt so `ai_cache` still hits. `MockProvider` returns the
  heuristic plan; `registry.py` reserves `provider: local_vlm`.
- Service (`VisualNarrativeStudio`): `load_photos` (scanned only, ≤ `max_photos`),
  `load_context`, `build_plan` (no writes), `generate(persist=True, dry_run=...)`,
  `save_plan` (new version each time), `apply_update(StoryboardUpdateRequest)`,
  `reorder_shots`, `set_hero_image`, `approve(force=...)`, `archive`, `issues_for`,
  `narrative_block(city_id)`. API and UI both call this one object — no duplicated logic.
- Admin API (`app.py`): `GET /api/cities/{id}/storyboard`,
  `POST /api/cities/{id}/storyboard/generate?dry_run=`,
  `PUT /api/cities/{id}/storyboard`, `POST /api/cities/{id}/storyboard/approve`,
  `GET /api/storyboards/{id}` + handlers mapping `NotFoundError→404`,
  `StateTransitionError→409`, `StoryboardValidationError→422` (issues in the body).
- Streamlit: `ui/storyboard_page.py` + a `🎬 Storyboard` tab in `ui/dashboard.py`.

## Invariants worth copying

- Exactly one hero image; shot `order` normalized to `0..n-1`; shots only from analysed
  photos; unique photo paths; required beats (`setup`, `climax`, `resolution`) SYNTHESIZED
  when the material cannot supply them instead of silently violating the arc.
- Storyboards are versioned rows (`next_storyboard_version`, unique per city) — history is
  immutable; editing an `approved` storyboard demotes it to `draft`.
- Honest degradation: provider failure → local heuristic plan flagged `degraded` +
  `degradation_reason` (surfaced by API/UI), never a silent empty storyboard.

## Verification that caught real bugs

```bash
cd ~/projects/travel-blog-app
.venv/bin/python -m pytest -q                      # 81 → 130 passed
.venv/bin/python -m compileall -q app.py cli.py core modules ui tests   # exit 0
PYTHONPATH=. .venv/bin/python /tmp/vns_smoke.py    # temp DB: preview→persist→approve→
                                                   # reorder→blocked re-approve→v2 history
python3 ~/.hermes/profiles/developer/tools/scan_credentials.py --staged   # clean
```

Two genuine bugs only the smoke/test pass found (both fixed, both now in the recipe):

1. **Missing `;` in the original `_SCHEMA`** — the new tables glued onto the last existing
   table, so `connect()` failed for the whole app. Symptom (schema syntax error) does not
   point at the real cause: the missing `;` is in the pre-existing code.
2. **`ensure_arc` could violate its own invariants** (kept a shot whose photo was not in the
   analysed set; could not synthesize a missing required beat when the plan had few shots).
   Fixed by filtering shots by membership when the photo set is known and by
   `_placeholder_beat()` for missing required beats.

## Live-run findings (2026-09-18, local stack)

Running the app locally (recipe: `local-run-and-ui-verification.md`) surfaced a third bug that
unit tests, the smoke script and `compileall` had all passed:

3. **`dry_run=dry_run or None` swallowed an explicit `false`.** With `app.dry_run: true` in
   `config.yaml`, `POST /api/cities/{id}/storyboard/generate?dry_run=false` answered
   `dry_run: true` and persisted nothing — `False or None → None →` the studio falls back to
   the config default, so the admin API could not write at all while the app ran in dry-run
   mode. Fixed by making the query param tri-state: `dry_run: Optional[bool] = None`
   (omitted → inherit `app.dry_run`, explicit `false` → real write); commit `0b5a536`,
   regression test `test_explicit_dry_run_false_is_not_swallowed_by_config`.
   Why the suite missed it: the API-test fixture sets `cfg.app.dry_run = False`, where
   `False or None` is harmless. **When a default is folded into a request value with `or`,
   test BOTH sides of the flag.**

Verified live afterwards (city 3, Tokyo):
`generate?dry_run=false → 200 (persisted; plan hero = the climax shot)` →
`GET → 200, v1 draft, 3 beats / 3 shots, issues []` → `PUT {storyboard:{logline}} → 200` →
`approve → 200 approved` → `approve again → 409 state_transition_error` →
`GET /api/cities/999/storyboard → 404`.
The Streamlit page rendered clean through AppTest (no exceptions, exactly one hero checkbox
`True`, editor table with 3 beats) and defaults to preview mode because `app.dry_run: true`.

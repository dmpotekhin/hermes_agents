# Brand-strategy wiring: a config-only policy layer over a shipped pipeline

Session 2026-09-19, right after the Tri-Face Carousel Factory merged into `main`.
Request: "зашить бренд-стратегию … точечно, минимум диффов … только config + hook scoring +
travel narrative guard". Deliverable: `853b8ad` "Brand alignment: content mix, builder-angle,
CTA funnel, hook brand_fit" — 5 files + 1 new test file, +325/−11; suite 404 → **408 passed**
(`pytest -q -p no:logging`, 106s); `compileall` OK; mypy clean on the 5 changed files;
`ruff check --isolated --select F,E9,B <files>` clean.

## The recipe: policy layer, not a rewrite

1. `config.yaml` → a new section under the existing parent key (`carousels.brand`), existing
   keys untouched. Every string a human may want to change (CTA copy, keyword lists) lives
   ONLY here — no copy in Python.
2. `core/config.py` → pydantic models + one field on the parent
   (`brand: CarouselBrandConfig = Field(default_factory=CarouselBrandConfig)`). Put the *policy
   helpers on the models* so no module carries the rules: `travel_rules.has_builder_angle(text)`,
   `cta_funnel.cta_for(vertical)` (accepts the enum or its `.value`). Model defaults mirror the
   YAML, so a config without the section still loads.
3. Scoring point → optional policy in the constructor
   (`HookEngine(brand: Optional["CarouselBrandConfig"] = None)`), factor applied last; `None`
   keeps the raw score. Multipliers RANK, never filter:
   `score = min(additive, 1.0) * factor`, factor clamped to the band
   (`BRAND_FIT_MIN/MAX = 0.8/1.2`), and the factor stays visible in `scores_json` so the hook
   stays explainable.
4. Narrative point → the guard only *appends a warning*; the slide plan still builds every
   slide, so the human approval gate remains the only blocker. `warning_only: true` in config.
5. CTA point → precedence `operator override → config → profile default`.
6. Wiring = 2 lines in `modules/carousels/service.py`:
   `HookEngine(brand=getattr(self.settings, "brand", None))` / `SlidePlanner(brand=...)`.
   No signature churn, no new module, no changes to renderer/publisher/analytics/state machine.
7. Import hygiene: `if TYPE_CHECKING: from core.config import CarouselBrandConfig` plus a quoted
   annotation — keeps engine/planner importable with no cycle and no runtime cost.

Face resolution for the hybrid pipeline:
`FAMILY_BY_PATTERN = {pattern.key: vertical for vertical, patterns in PATTERNS_BY_VERTICAL.items()
for pattern in patterns}` — the literal spec only named single verticals, but `HYBRID` needs it too.

Resulting multipliers (mix 0.60/0.25/0.10/0.05, spread 0.25, lifestyle floor 0.8): vibecoding
1.15 · travel with a builder angle 1.06 · travel as pure lifestyle 0.85 · QA hook whose category
is in `qa_rules.reliability_categories` 1.03 · everything else 1.00.

## Bugs and pitfalls that cost real time

- **Leaking the new key into the no-policy path.** `brand_fit = scores.pop("brand_fit", 1.0)`
  followed by an unconditional `scores["brand_fit"] = brand_fit` put `brand_fit: 1.0` into
  `scores_json` even for `HookEngine()` with no brand — the "behaviour is unchanged without
  config" premise was false, and the new test caught it. Use a `None` sentinel:
  `pop("brand_fit", None)`, re-insert only when it is not `None`,
  `factor = 1.0 if brand_fit is None else brand_fit`.
- **The CTA slide is not `slides[-1]`.** The QA profile's `slide_sequence` ends with
  `prevention_checklist` and contains NO CTA slide at all (travel and vibecoding do end with
  `SlideType.CTA`). Locate it with
  `next((s for s in result.slides if s.slide_type is SlideType.CTA), None)`. Honest consequence
  to report: `cta_funnel.default_cta_by_vertical.qa` is configured but unrendered today — do NOT
  "fix" it by editing `vertical_profiles.py` (it changes slide counts and existing tests).
- **Score assertions under a multiplier and a 1.0 cap.** A strict `>` on the bonus flakes when
  the additive part already sits at the cap: assert `>=` for the bonus, `<` for the penalty, and
  prove ranking by the gap widening (`branded_gap > plain_gap`) rather than by absolutes.
  Compare the SAME fact/pattern across the branded and the plain run — the candidate set and the
  fact→pattern assignment are brand-independent, so only the factor moves the score.
- **Rounding:** `1 + 0.25*0.25 = 1.0625` → `round(..., 2)` = `1.06`; assert with
  `pytest.approx(1.06, abs=0.01)`, not float equality.
- **`ruff` in this venv needs the subcommand form:**
  `.venv/bin/python -m ruff check --isolated --select F,E9,B <files>`; the bare
  `ruff --select ...` fails with `unexpected argument '--select'`.

## Test file added

`tests/test_carousel_brand.py` (4 tests, fixture style copied from `tests/test_carousel_hooks.py`
and `tests/test_carousel_planner.py`):

- `test_brand_config_loaded` — config round-trip (mix numbers, keyword list, CTA per vertical)
  plus "existing `carousels.*` keys survive" (`mode`, `require_human_approval`, `slide_count`).
- `test_travel_builder_angle_warning` — pure-lifestyle travel → exactly one warning with the
  spec prefix and still 6 slides; builder-angle fact → no warning; QA unaffected; **no brand →
  silent** (proves the pre-brand path).
- `test_hook_brand_fit_vibecoding_bonus` — per-fact `brand_fit` by matched family, same-fact
  branded vs plain comparison, gap widening, and **no brand → no `brand_fit` key at all**.
- `test_cta_default_by_vertical` — configured text rendered, `!= profile.cta_style`,
  `cta_override` wins, no brand → profile fallback.

## Verification and delivery for this class of request

`pytest -q -p no:logging > /tmp/pytest_<x>.log` → `compileall -q app.py cli.py core modules ui tests`
→ mypy/ruff on the changed files only → `scan_credentials.py --staged` (exit 0) →
`git commit -F /tmp/msg.txt` with the exact message from the brief → `git push` → prove
`main == origin/main` (`git rev-list --left-right --count origin/main...HEAD` = `0 0`) and a clean
`git status --porcelain`. The reply is the numbered artifact list the user asked for (config diff,
code-point diffs, pytest line, commit hash) plus one honest note for any spec item that cannot be
satisfied without touching forbidden files (the QA CTA case above).

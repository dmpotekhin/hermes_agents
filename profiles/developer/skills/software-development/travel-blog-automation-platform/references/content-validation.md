# Content compliance validation in travel-blog-app (worked feature G1–G7)

Verified 2026-08-29 while adding automatic validation of BOTH content types
(Trip.com Trip Moments + VibeCoding educational/expert). Pair with
`references/extending-content-types.md` for the content-type recipe; this file is
the reusable *validation layer* pattern that sits on top of any content type.

## The pattern (add a validator for a content type)

1. **Config** — `core/config.py` + `config.yaml`: one guidelines block per content
   type (`trip_guidelines`, `vibecoding_guidelines`), each with a
   `block_non_compliant: false` flag (see soft-gate below). Block-style YAML.
2. **Shared scaffolding** — `modules/validation_base.py`: `ValidationCheck`
   (`id`, `label`, `passed`, `severity`, `message`, `recommendation`) and
   `ValidationResult` (`checks`, `compliant`, `score`, `recommendations`, `to_dict()`)
   dataclasses + text helpers `word_count`, `count_hashtags`, `contains_emoji`,
   `has_question`, `find_forbidden`. Severity: `error` gates compliance;
   `warning`/`info` are non-blocking recommendations.
3. **Validators** — `modules/trip_validator.py` (`TripValidator.validate(draft, city)`)
   and `modules/vibecoding_validator.py` (`VibeCodingValidator.validate(post)`). They
   NEVER raise — always return a `ValidationResult`. Base config on the real entity
   (`Draft`+`City` for Trip, `VibeCodingPost` for VibeCoding), not on a made-up shape.
4. **Scheduler gates** — `modules/scheduler.py`: `_trip_gate()` / `_vibe_gate()`
   returning `{compliant, blocked, summary}`, called in `run_due()` (trip_com) and
   `publish_vibecoding_due()`.
5. **UI** — `ui/validation_view.py`: `render_validation(dict)` shared Streamlit
   checklist renderer (metrics + per-check ✅/⚠️/❌ + 💡 recommendations). Wire it into
   the Posts tab (Trip) and the VibeCoding page with a "Проверить" button.
6. **Logging** — every run through Loguru: `logger.bind(validator, post_id).info(...)`
   with score/summary. Never read secrets, never log content beyond summary.
7. **Tests** — `tests/test_validators.py`: one compliant + one non-compliant per type,
   plus soft-vs-block gate assertions.

## Soft-gate pattern (reusable for ANY compliance/quality gate)

Each guidelines block adds `block_non_compliant: false`. Validation **always** runs,
is logged via Loguru (`logger.bind(validator, post_id)`), and is shown in the UI;
publishing is blocked **only when** `block_non_compliant: true`. Preserves the
existing honest-automation flow while surfacing concrete recommendations. To make a
gate strict, flip that one flag — the plumbing is already there.

## Heuristics, not fake assertions

- Trip restaurant minimum (5 photos) inferred from per-photo AI `analysis` keywords
  (`restaurant`/`еда`/`кафе`/`coffee`/...); interior-photo requirement from
  `interior`/`внутри`/`inside`/... Only the `photos_json` the real engine writes
  (`{"photos":[{path,analysis}]}`) is parsed — handle both JSON dict and raw list.
- Video-duration checks are marked `info` "not applicable" — the current
  Draft/VibeCodingPost shape has NO video field. Never fake a pass/block.
- VibeCoding `min_photos: 2` is a **warning** (one post carries one AI image);
  `min_words` below the floor is an **error** (thin content).
- `has_question` accepts an explicit `?` OR the configured default engagement
  question — don't require perfect interrogative parsing.

## Verification

`cd ~/projects/travel-blog-app && .venv/bin/python -m pytest tests/test_validators.py -p no:cacheprovider -q` (10 passed); full suite 59 passed. run pytest redirected to a file, never piped through grep/tail.

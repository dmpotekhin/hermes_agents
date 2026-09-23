# Adding a new content type / feature to travel-blog-app

Verified 2026-08-29 while adding the **VibeCoding** content type (F1–F7). This is
the reusable recipe for extending the app with a new generated content type, plus
the gotchas that surfaced. Adapt to the real project structure — do NOT follow a
spec's file names blindly.

## Reusable recipe (each step is a real file)

1. **Config** — `core/config.py`: add a typed section model (e.g. `VibeCodingConfig`,
   `ImageGenerationConfig`, `TextGenerationConfig`) + add it to the `Config` class;
   add any new secrets (e.g. `replicate_api_token`, `openai_api_key`) to `Secrets`.
   `config.yaml` gets the block **block-style** (never flow `{...}`) — YAML validation
   fails on flow maps.
2. **State machine + entity** — `core/models.py`: add a `*Status` enum, a
   `_X_TRANSITIONS` dict, a `x_transition()` helper (via `check_transition`), and the
   `Pydantic` entity model. Rule: never write a status directly — go through the
   validated transition helper.
3. **Database** — `core/database.py`: add the table to `_SCHEMA` (Postgres-esque,
   `TEXT` defaults, `created_at`/`published_at`), CRUD methods (add/get/list/update/
   delete), a validated `update_x_status` using the transition helper, a row→model
   converter, and module-level async wrappers in the public API block.
4. **Generator** — `modules/<type>_generator.py`:
   - `ImageGenerator`: call image providers via **httpx REST** (Replicate
     `POST /v1/models/{model}/predictions` + poll; OpenAI `POST /v1/images/generations`;
     HuggingFace inference). Under `app.dry_run` (the default) fall back to a **Pillow
     placeholder** so the whole pipeline runs offline with no keys. Never import the
     `replicate`/`openai` SDKs — they are not installed and the project calls all
     external services over httpx.
   - Text: reuse the existing AI registry — `build_provider(db, config, "deepseek")`.
     In `dry_run` the registry auto-forces `MockProvider`, so no key is needed.
   - Orchestrator: `generate_post` → `save_post` → `generate_and_save`.
5. **Media** — `modules/media.py`: add `prepare_<type>_media(img, id, presets, config)`.
   Reuse `optimize_image`; write per-platform assets under `media_ready/<type>/{id}/`.
   Skip MP4 presets for static images.
6. **Publisher** — `modules/publishers/<type>.py`: a service (NOT a new adapter) that
   maps a post onto the existing `BasePublisher` contract via `build_publisher`. Auto
   platforms publish via their adapters (Mock under dry_run); MANUAL platforms stay
   honestly `manual` — never fake `published`.
7. **Scheduler** — `modules/scheduler.py`: add a `publish_<type>_due()` method honoring
   `config.<type>.enabled` and an `auto_publish` gate, plus a cron job in
   `build_async_scheduler()` at `<type>.schedule_time` on `<type>.schedule_days`.
8. **UI** — new `ui/<type>_page.py` + `ui/settings_page.py` with a `render()` function;
   import them into `ui/dashboard.py` as new tabs. Each ui module must bootstrap
   `_ROOT` into `sys.path` before imports (Streamlit runs cwd=`ui/`).
9. **Tests** — `tests/test_<type>.py`, all under dry_run/mock (no network, no keys).

## Gotchas / pitfalls

- **Bare `Config()` has EMPTY `media_presets`** (`default_factory=dict`). Calling any
  `prepare_*_media` with `cfg.media_presets` returns nothing. In tests, either pass an
  explicit `MediaPreset` dict or use `load_config_file()`.
- **`Config()` defaults `app.dry_run=True`** (AppConfig). This is what makes mock text +
  mock image + MockPublisher work in tests with no setup.
- **Idempotency**: a published post returns as-is on re-publish (guard on
  `status == PUBLISHED` before re-entering the publish loop).
- **Scheduler gating**: only `pending` posts are auto-published unless
  `config.<type>.auto_publish` is true; `draft` posts are left untouched.
- **Naming**: a spec/ТЗ may name files differently from reality
  (`media_processor.py`/`publisher.py` vs the real `modules/media.py` +
  `modules/publishers/`). Map spec names onto the actual project structure.
- **Dynamic UPDATE**: build the SET clause from a module-level column whitelist and ignore
  unknown keys — never interpolate a field name straight into SQL.
- **Row→model coercion**: SQLite returns `0/1` for booleans and `str` for JSON columns, so
  models need tolerant accessors/validators (parse `*_json` fields, coerce `bool`), and the
  round-trip (`model_dump()` → row → model) deserves its own small test.
- **Docs count as part of "done"**: `ARCHITECTURE.md` (new numbered section),
  `README.md` (ADR table row + tests badge), `.planning/STATE.md` (Current Position /
  Progress / Recent Activity). Also correct any earlier claim you find to be false
  (e.g. the "not a git repo" line that used to live in this file).

## More gotchas (added 2026-09-18, ADR-106)

- **`_SCHEMA` append trap — it breaks the whole app, not just your feature.** Every
  `CREATE TABLE` in `core/database.py` ends with `;` … except possibly the LAST one.
  Appending new tables right after a table that lacks its `;` glues the statements
  together and `connect()` dies with a syntax error (`near "CREATE": syntax error`),
  taking down every entrypoint (FastAPI, Streamlit, CLI, and the entire test suite).
  Check the tail of the schema for a trailing `;` BEFORE appending (in the
  `vibecoding_posts` era it was missing — a one-char `patch` fixed it).
- **Adding an AI capability without touching existing providers**: put the method on
  `BaseAIProvider` (`modules/ai/base.py`) WITH a default implementation built on the
  existing public path (`generate_text()` / `analyze_image()`), so `gemini.py` and
  `deepseek.py` inherit it unmodified. Override it in `MockProvider` with a deterministic
  result (that's what makes tests and `dry_run` work with no keys), and register any new
  provider name in `modules/ai/registry.py` as an explicit extension point that raises a
  clear `ConfigurationError` until the module exists (e.g. `provider: local_vlm`).
- **Extending the pipeline without new statuses**: add the step *inside* `process_city`
  (`modules/content/engine.py`) and pass its rendered output into the existing prompt
  builder through a NEW KEYWORD ARG WITH A DEFAULT (`narrative_block: str = ""`) — default
  args keep every existing caller and test green. Any human-approval gate goes behind an
  opt-in config flag (default off) instead of changing the city state machine, which is
  public contract (CLI/API/UI/tests). The step itself must be wrapped in try/except → log
  a warning and return the empty continuation: a new layer must never be able to kill a city.
- **Testing an admin API endpoint**: `tests/test_api.py` imports the real `app`, whose
  lifespan opens `Database()` → the real `travel_blog.db`. In a feature test, seed a temp
  DB with `asyncio.run(...)`, then
  `monkeypatch.setattr(core.database, "DEFAULT_DB_PATH", str(tmp_path / "api.db"))` and
  monkeypatch the app's config loader (e.g. `app._load_config`) BEFORE
  `TestClient(app_module.app)`. Then set `cfg.app.dry_run = False` on that patched config —
  bare `Config()` AND the shipped `config.yaml` both default `dry_run: true` (bare `Config()`
  forces `MockProvider`), and a dry-run step deliberately writes nothing to the DB, so an
  API test expecting a persisted row will otherwise see an empty result.

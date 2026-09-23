# Carousel Factory: pre-PR hardening notes (2026-09-19)

Project: `/Users/dmitrypotekhin/projects/travel-blog-app`, branch
`feature/tri-face-carousel-factory`. State after the hardening commit `9e2ac1c`:
suite 404 passed, 12 commits ahead of `main`, PR body prepared in
`docs/pr-tri-face-carousel-factory.md` (PR itself needs GitHub auth the sandbox
does not have: MCP github server uses `${DEVELOPER_GITHUB_TOKEN}` -> "Bad
credentials"; `gh` is not installed).

## Offline-but-real test patterns the project already uses

* `httpx.MockTransport` handed to a real client; every external collaborator is
  injectable, so a full pipeline walk needs no network and no key:
  * `GitHubSourceResolver(CarouselGithubSourceConfig(), client=httpx.AsyncClient(transport=...), token="")`
  * `UploadPostPublisher(token=..., user=..., client=..., backoff_seconds=0.0)`
  * `UploadPostMetricsCollector(publisher)` — reuse the SAME publisher for
    publish and metrics; do not `aclose()` it before collecting.
* service seams: `research(job_id, resolver=...)`, `draft_narrative(..., engine=...)`,
  `render_slides(job_id, renderer=...)`, `verify_slides(job_id, verifier=...)`,
  `publish(job_id, publisher=..., platforms=...)`,
  `collect_metrics(job_id, collector=...)`.
* `CarouselFactory(db, config, secrets)`; tests do
  `Database(str(tmp_path / "carousel.db"))` + `await db.connect()`;
  redirect renders with `factory.settings.output_dir = str(tmp_path / "carousels")`.
* `pytest.ini` has `asyncio_mode = auto` (plain `async def test_` works).
* A synchronous publish stub must answer with per-platform rows
  (`{"success": true, "request_id": "...", "results": [{"platform": ..., "success": true, "post_url": ...}]}`),
  otherwise rows stay `PROCESSING` and the job never reaches `published`.
* `dry_run=True` is the config default and wins over an injected publisher
  (`is_dry = isinstance(active, MockCarouselPublisher) or self.dry_run`); set
  `factory.settings.dry_run = False` to exercise the publishing transitions with
  a stub wire.

## Streamlit smoke (real page, stub service)

* `AppTest.from_function` runs the function's SOURCE in a fresh module
  namespace: pass a wrapper whose imports (`import streamlit`,
  `from ui import carousel_page`) live INSIDE the function, and pass arguments
  via `kwargs={...}` (supported in streamlit 1.62). Monkeypatching the imported
  `ui.carousel_page` module works because `sys.modules` is shared.
* `ui/carousel_page.py` calls the service through `_run(action, *args)` and a
  module-global `_factory(db, cfg)` / `Database`; replace both in the test.
* Stub traps: never give a stub an attribute that shadows a method it must
  expose (`self.recommendations = [...]` silently kills `recommendations()`);
  `st.image` really opens the file, so write a genuine JPG with Pillow.

## Bugs this hardening found (all fixed, all in carousel code)

* `ui/carousel_page.py`: source-type list must come from `CarouselSourceType`
  ("github"/"manual"/"mock" are not members); "auto" vertical must be sent as
  `""` (`CarouselVertical` has no AUTO); the slide image field is
  `final_image_path` (not `image_path`); the publish button must take its gate
  from `status_report()["can_publish"]` and be `disabled` otherwise.
* `modules/carousels/service.py`: ids read back from the DB are `int | None` —
  guard them (`_require_id`) instead of passing them to `update_*`.
* `sources/github.py`: a list of `Metric | None` must be filtered BEFORE being
  assigned to a variable that is later passed as `List[Metric]`.
* `render/providers.py`, `render/pillow_renderer.py`: `Image.load()` returns
  `PixelAccess | None` — assert before indexing.
* `analytics/learnings.py`: `refresh_learnings()` writes rows even when the
  sample is below `min_sample_size` (honesty lives in `sample_size`/`confidence`
  on the row); `recommendations()` is what respects the threshold.
* `cli.py`: `score` returns a structured payload, not a bare string.

## Lint policy for this repo

* No `pyproject.toml`/`setup.cfg`; `ruff` and `mypy` are NOT in requirements —
  install with `.venv/bin/python -m pip install mypy ruff` when asked.
* Run focused, else the 579-finding style noise from ruff's defaults buries the
  signal: `ruff check --isolated --select F,E9,B <paths>` and
  `mypy <paths> --ignore-missing-imports --follow-imports=silent`.
* `ruff --fix --select F401` is safe for plain modules, but NOT for facade
  modules that re-export core enums (`modules/carousels/enums.py`): add the name
  to `__all__` instead, or the public surface disappears.
* Legacy noise stays: cli.py travel branches reuse one variable name (`res`) and
  trigger two mypy errors — report, do not refactor.

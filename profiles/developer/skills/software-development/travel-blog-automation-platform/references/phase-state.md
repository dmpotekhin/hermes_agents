# Phase state snapshot (2026-08-28)

Worked P2..P7 to green with one real pytest per phase; P8 layer is written but not yet
green. This is the continuation reference.

## Verified phases (each backed by a passing pytest in tests/)
- P2 Scanner — test_scanner.py (incremental, EXIF/GPS, deduced cities, broken→failed)
- P3 City Queue — test_queue.py (priority/year, claim/requeue, require_photos, counts)
- P4 AI — test_ai.py (httpx REST adapters Gemini+DeepSeek, AICache, RateLimiter,
  deterministic MockProvider, registry/build_provider)
- P5 Content — test_content.py (photo select → facts → base story → per-platform
  drafts; city status → DRAFTED/ERROR)
- P6 Media — test_media.py (Pillow image path: optimize/orient/resize/size-cap,
  per-platform asset sets). VIDEO sub-step left MANUAL/optional: moviepy 2.2.1 is
  installed but `import moviepy` / imageio-ffmpeg ffmpeg resolution hangs on the
  network — there is no live video path; image path is the verified one.
- P7 Drafts — test_drafts.py (approve/reject/reset via the state-machine helpers,
  auto-approve rule for telegram+vk only)

Last full green run before P8: 20 passed.

## P8 Publishers — IN PROGRESS (do NOT mark done until green)
Layer written under modules/publishers/: base.py, mock.py, telegram.py, vk.py,
facebook.py, manual.py, registry.py, service.py (PublishService). Added
PublicationStatus.MANUAL to core/models.py. tests/test_publish.py written but NOT
passing yet. Known gap to fix first:
- test constructs `DraftManager(db, config)` but `DraftManager.__init__` takes only
  `(db)`. Either change the test to `DraftManager(db)` or make config optional.
- Confirm a `get_publication_by_platform(city_id, platform)` method exists in
  core/database.py before the test calls it.

## Honest-automation platform modes (ARCHITECTURE.md D3)
- auto: telegram, vk (VK wall.post supports publish_date scheduling).
- partial: facebook (post+photo via API; scheduled Page posts app/version-dependent).
- manual (prepare content+media, record `manual`, NEVER fake `published`):
  zen, trip_com, instagram, youtube.

## Live state lives in
- .planning/STATE.md — current phase + phase checklist.
- ARCHITECTURE.md §77 — the design-decision register (append trade-offs here).

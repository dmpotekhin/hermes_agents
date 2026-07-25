---
name: travel-content-factory
description: >-
  Work with the Travel Content Factory project — a local video production tool
  for travel content. Full-stack FastAPI plus SQLAlchemy async plus aiosqlite
  backend, Vanilla JS frontend, FFmpeg video processing, DeepSeek AI integration.
---

# Travel Content Factory

Project at `/Users/dmitrypotekhin/travel-content-factory/`

Local web tool for managing travel media archives and creating content for TikTok, Reels, Facebook.
Upload photos/videos → extract EXIF/GPS → montage with AI scripts → render with music → export.

**Start:** `./start.sh` → `http://localhost:8000`

## Architecture

```
Browser (Vanilla JS SPA)
    ↕ REST JSON + multipart uploads
FastAPI (port 8000)
    ├── routers/media.py    — /api/media/*    scan, list, thumbnail, delete
    ├── routers/projects.py — /api/projects/*  CRUD, auto-match, script-to-scenes, render
    ├── routers/ai.py       — /api/ai/*        DeepSeek content generation
    └── routers/music.py    — /api/music/*     list, upload, delete background tracks
    ├── services/scanner.py  — exiftool subprocess → EXIF, GPS, date, duration
    ├── services/ffmpeg.py   — trim, concat, overlay_audio, normalize_audio, thumbnail
    └── services/deepseek.py — BaseAIClient → DeepSeekClient (httpx, retry, JSON mode)
SQLite (aiosqlite) via SQLAlchemy 2.0 async
    ├── media_files, projects, project_clips, generations
```

## Key files

| File | Responsibility |
|------|---------------|
| `backend/main.py` | FastAPI app, CORS, lifespan (DB init + dirs), static mount |
| `backend/database.py` | Async engine, session factory, auto-computed DATABASE_URL |
| `backend/models.py` | MediaFile, Project, ProjectClip, Generation |
| `backend/routers/media.py` | Scan folders, list/filter, thumbnails, delete |
| `backend/routers/projects.py` | CRUD + auto-match + script-to-scenes + render with music |
| `backend/routers/ai.py` | DeepSeek: generate script+caption+hashtags, script-to-scenes |
| `backend/routers/music.py` | List/upload/delete music tracks in `music/` |
| `backend/services/scanner.py` | exiftool -json wrapper, GPS/date/duration extraction |
| `backend/services/ffmpeg.py` | trim, concat, overlay_audio, normalize_audio, overlay_text, get_duration, thumbnail |
| `backend/services/deepseek.py` | BaseAIClient abstract + DeepSeekClient (retry, JSON mode) |
| `frontend/index.html` | SPA shell: 3 tabs + 3 modals (new project, detail, render) |
| `frontend/js/app.js` | API wrapper, tabs, grid, modals, toasts, music upload |
| `frontend/css/style.css` | Dark theme, responsive grid, preset buttons |

## Gotchas — common bugs and fixes

### 1. SQLAlchemy DetachedInstanceError on Project.clips
Symptom: `Internal Server Error` on any endpoint returning Project objects.
Root cause: `_project_to_dict(p)` accesses `p.clips` (lazy relationship) after session closes.
Fix: Always query with `selectinload(Project.clips).selectinload(ProjectClip.media)`.
`await db.refresh(p)` does NOT eager-load — re-query with selectinload instead.
→ See `references/sqlalchemy-pitfalls.md` for full error transcript.

### 2. SQLite path: relative `./data/` resolves from CWD not project root
Symptom: `sqlite3.OperationalError: unable to open database file`.
Fix: `database.py` computes absolute path from `__file__`: `Path(__file__).parent.parent / "data" / "travel_factory.db"`.
Do NOT set `DATABASE_URL` in `.env` unless overriding with an absolute path.

### 3. FastAPI `app.mount("/", StaticFiles)` shadows later routes
Symptom: `/api/health` → 404, but `/api/media/list` works.
Fix: ALL `app.include_router()` + ALL `@app.get()` MUST come BEFORE `app.mount("/", ...)`.
Health check, in particular, must be above the mount.

### 4. Generic `.hidden` CSS class required
Symptom: Elements with `class="hidden"` still visible.
Fix: Add `.hidden { display: none !important; }` in CSS. Without `!important`, it may not override
other display values set by `.modal`, `.toast`, etc.

### 5. .env content mangling in write_file
The `write_file` tool may mangle lines containing `***` followed by newlines in `.env` files.
Workaround: use `terminal` with heredoc (`cat > file << 'EOF' ... EOF`) for `.env` files.

### 6. Foreground `&` backgrounding blocked
Terminal tool rejects `command &` syntax. Use `terminal(background=true)` for servers.

### 7. FFmpeg drawtext special character escaping
Symptom: `overlay_text failed` with garbled text or filter parse errors.
Fix: Always use `_escape_drawtext()` before passing text to the drawtext filter.
Characters requiring escapes: `:` → `\\:`, `'` → `\\'`, `%` → `\\\\%`, `\` → `\\\\`.
Without escaping, text containing `:` (like "Morning in Paris: Day 1") breaks the filter chain.
→ See `references/ffmpeg-audio-patterns.md` for the full filter graph.

## Render pipeline

```
1. trim_video()      → extract each clip from source
2. overlay_text()    → [optional, per-clip] AI-generated text captions (drawtext)
3. concat_videos()   → concatenate all clips
4. overlay_audio()   → [optional] loop music, fade in/out, mix with original
5. normalize_audio() → loudnorm to -14 LUFS
6. export            → save to exports/
```

Render endpoint: `POST /api/projects/{id}/render` with optional body:
```json
{"music_path": "music/track.mp3", "music_volume": 0.25, "add_captions": true, "caption_text": ""}
```

Response includes: `"music_applied": true/false, "captions_applied": true/false`.

Caption behavior:
- `add_captions=false` → no text overlay (default)
- `add_captions=true, caption_text=""` → AI generates captions per clip from metadata (location, date, filename)
- `add_captions=true, caption_text="My text"` → same text on every clip

AI caption generation sends clip metadata to DeepSeek: location, date, duration, filename.
Returns array `{"captions": [{"clip_index": 0, "text": "Morning in Paris"}, ...]}`.
Clips with existing `scene_description` use that instead of AI generation.
AI failure is non-fatal — renders without captions and logs warning.

## FFmpeg services

| Function | Purpose | Key params |
|----------|---------|------------|
| `trim_video()` | Extract clip segment | `start`, `duration` |
| `concat_videos()` | Concatenate clips | demuxer, re-encode fallback |
| `overlay_audio()` | Mix music into video | `music_volume`, `original_volume`, `fade_in`, `fade_out` |
| `normalize_audio()` | Loudness normalization | `target_level` (−14 LUFS default) |
| `overlay_text()` | Drawtext overlay per clip | `text`, `font_size=28`, `position="bottom"`, `box_opacity=0.5` |
| `get_duration()` | Get video duration via ffprobe | — |
| `create_thumbnail()` | Generate preview JPEG | `size="320x240"` |

### drawtext escaping

The `_escape_drawtext()` helper escapes `:`, `'`, `%`, `\` for FFmpeg drawtext filter.
Multi-line text uses `\n` in the text string; FFmpeg `line_spacing=6` handles vertical gap.
Position: bottom third (`y=h-th-60`), centered horizontally (`x=(w-text_w)/2`).
Text is white on semi-transparent black box (`box=1:boxcolor=black@0.5:boxborderw=8`).

## Music library

Tracks stored in `music/` directory. API:
- `GET /api/music/list` — returns `{tracks: [{path, filename, size_mb, duration}]}`
- `POST /api/music/upload` — multipart file upload (accepts .mp3/.m4a/.wav/.ogg/.flac)
- `DELETE /api/music/{filename}` — remove track

Frontend render dialog populates dropdown from `/api/music/list` on open.
"+ Upload" button sends file to `/api/music/upload` and refreshes dropdown.

Volume presets for short-form video:
- Voice-over: 12% — speech primary, music barely audible
- Balanced: 25% — standard reel/tiktok (default)
- Music first: 45% — slideshow/montage without narration

→ See `references/frontend-patterns.md` for the JS patterns used.

## Dependencies

```bash
brew install ffmpeg exiftool
```

Python deps in `requirements.txt`: fastapi, uvicorn, sqlalchemy[asyncio], aiosqlite, httpx,
python-dotenv, python-multipart, aiofiles.

DeepSeek API key in `backend/.env`: `DEEPSEEK_API_KEY=***`.

## Documentation style

Project docs use rich visual formatting:
- Emoji icons in headings, table cells, and list items
- shields.io badges for tech stack header
- ASCII-art box-drawing mockups for UI flows
- Tables for API references and configuration
- Concrete examples with fake but realistic paths

When editing `README.md` or writing new docs, match this style exactly:
emojis first, tables over bullet lists, concrete examples.

## GitHub

- Repo: https://github.com/dmpotekhin/travel-content-factory
- Remote: `git@github.com:dmpotekhin/travel-content-factory.git`
- Branch: `main`
- SSH auth works

## Hermes MCP servers

The Hermes agent developing this project has MCP servers configured in `~/.hermes/config.yaml`:

| Server | Package | Provides |
|--------|---------|----------|
| GitHub | `@modelcontextprotocol/server-github` | `mcp_github_*` — issues, PRs, reviews, file contents |
| Playwright | `@playwright/mcp@latest` | `mcp_playwright_*` — browser automation, screenshots, e2e |
| Perplexity | `@perplexity-ai/mcp-server` | `mcp_perplexity_*` — web search via Perplexity API |

Perplexity needs `PERPLEXITY_API_KEY` in `~/.hermes/.env`. Other two work out of the box.
The `mcp` Python package must be in the system Python (`pip3 install mcp --break-system-packages`).
On macOS without Xcode CLT, use `--only-binary :all:` for cryptography to avoid Rust compilation.

## Reference files

- `references/sqlalchemy-pitfalls.md` — DetachedInstanceError, relative SQLite paths, FastAPI mount shadowing
- `references/ffmpeg-audio-patterns.md` — overlay_audio filter graph, normalize_audio, volume presets
- `references/frontend-patterns.md` — Vanilla JS: API wrapper, tabs, modals, toasts, grid, XSS escaping, CSS patterns

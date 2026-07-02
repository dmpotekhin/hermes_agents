---
name: media-retrieval
description: "Fetch web media content: YouTube transcripts via youtube-transcript-api and GIF search/download via the Tenor API."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [media, YouTube, transcripts, GIF, Tenor, search, download]
---

# Media Retrieval — YouTube Transcripts & GIF Search

Web media content retrieval tools. Two standalone modules:

---

## A. YouTube Content — Transcripts to Summaries, Threads, Blogs

Extract YouTube video transcripts and transform them into useful formats (summaries, chapter lists, Twitter threads, blog posts, quotes).

### Setup
```bash
uv pip install youtube-transcript-api
```

### Fetch Transcript

Use the bundled helper script — accepts any YouTube URL format, short links (youtu.be), shorts, embeds, or raw 11-character video ID.

```bash
# JSON output with metadata
SKILL_DIR=$(dirname $(find ~/.hermes/skills -name "SKILL.md" -path "*/media-retrieval/*" | head -1))
uv run python3 "$SKILL_DIR/scripts/fetch_transcript.py" "https://youtube.com/watch?v=VIDEO_ID"

# Plain text (good for piping)
uv run python3 "$SKILL_DIR/scripts/fetch_transcript.py" "URL" --text-only

# With timestamps
uv run python3 "$SKILL_DIR/scripts/fetch_transcript.py" "URL" --timestamps

# Specific language with fallback chain
uv run python3 "$SKILL_DIR/scripts/fetch_transcript.py" "URL" --language tr,en
```

### Output Formats

After fetching, transform based on user request:
- **Chapters**: Timestamped list grouped by topic shifts
- **Summary**: 5-10 sentence overview
- **Chapter summaries**: Chapters with short paragraph each
- **Thread**: Twitter/X thread format, numbered posts
- **Blog post**: Full article with title, sections, takeaways
- **Quotes**: Notable quotes with timestamps

### Workflow
1. Fetch transcript with `--text-only --timestamps`
2. Validate non-empty output. If empty, retry without `--language`
3. If transcript > ~50K chars, chunk (40K + 2K overlap), summarize each, merge
4. Transform to requested format (default: summary)
5. Verify coherence before presenting

### Error Handling
- **Transcript disabled**: tell user, suggest checking subtitle availability
- **Private/unavailable**: relay error, ask user to verify URL
- **No matching language**: retry without `--language`, note actual language
- **Dependency missing**: `uv pip install youtube-transcript-api` and retry

---

## B. GIF Search — Tenor API

Search and download GIFs via the Tenor API using curl + jq. No extra tools needed.

### Setup
```bash
# Get free API key at https://developers.google.com/tenor/guides/quickstart
export TENOR_API_KEY=your_key_here
```
Requires `curl` and `jq` (both standard on macOS/Linux).

### Search GIFs
```bash
# Search and get GIF URLs
curl -s "https://tenor.googleapis.com/v2/search?q=thumbs+up&limit=5&key=${TENOR_API_KEY}" | \
  jq -r '.results[].media_formats.gif.url'

# Get preview versions
curl -s "https://tenor.googleapis.com/v2/search?q=nice+work&limit=3&key=${TENOR_API_KEY}" | \
  jq -r '.results[].media_formats.tinygif.url'
```

### Download Top Result
```bash
URL=$(curl -s "https://tenor.googleapis.com/v2/search?q=celebration&limit=1&key=${TENOR_API_KEY}" | \
  jq -r '.results[0].media_formats.gif.url')
curl -sL "$URL" -o celebration.gif
```

### Get Full Metadata
```bash
curl -s "https://tenor.googleapis.com/v2/search?q=cat&limit=3&key=${TENOR_API_KEY}" | \
  jq '.results[] | {title: .title, url: .media_formats.gif.url, preview: .media_formats.tinygif.url}'
```

### API Parameters
| Parameter | Description |
|-----------|-------------|
| `q` | Search query (URL-encode spaces as `+`) |
| `limit` | Max results (1-50, default 20) |
| `media_filter` | Filter: `gif`, `tinygif`, `mp4`, `tinymp4`, `webm` |
| `contentfilter` | Safety: `off`, `low`, `medium`, `high` |
| `locale` | Language: `en_US`, `es`, `fr`, etc. |

### Available Media Formats
Each result has multiple formats under `.media_formats`:
- `gif` — Full quality
- `tinygif` — Small preview
- `mp4` — Video version (smaller file)
- `tinymp4` — Small preview video
- `webm` — WebM video

### Notes
- URL-encode queries: spaces as `+`, special chars as `%XX`
- For sending in chat, `tinygif` URLs are lighter weight
- GIF URLs work directly in markdown: `![alt](url)`

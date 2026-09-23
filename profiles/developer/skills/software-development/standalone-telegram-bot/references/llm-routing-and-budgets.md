# LLM routing with free-primary / paid-fallback budgets

Layer that keeps a bot on a free tier (Groq) and spends on a paid provider
(DeepSeek) only when it must. Shape used by tg-transcriber: one `llm_router.py`
plus `quota.py` and `cache.py` — no new dependencies, no DB.

## Routing decision: plan first, call second

Return a `RoutePlan` (provider, model, max_tokens, max_input_chars, reason)
before any HTTP call. The plan is what tests assert, what the log prints and what
`/usage` explains — never scatter `if provider == ...` through the call site.
Evaluate in this order:

1. **Explicit user mode wins.** `off` → no LLM call at all; `groq`/`deepseek` →
   that provider only. Let an explicit DeepSeek request run even when automatic
   fallback is disabled: the flag gates *automatic* spend, not a direct ask.
2. **Input size picks the model.** `<= GROQ_MAX_INPUT_CHARS` → default chat
   model; larger → heavy model; above the deepseek threshold (e.g. 40k) → paid
   provider if fallback is allowed, else heavy model with the input truncated.
3. **Provider health.** Local daily quota exhausted / 429 / timeout / network /
   invalid JSON after one strict retry → paid fallback if allowed, otherwise a
   local template result flagged degraded.
4. **`auto` is the default** for every internal caller (auto notes, weekly).

## One request per content, one content for two consumers

Analysis and metadata extraction used to be two paid calls on the same text.
Emit a single JSON object (title, summary, technologies, tasks, tags, theme,
project) and reuse it: the note body renders from it and the metadata dict rides
along on the pipeline result instead of being re-asked. Halves spend per item.
Delete the old metadata-only wrapper once the pipeline carries the dict — a
wrapper kept "just in case" is dead code that hides the new path.

## Budget accounting (`quota.py`)

- Counters per calendar day in one JSON file keyed by date + timezone: paid
  calls, primary requests, primary tokens, transcription seconds, cache hits.
- `check_*()` raises the project's own error *before* the call; `register_*()`
  records after it. A cache hit must not increment provider counters.
- Save atomically (temp file in the same dir + `os.replace`), and treat a corrupt
  file as fresh state instead of crashing. Reset on date change.
- The quota error message names the env var to raise
  (`DAILY_GROQ_REQUEST_LIMIT`), not just "limit exceeded".

## Cache (`cache.py`)

- Key = sha256 over `LLM_PROMPT_VERSION : model : source_type : content`.
  Include the prompt version or an edited prompt keeps serving stale answers.
- Never put the source URL in the key — the same text from a different link
  should hit. TTL + max-items bound the file; corrupt file → empty cache.
- Return `provider_used="cache"` so `/usage` can show the saving.

## Save quota before spending it

- Silence detection before the transcription API:
  `ffmpeg -af volumedetect -f null -` then parse `mean_volume`/`max_volume`;
  below the thresholds (e.g. -50 / -25 dB) skip transcription entirely and still
  produce a note. Count audio duration against the transcription-seconds budget.
- Normalise input before the chat call: drop duplicate and very short OCR
  lines, cap OCR chars, head/middle/tail truncate with an explicit
  `[... truncated ...]` marker, and never cut inside a URL.

## Degraded path and user-facing surface

- LLM unreachable → still answer: send transcript/OCR as files and say what is
  missing. Never a stack trace in chat, never a silent failure.
- A file-only command (`/save`-style) must not touch the LLM at all.
- Per-user mode in a small JSON store (`/mode auto|groq|deepseek|off`) behind an
  env flag, plus `/usage` for today's counters; one startup log line prints
  router/primary/fallback/limits/cache state.
- Log provider, model, input length, tokens, cache-hit and fallback reason —
  never keys.

## Provider drift: retired model ids

Free providers retire chat model ids without notice; a hardcoded default then
fails with a "model not available" 404 and the bot silently degrades to the
local template while every test stays green. When output suddenly looks
fallback-ish, diff the catalog against the config before touching the code:
`curl -s https://api.groq.com/openai/v1/models -H "Authorization: Bearer $KEY"`.
Call it with `curl`, not Python `urllib`: a bare urllib request has no
browser-like User-Agent and Cloudflare answers `403 ... error code: 1010`
(false "blocked"), which hides the real answer. Keep the model ids in `.env`
with defaults in the router, and print the resolved model at startup.

## Reasoning models return empty content, not an error

Groq's `openai/gpt-oss-*` (and the same family elsewhere) spend the budget on
hidden reasoning: with a small `max_tokens` the response is
`content: ""` + `finish_reason: "length"` — indistinguishable from an outage,
so the router falls back locally and the user sees templates. Handle it in the
single call site: detect reasoning ids by marker (`gpt-oss`, `o1`, `-reasoning`),
send `reasoning_effort=low`, raise the output limit (a 60-token cap yields
nothing; ~2000 for the fast model, ~4000 for the heavy one), retry once WITHOUT
the parameter if the provider rejects it, and on `finish_reason=length` retry
with a doubled limit before declaring the provider unhealthy. Probe each model
with one real call through the router and print `finish_reason` + content length:
the `/models` list alone proves nothing about behaviour.

## Upload format whitelist (Whisper-style STT)

Groq audio transcription accepts a FIXED extension list
(`flac mp3 mp4 mpeg mpga m4a ogg opus wav webm`); Telegram delivers voice as
`.oga`, and a bare file handle makes the SDK guess the MIME from the filename →
`400 unsupported_audio_format` (the error body lists the allowed types). This
reports as a hard failure, not a degraded path, so voice notes stop working
entirely. Normalise inside the one transcription call:

- `.oga`/`.opus` → upload as OGG with an explicit tuple
  `file=(filename, fileobj, mime)` = `("voice.ogg", fh, "audio/ogg")`;
- any extension outside the whitelist (`.mkv`, `.aac`, `.wma`, `.mov`, `.bin`) →
  ffmpeg-transcode to a temp MP3 (mono, 16 kHz) and `shutil.rmtree` that temp dir
  in a `finally`;
- never let the SDK infer name/MIME from the local path, and log the name you
  actually sent.

Verify against the live API with a real file in the offending format (generate
one with `ffmpeg -f lavfi -i "sine=frequency=440:duration=1" -c:a libopus x.oga`)
and assert an accepted response; a unit test over the suffix→MIME table passes
even when the provider still rejects the upload.

## Testing offline

Inject the transport, not the router: monkeypatch the single `call_chat(...)`
coroutine with a fake that pops a queue of `("text", ...)` / `("error", ...)`
items, and reset the settings/quota/cache singletons per case against fresh temp
paths (see the env-isolation lesson in `aiogram-offline-testing.md`). Assert the
plan, the fallback reason, the counters and the cache-hit path — no network.

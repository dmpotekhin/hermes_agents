---
name: standalone-telegram-bot
description: Use when running a self-hosted Telegram bot (aiogram).
version: 1.0.0
---

# Standalone Telegram Bot (self-hosted, long polling)

For bots built in this repo and started with `python bot.py` — aiogram 3 plus
OpenAI-compatible APIs (Groq/DeepSeek/etc.). NOT for bots wired into the Hermes
gateway; those live in `telegram-bot-setup` / `telegram-bot-gateway` /
`telegram-bot-assistant`.

## Project shape

```
bot.py          код бота (один файл — норм)
.env.example    шаблон без секретов
.env            реальные ключи, в .gitignore
requirements.txt, .gitignore (.env .venv __pycache__ .idea), .venv/
```

## Pre-flight before the first run

1. **Check the runtime env file, not the template.** Users routinely paste real
tokens into `.env.example`; the bot then exits with "не заданы переменные" and
the real cause is invisible. Verify the file the code actually loads:
`python3 scripts/inspect_env.py <project>/.env KEY1 KEY2`. If `.env` is missing
but `.env.example` was modified minutes ago — that is the tell — run
`cp .env.example .env`, then restore `.env.example` to the clean template
(patch it) and add `.gitignore` with `.env`.
2. **Never print secret values.** Report `KEY: заполнено (46 символов)` /
`ПУСТО` / placeholder — lengths only, never prefixes, suffixes or hashes of
prefixes. Any helper you write for this must follow the same rule.
3. **Token collision with a running gateway bot.** Two pollers on the same bot
token fight over `getUpdates` (one gets 409, the user's gateway breaks).
Compare the project token with the gateway token before starting; the bot id
(the part before `:`) is public, so print ids: equal id → stop and ask which bot
to use; different id → safe.
4. **Install with the pin, then check what resolved.** `pip install -r
requirements.txt` (not bare `pip install aiogram openai`, which grabs the latest
major — e.g. openai 3.x where the project pinned `<2.0.0` — i.e. a version the
code never ran against). Print resolved versions afterwards.

## Run and confirm readiness

- Start it through the terminal tool's own background mode
  (`terminal(..., background=true, notify=["Start polling"], workdir=<repo>)`),
  not by hand: `nohup`/`disown`/`setsid` wrappers are refused outright, so the
  process is not tracked and readiness never fires. Keep **`-u`**
  (`./.venv/bin/python -u bot.py`); with `-u` a `| tee /tmp/bot.log` pipe still
  writes the log within seconds, so tee is an acceptable way to keep the log at
  a fixed path. Without `-u` stdout is block-buffered: the log file sits at 0
  bytes for minutes while the bot already answers updates, which reads exactly
  like a bot that died at boot.
- Check for a leftover poller first: `pgrep -fl bot.py`. Two instances on one
  token fight over `getUpdates`, and the second one's log comes back **blank** —
  a blank log looks like a crash but is a duplicate instance. A `kill` issued
  inside a terminal call that got BLOCKED never ran, so verify the process list
  instead of trusting that the kill worked.
- Kill by PID, not by pattern: `pkill -f "python -u bot.py"` matches nothing
  when the interpreter is Homebrew's, because argv holds
  `.../MacOS/Python -u bot.py`. Take the PIDs from
  `ps -eo pid,command | grep "bot\.py"` and `kill` those; then re-list to prove
  the count went down, since a chatty `grep`/wrapper line can fake a survivor.
- Readiness is a line in the log, never "the process is alive": aiogram emits
  `Start polling` (dispatcher) and, right after, the bot identity line
  (`Run polling for bot @<username> id=<id>`). `notify=["Start polling"]` on the
  background start fires on the first; the identity line proves WHICH token is
  polling, which is what matters when several bots share the machine.
- Keep the exit notification on: a later crash is then reported instead of
  silently leaving a dead bot.
- Watch-pattern notifications from a process you already replaced keep arriving
  later (rate-limited replays name the OLD command/PID). Re-check the CURRENT
  process's log and count its tracebacks before diagnosing again; a dead
  process's log is history, not a new failure.

## Startup wiring needs its own smoke run

Suites import modules and call functions — they never execute `main()`/startup
logging, so a suite can be fully green while the bot dies on launch. After
adding or touching anything on the startup path (config logging, scheduler,
singletons that load state files), do the real thing: kill the poller, start
`exec ./.venv/bin/python -u bot.py`, and read the startup lines in the log
before reporting done.

Real failure mode: a startup log line read `settings.cache_enabled`, but that
flag lives on the *cache* module's settings object, not on the LLM settings
dataclass — `AttributeError` at boot with the whole offline suite passing. When
a helper formats config for a log line, take each field from the object that
owns it (`llm_router.get_cache_store().settings.enabled`), and exercise that
helper in a smoke run rather than only importing it.

## Access control (private bot)

Every bot built for this user ends up needing a gate — build it in from the
start, as one middleware, not as decorators scattered over handlers.

- Identify users by the numeric `from_user.id` only; username is mutable and
  must never be the (sole) basis of access. Log the id as the access reason.
- One `BaseMiddleware` registered on `router.message` as the first line of
  `build_router()`. Strip the `@botname` suffix before matching a command —
  Telegram delivers `/start@videotrscrb_bot`, so plain equality silently lets
  everything through while looking correct.
- Public commands (`start`, `help`, `whoami`, `access`) pass; media, `/yt`,
  `/save` and the allowlist commands are gated. `OWNER_TG_ID` always passes, and
  owner-only commands answer a distinct "owner only" message so a non-owner can
  tell it apart from a plain denial.
- Default mode `allowlist`; `off` only when explicitly set; an unknown value
  normalizes to `allowlist` (privacy must not be disabled by a typo).
- Group access via `bot.get_chat_member(...)` for status in
  `{member, administrator, creator}`; any API error means deny, never an
  exception out of the middleware, and cache the verdict ~60 s (Turbo limits).
- Effective list is `ALLOWED_USER_IDS` ∪ JSON file; file writes are atomic
  (`mkstemp` in the same dir + `os.replace`), the file is created on startup if
  missing, and a corrupt one is treated as empty, not as a crash.
- `/deny` on an id that comes from `ALLOWED_USER_IDS` must say it can only be
  removed in `.env` — never report a removal that did not happen.
- Settings must be injectable: module-global settings + `set_access_settings()` /
  `set_bot_instance()`, and the settings stored on `Config` (`config.access`) so
  handlers get them via `workflow_data`.
- One startup log line (mode, owner id, allowed count, group id) plus a warning
  when `allowlist` + empty list — that line is the readiness evidence for the
  feature.

Env contract, mode table, check order, storage format and command semantics:
`references/access-control.md`. `references/aiogram-offline-testing.md` — how to
test the gate for real without a token.

## Verify the pipeline yourself before asking the user to test

A bot cannot send itself updates as a user: messages a bot sends never arrive
as updates for its own token, so "send /start" cannot be automated. Test each
stage directly with the real keys from `.env`:

- speech: `say -o /tmp/speech.aiff -v <voice> "<text>"` → your ffmpeg path →
  the transcription function; `say -v '?' | grep ru_RU` lists voices;
- request shape: monkeypatch the SDK client with a fake that captures kwargs and
  assert model/temperature/max_tokens/base_url/truncation marker;
- the access gate: drive the real `Dispatcher.feed_update` with a fake session
  and assert the exact reply per mode, command and member status — recipe in
  `references/aiogram-offline-testing.md`;
- error paths: call with a deliberately invalid key and assert your own
  exception type comes out (a 401 proves the wrapper catches it).
- a new section's service layer end to end on real providers: call the entry
  function with the real `.env`, the real `Config` object and the real vault,
  then check provider/model (the primary answered, not the fallback), token
  count, duration, and that a second identical run comes from cache (~0.3 s vs
  ~10 s). Prove the call went THROUGH the router: the daily quota counter in the
  startup log must rise by exactly the number of live calls — if it does not, the
  new code dialled the provider directly and now bypasses quotas and cache. Read
  the saved artifact (file, frontmatter, tags) from disk; a log line saying
  "сохранено" is not evidence.
- delete the throwaway verification script before `git add`: probes with
  absolute paths and hardcoded ids must not land in the repo.

Only then hand the user two actions — open the bot, send `/start` and a media
file — and read the process log while they do it.

## The user says "the bot hung / no answer"

Diagnose with facts, in this order — the complaint names the wrong component
more often than not:

1. **Liveness is a stack, not a vibe.** `ps -eo pid,etime,command | grep bot.py`
   (exactly ONE poller) and `sample <pid> 2 -f /tmp/bot_sample.txt`; the main
   thread sitting in `select_kqueue_control_impl` with no httpx/ssl/telegram
   frames means the event loop is alive and idle — nothing is stuck on the
   network. A frame inside a network call is the real hang.
2. **Reconcile the claimed wait against log timings** before hunting the
   collector: filter the log by time (`awk '$2 >= "HH:MM:00"'`) and find the
   stage's done-line. Stage finished → the problem is delivery/reporting, not
   the worker. No stage start-line after the button tap → the work never began
   (check the "already running" busy flag on the service).
3. **Delivery cannot be proven from the log.** aiogram 3 talks over aiohttp, so
   an httpx-configured log shows every outbound HTTP call EXCEPT Telegram's:
   silence there proves neither delivery nor failure. Verify the channel by hand
   (POST `sendMessage` to the owner's `chat_id` with the token read out of
   `.env` in the same shell, never printed) and give manual handlers their own
   log lines (`stage.start` / `stage.done` / `stage.sent chars=`) so the next
   complaint is diagnosable instead of blind.
4. **A status message that is only SENT, never edited or deleted, hangs in the
   chat forever and is read as a freeze.** "Собираю новости…", "Скачиваю…" sent
   as its own message, while the result goes to a different message (a shared
   renderer edits the previous screen) leaves the user staring at the stale
   status for minutes. Rule: hold the status object in a variable and replace it
   with the result (`status.edit_text(...)`); if that fails (too long, too old),
   delete the status and send the result as a new message — never leave it.
5. **`grep -i error` over a bot log lies.** Pipeline/agent lines carry `error=-`
   on INFO level and match the word; filter by level
   (`grep -E "ERROR|CRITICAL|Traceback"`) or exclude the `error=-` shape.

When the fix touches a long-running handler (collect, sync, export), add the
handler's own start/done/sent log lines in the same change — leaving them out is
what makes the next identical complaint cost another full investigation.

## Handing a new section to the user

A reply keyboard belongs to the bot's LAST message, so the client keeps
rendering the old bottom rows until the bot sends a new one: adding a button to
`main_reply_keyboard()` and restarting the poller does NOT make it appear.
Instruct the user to restart the bot **and send `/start` (or `/menu`)**, and say
which row the button now sits in, so they do not hunt for it. A tap on a stale
keyboard only sends its text — so hand-typing the button text works as a
fallback, and text filters (`F.text == BTN_*`) match it; offer that when an
emoji-heavy button is easy to miss in the client. A bottom-row button that opens
a section must clear the FSM state first, or a half-finished flow (waiting for a
value) swallows the press.

## Date-boundary tests: one green run proves nothing

Native date math («next week» = next Monday, «tomorrow», ISO week edges) passes
for most of the week and flips on one day: `today + timedelta(days=7 -
today.weekday())` returns TOMORROW on Sunday, so «перенести на следующую неделю»
quietly became «завтра». A suite run in the morning can be green and the same
suite red after midnight — check the calendar before hunting the diff. Test the
PROPERTY, not the moment: inject `today` (e.g. monkeypatch the module's
`today_for` helper) and loop over all seven weekdays, asserting what must hold
(lands on Monday, at least two days ahead) instead of `due > tomorrow`.

## macOS TTS is not a transcription-quality benchmark

`say` output is robotic: Whisper mangles proper nouns (`FastAPI` → `FSTP`) and
drops URLs, and the LLM then analyzes that garbage faithfully. Do not report it
as an API defect. Quality is only meaningful on real human speech; for technical
content pass Whisper `prompt=` with a vocabulary hint (library/framework/tool
names) to bias decoding — expose it as an env var (e.g. `WHISPER_PROMPT`,
empty default) so behaviour is unchanged until the user opts in.

## Confirming a GUI app really opened

A screenshot showing no window is not evidence: `screencapture` returns
wallpaper-only when the calling process lacks Screen Recording permission (the
tell is a capture with no menu bar and none of the user's windows). List the
real on-screen windows instead:

```
swiftc -O scripts/winlist.swift -o /tmp/winlist && /tmp/winlist [owner-substring]
```

The first compile prints a "did not find a prebuilt standard library" remark and
takes about a minute — that is normal, not a failure. Window titles come back
empty without Screen Recording permission; pid/owner/geometry are always there.
Cross-check with the app's own log (e.g.
`~/Library/Logs/JetBrains/PyCharm2026.1/idea.log`) to see whether it actually
opened the project.

## Shell discipline in this environment

- Installs and `python -c` may need approval; run them once and continue rather
  than re-issuing variants.
- Long quote-heavy inline one-liners trip the "command parser limit" blocklist.
  Put logic in a `.py`/`.swift` file and run the file; keep shell lines short.
- GUI apps: launch with `open -a "<App>.app" <path>`; a second launch of the
  same IDE just hands off to the running instance.

## Stub-importing code whose dependencies are not installed

To exercise a module's own logic without its third-party deps: inject stub
modules into `sys.modules` (aiogram/openai/...), then register the module under
its own name **before** `exec_module` — `sys.modules["bot"] = module`. Without
that, `@dataclass` fails with
`'NoneType' object has no attribute '__dict__'`.

## Logging for battle testing

Log each stage with the durations that matter (download, ffmpeg, each API,
lengths of transcript and analysis) and keep API keys out of logs. When a stage
fails, the user-facing message stays short and the traceback goes to
`logger.exception` only.

## scripts/ and references/

- `scripts/inspect_env.py` — which env keys are set, lengths only, placeholder
  detection (never values).
- `scripts/winlist.swift` — list on-screen windows with pid/owner/bounds.
- `references/access-control.md` — access gate for a private bot: env contract,
  modes, middleware decision order, atomic allowlist storage, command semantics,
  test hooks.
- `references/aiogram-offline-testing.md` — real `Dispatcher` + fake session
  harness with the `GetMe` / `ChatMember*` / env-isolation pitfalls.
- `references/llm-routing-and-budgets.md` — free-primary/paid-fallback layer for
  a bot's LLM calls: plan-first routing, daily quotas, content-hash cache,
  silence skip before transcription, degraded payload, per-user `/mode` + `/usage`,
  and provider drift (retired model ids, reasoning models returning empty
  content, Whisper's upload-format whitelist vs Telegram `.oga`).
- `references/github-solution-search.md` — GitHub Search API as the first step of
  "есть ли уже готовое?": query qualifier, shrinking word chain, junk filters,
  what to hand the LLM, graceful degradation on rate limits.
- `references/llm-report-sections.md` — adding a new analyzed section to the
  bot's LLM report (schema → prompt rules → normalize → two renderers → settings
  → external context file → tests with backward compatibility).
- `references/collector-health-and-feeds.md` — an RSS/API collector inside the
  bot: final feed URLs (a 301 chain burns the source's timeout), the curl probe,
  and the dry run on a WAL-aware DB copy with the expensive layer disabled.
- `scripts/collect_check_on_copy.py` — run one collection against a copy of the
  live DB with the LLM layer off; prints ok/failed/`source_errors`/elapsed and
  exits 1 on any failed source.

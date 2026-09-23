# Verification ladder for a freshly written Python service

Worked recipe for the five rungs. Rung 1 costs seconds and no install; rung 5 is the one that
catches "fatal error exits 0". Do the cheap rungs first, and re-run all of them against the
current bytes after every edit.

## Rung 1 — stub the third-party imports, test pure logic

```python
import importlib.util, sys, types

def _stub(name: str, **attrs):
    module = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(module, k, v)
    module.__getattr__ = lambda item: type(item, (), {"__init__": lambda self, *a, **k: None})
    sys.modules[name] = module
    return module

aiogram = types.ModuleType("aiogram")
aiogram.Router = _router_class()      # must return a FRESH class per call
aiogram.Dispatcher = _router_class()
aiogram.F = _filter_builder()         # magic-filter stub, see __or__ trap
sys.modules["aiogram"] = aiogram
sys.modules["aiogram.exceptions"] = _stub("aiogram.exceptions", TelegramBadRequest=type("TelegramBadRequest", (Exception,), {}))
# ... same for aiogram.filters, aiogram.types, dotenv, openai

spec = importlib.util.spec_from_file_location("bot", "/abs/path/bot.py")
bot = importlib.util.module_from_spec(spec)
sys.modules["bot"] = bot               # BEFORE exec_module — dataclass needs it
spec.loader.exec_module(bot)
```

**Trap 1 — `sys.modules[<name>] = module` before `exec_module`.** Otherwise a `@dataclass` in the
target dies with `AttributeError: 'NoneType' object has no attribute '__dict__'` raised from
`dataclasses._is_type` (it resolves the defining module via `sys.modules.get(cls.__module__)`).
The traceback points at the target file, so it reads like a real bug in your code.

**Trap 2 — magic-filter stubs need `__or__`.**

```python
def _filter_builder():
    class _MagicFilter:
        def __getattr__(self, item):
            return self
        def __or__(self, other):
            return self

    class _F:
        video = _MagicFilter()
        video_note = _MagicFilter()
        document = _MagicFilter()
    return _F()
```

Exposing `F.video` as a plain string breaks `@router.message(F.video | F.video_note | F.document)`
with `TypeError: unsupported operand type(s) for |: 'str' and 'str'`. Real `F` attributes are
filter objects, so the stub must be too.

What rung 1 can pin: `split_text` chunk boundaries and max length, `extract_urls` order/dedupe,
`load_config` missing-var and bad-int branches, media-type resolution, `_default_suffix`,
temp-file writers.

## Rung 2 — real deps, from the pins

```bash
pip install -q -r requirements.txt
python -c "import aiogram, openai; print('aiogram', aiogram.__version__, '| openai', openai.__version__)"
```

Loose `pip install openai` resolved **3.16.2** while the project pinned `openai>=1.55.0,<2.0.0`;
`-r requirements.txt` then downgraded it to **1.109.1**. Testing against the unpinned major is not
evidence about the deliverable.

Framework internals worth asserting against the real library:

```python
router = bot.build_router()
observed = [o.callback.__name__ for o in router.message.handlers]          # registration
for h in router.message.handlers:
    print(h.callback.__name__, list(inspect.signature(h.callback).parameters))
# ['message', 'config'] proves the DI kwarg matches dispatcher.workflow_data's key
fs_file = bot.FSInputFile(path, filename="transcript.txt")                 # constructor kwarg exists
```

## Rung 3 — live provider probes

**(a) Invalid key is the cheap proof of the error mapping.**

```python
try:
    asyncio.run(bot.analyze_with_deepseek("тест", cfg_with_key("sk-invalid-key-for-test")))
except bot.AnalysisError as exc:
    print("AnalysisError on bad key OK:", exc)
```

This exercises the real SDK's exception hierarchy (an `AuthenticationError` raised as
`APIError`) through your wrapper — the mapping is asserted, not assumed. Same probe for the
second provider.

**(b) Capture the request payload with a fake client — no tokens spent.**

```python
captured = {}

class _FakeClient:
    def __init__(self, *a, **kw):            captured["client_kwargs"] = kw
    async def __aenter__(self):              return self
    async def __aexit__(self, *exc):         return False
    class chat:
        class completions:
            @staticmethod
            async def create(**kw):
                captured.update(kw)
                return types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="готовый анализ"))])

real = bot.AsyncOpenAI
bot.AsyncOpenAI = _FakeClient
analysis, truncated, seconds = asyncio.run(bot.analyze_with_deepseek("технология. " * 6000, cfg))
bot.AsyncOpenAI = real
assert captured["temperature"] == 0.2 and captured["max_tokens"] == 3000
assert captured["client_kwargs"]["base_url"] == "https://api.deepseek.com/v1"
assert "[Транскрипт был обрезан для анализа]" in captured["messages"][1]["content"]
```

The fake must support `async with` when the wrapper opens the client that way, and must be
restored afterwards.

**(c) Key handling.** `~/.hermes/.env` may hold a stale copy of the same var; `load_dotenv` never
overwrites an existing var, so load the profile file with `override=True`. Never print the value —
print `bool(key)`.

## Rung 4 — real external binary roundtrip (ffmpeg)

```python
video = os.path.join(d, "test.mp4")
code, err = await bot._run_ffmpeg([
    "ffmpeg", "-y",
    "-f", "lavfi", "-i", "testsrc=size=320x240:rate=15:duration=2",
    "-f", "lavfi", "-i", "sine=frequency=440:duration=2", "-shortest",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", video,
])
assert code == 0 and os.path.getsize(video) > 0
audio, seconds = await bot.extract_audio(video, d)      # primary branch
assert audio.endswith(".mp3") and os.path.getsize(audio) > 0
```

Then exercise the other two branches in the same run: the fallback encoder explicitly (run the WAV
command by hand and assert non-empty output) and garbage input (`open(p,"wb").write(b"not a video")`
→ your `AudioExtractionError`, not a raw `CalledProcessError`/traceback).

## Rung 5 — entry point fatal path

```bash
.venv/bin/python app.py; echo "exit_code=$?"
```

Expect: one human-readable line, no traceback, `exit_code=1`. The generator bug this catches:

```python
if __name__ == "__main__":
    try:
        asyncio.run(main())          # main() does `raise SystemExit(1)` on ConfigError
    except (KeyboardInterrupt, SystemExit):   # <-- swallows it; process exits 0
        pass
```

Catch `KeyboardInterrupt` only, and keep `raise SystemExit(1)` in `main()` so a missing token or
missing binary is a non-zero exit.

## Defect classes these rungs actually caught

- Fatal config error exiting 0 (rung 5).
- A two-pass URL extractor emitting links in *pass* order, not text order — the unit check asserted
the expected list order and failed. Fix: collect `(match.start(), url)` from both regexes and sort by
position before deduping. When a helper scans the same text with several patterns, order the results
by source position.
- An ffmpeg command that looked correct but was only ever run against a synthetic happy path:
the broken-input branch was never exercised until rung 4.

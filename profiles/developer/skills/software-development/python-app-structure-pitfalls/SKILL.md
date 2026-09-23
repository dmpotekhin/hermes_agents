---
name: python-app-structure-pitfalls
description: Use when Python module/import/install steps misbehave.
---

# Python app structure pitfalls

Verified, environment-independent traps hit while building modular async Python
services (FastAPI + SQLite + external API adapters). First surfaced building
travel-blog-app; reproducible anywhere.

## 1. Module name that collides with an existing package imports the package

**Symptom:** `from modules.media import optimize_image` resolves a *package*
(`modules/media/__init__.py`) instead of the `modules/media.py` module you just wrote —
the symbol is missing or the empty package's exports get used.

**Cause:** Python resolves a package (directory) over a same-named module (.py).

**Fix:** before naming a module, check for BOTH `modules/<name>.py` and `modules/<name>/`.
If an empty placeholder package exists, delete the directory (`rm -rf modules/<name>`)
and keep the `.py` module. Confirm the import afterward.

## 2. Circular import between two modules → lazy import inside the method

**Symptom:** ImportError when A imports B and B imports A (e.g. a service layer
`base.py` ↔ a sibling `cache.py`).

**Cause:** both import each other at module top, so whichever loads first hasn't
finished defining its names.

**Fix:** keep shared dataclasses/types in one module and import the other LAZILY,
inside `__init__` or the method that needs it. Use `TYPE_CHECKING`-only imports for
pure types. Never let two modules import each other at top level.

## 3. Long write_file payloads can be truncated mid-docstring

**Symptom:** the written file is cut off inside a multi-line module docstring, leaving
an unterminated `"""` → SyntaxError. Bit repeatedly on large single-block writes.

**Fix:** keep module docstrings to one line; write large new files as a compact first
pass, then build up with targeted `patch` edits (or small `write_file` + `patch`)
instead of one giant `write_file` payload. If a write looks suspiciously short, read
it back and re-verify.

## 4. Heavy/network pip install can hang and trip a terminal approval guard

**Symptom:** `pip install ...` — or an import that resolves a binary on first use
(e.g. imageio-ffmpeg fetching ffmpeg) — hangs on the network and the terminal tool
returns a hard "stop and wait for the user" block.

**Fix:** run slow/network installs as `terminal(background=true, notify_on_complete=true)`
and keep building meanwhile. Verify installs via `search_files` on
`.venv/lib/python3.11/site-packages` (target=files) rather than a hang-prone `import`.
Prefer pure-Python wheels (httpx, Pillow, numpy, moviepy) over SDKs that trigger native
builds (e.g. an SDK that pulls `cryptography` on a machine without Xcode CLT).

## 5. Layering: canonical types in the lower layer, feature packages re-export

**Symptom:** a new feature package (`modules/<feature>/`) defines its own enums/models,
but the DB layer (`core/database.py`) is the only module allowed to write SQL and now has
to import them → `core` → `modules` import, which inverts the layering and risks a cycle
(services already import `core`).

**Fix:** keep the canonical enums/models in the module everyone already imports
(`core/models.py`) and make `modules/<feature>/{enums,models}.py` thin re-export facades
carrying the feature-flavoured names. SQL stays in `core/database.py`; give the feature
package a `database_helpers.py` facade that only delegates to `Database` methods.
Verified on travel-blog-app ADR-107 (carousel factory) — `core` imports no `modules`.
Also keep a single binding boundary: one `_sql_value`-style helper, not per-call casts.

## 6. sqlite3 cannot bind `datetime` or `str`-Enum values

**Symptom:** `sqlite3.InterfaceError` / "Error binding parameter N: type 'X' is not
supported" from a dynamic update method that passes a model field straight into `?`.

**Cause:** `sqlite3` binds only int/float/str/bytes/None. `datetime` is unsupported, and
`enum.Enum` — even `class Status(str, Enum)` — is not auto-unwrapped as a *value*.

**Fix:** unwrap/convert at the binding boundary and route every dynamic `UPDATE` value
through it:

```python
from datetime import datetime

def _sql_value(value):
    value = getattr(value, "value", value)   # unwrap str-Enum
    if isinstance(value, datetime):
        return value.isoformat()
    return value
```

Readers must convert back (`Status(row["status"])`) so callers keep real enum types.
Model fields can stay enums: a pydantic model reconstructs them on read.

## 7. pydantic enum field: canonicalise with a `before` validator

`field: str = SomeEnum.X.value` silently accepts typos; `field: SomeEnum` rejects the
friendly names a spec or human writes (`"symptom_list"`, `"code_fix"`). Do both — type
the field as the Enum plus a normalising validator:

```python
@field_validator("slide_type", mode="before")
@classmethod
def _canonicalize_slide_type(cls, value: object) -> object:
    if isinstance(value, SlideType) or value is None:
        return value
    raw = normalize_slide_type(str(value))          # alias table -> canonical value
    try:
        return SlideType(raw)
    except ValueError as exc:
        raise ValueError(f"Unknown slide type: {value!r}") from exc
```

Result: aliases in JSON/payloads validate, the stored value is canonical, and a typo
fails loudly instead of being persisted. Put the validator **after** the field
declarations — a method between annotated fields is legal but reads badly.

## 8. Triage new-test failures with `--tb=line`, classify, then edit

`.venv/bin/python -m pytest tests/test_new_*.py -q --tb=line` gives one line per failure.
Sort every failure before touching anything:

- **(a) the test invented an API detail** — made-up table/index names, assumed return keys,
  assumed async vs sync. Fix the test, reading the real name from the source first.
- **(b) the source is genuinely inconsistent** — fix the source, never relax the test.
  Real case: `create_job` recorded `warnings=["source not resolved yet"]` on the job but
  `["resolution pending (phase 2)"]` on the source record; the test comparing the two
  exposed it, and the fix was to make ONE list the single source of truth.

Guessing schema object names is the most common (a): grep `^CREATE TABLE IF NOT EXISTS` and
`CREATE INDEX IF NOT EXISTS` in `core/database.py` and assert only on what is there.
Run the command as a **single plain command** — wrapping it in a pipe (`| tail`, `| head`)
hands back the pipeline's exit status and hides pytest's; and a full-suite run afterwards
is what proves backward compatibility (count baseline → count after).

## 9. A status-only enum helper leaks `str(Enum)` into TEXT columns

**Symptom:** rows read back as `CarouselVertical.QA` / `CarouselStatus.RENDERING` instead of
`qa`; the pydantic model then rejects the value on read, or filters silently never match.

**Cause:** a helper existed for the *status* axis only (`status_value`), so a second enum axis
(vertical, source type) got `str(value)` at the DB boundary. `str(SomeStrEnum.X)` is
`"SomeStrEnum.X"` unless the class overrides `__str__`.

**Fix:** one generic helper in the feature's `enums.py`, used for **every** enum written to a
TEXT column (and for str-form comparisons in state machines):

```python
from enum import Enum
from typing import Any

def enum_text(value: Any) -> str:
    """str-форма любого enum для TEXT-колонок и логов."""
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)
```

Grep the feature for `str(` at DB/JSON boundaries after adding a second enum axis — the old
helper's name tells you nothing. Alias maps (`SLIDE_TYPE_ALIASES`) stay built on the canonical
enum, so canonicalisation and storage agree.

## 10. Sync code calling an async provider → "This event loop is already running"

**Symptom:** `RuntimeError: This event loop is already running` (asyncio) when an async
function is invoked from a sync function that an **async** caller reached — e.g. a renderer
that calls `asyncio.run(provider.background(...))` while the service already owns the loop.

**Cause:** `asyncio.run()` cannot be nested inside a running loop.

**Fix:** expose both entry points on the ABC rather than hiding the sync/async boundary:

```python
class BaseSlideRenderer(ABC):
    @abstractmethod
    def render(self, ...) -> RenderedSlide: ...          # deterministic, no provider calls

    async def render_async(self, ...) -> RenderedSlide:  # default: delegate
        return self.render(...)
```

The concrete renderer overrides `render_async` to `await` the provider and then paint; plain
`render()` paints the fallback and records `warnings=["provider skipped in sync context"]`.
The service always awaits `render_async`, so a caller-supplied stub that implements only
`render` still works (the default implementation forwards). Do NOT "fix" it with
`run_until_complete` on the running loop — that just moves the crash.

## 11. A `set_X(None)` reset that builds from a default argument ignores config

**Symptom:** a module-global singleton factory `set_store(None)` is called to
"reset" the object, but state files appear in the project cwd instead of the
configured path, and code that points the path at a temp dir keeps reading the
real file.

**Cause:** the reset branch constructs the object with its parameter default
(`Store()`), which is the hardcoded default path — the `from_env()` / settings
lookup only runs on the other branch.

**Fix:** every reset path rebuilds through the same config loader as normal
startup:

```python
def set_store(store: Store | None = None) -> Store:
    global _store
    with _lock:
        _store = store if store is not None else Store(get_settings().state_path)
    return _store
```

Same rule for `set_settings(None)` / `set_client(None)`: "reset" means "recompute
from the current environment", never "use the function default".

## 12. After a refactor, sweep what the refactor orphaned

Replacing a helper leaves its prompt constants, status strings and error
messages defined but unreferenced — they survive review and look live to the
next session.

**Fix:** before calling the refactor done, count references for every name the
old path used; a `grep -c NAME` result of 1 means "definition only" → delete it
together with its comment. Sweep the whole cluster (`PROMPT`, `MAX_*`,
`STATUS_*`, error strings), not just the function — an orphaned trio is invisible
in a diff but misleads the next reader. Keep genuinely public types (exception
classes other code may catch) even when unreferenced internally.

## Related principle: test against mock providers, not real keys

For API layers (AI, publishers), make the factory return a deterministic mock when
`app.dry_run` is on so tests run without network/keys, and assert the mock's
shape (non-empty content, per-platform drafts, honest manual/`published` states).

## References
- travel-blog-automation-platform `references/pitfalls.md` — project-specific
  aiosqlite-shutdown and EXIF/GPS lessons in the same class.
- travel-blog-automation-platform `references/carousel-factory.md` — worked example of
  §5 (canonical types in `core`, façade package, single `_sql_value` boundary), §6/§9
  (enum storage), §10 (sync/async renderer split) and §8 (the warnings-inconsistency fix),
  with the additive-table/index naming to assert on.

# Task 4 — Kids Learn: Python code sandbox & check service

Brief gave verbatim `sandbox_service.run_code()` + `check_service.py`. Both were only a
"design guide" and the sandbox had TWO defects the brief's own test steps would have caught.

## Defect 1 — `__builtins__` is a MODULE, not a dict, in a script

The brief's preamble did:
```python
__builtins__ = {k: v for k, v in __builtins__.items() if k not in {...}}
```
In a script run via `python3 file.py`, `__builtins__` is the `builtins` **module**, and
`module.items()` raises `AttributeError: module 'builtins' has no attribute 'items'`.
Result: **every code task failed** (`check_answer` for `type=="code"` returned `False`).

Minimal patch is `vars(__builtins__).items()` — but that still does NOT fix security (see Defect 2).

## Defect 2 — reassigning `__builtins__` at module top-level does NOT restrict builtins

Even after the `.items()` fix, forbidden names stayed reachable:
- `print(open)` → `<built-in function open>` (still defined)
- `open('x')` → `FileNotFoundError`, NOT `NameError` (proof it was never stripped)
- `print(dir)`, `print(getattr)`, `print(vars)` all still printed `<built-in function ...>`

Reason: CPython re-binds a script's module-level `__builtins__` to the real builtins module on
import, so top-level reassignment is bypassed for name lookup. This is a **false sense of security**
and easy to ship believing you've blocked `open`/`eval`/`subprocess`.

## Robust fix — restrict via the `globals` argument to `exec`

A **dict-valued `__builtins__` passed as the `globals` arg to `exec`/`compile` genuinely shadows
lookups** — unlike module-level reassignment. Pattern that actually blocks:

```python
FORBIDDEN = {"__import__","open","eval","exec","compile","input",
             "globals","locals","vars","dir","getattr","setattr",
             "delattr","hasattr","breakpoint","exit","quit"}
_FORBIDDEN_LIT = ", ".join(repr(f) for f in FORBIDDEN)

# This runs inside the subprocess file; the whitelist dict is built in the runner's own
# trusted scope, then used as __builtins__ for the USER'S code only.
PRELUDE = f"""
import builtins as _b
ALLOWED = {{k: getattr(_b, k) for k in dir(_b) if not k.startswith('__') and k not in {{{_FORBIDDEN_LIT}}}}}
import math as _math, random as _random
def _run(_code):
    _g = {{'__builtins__': ALLOWED, '__name__': '__main__', 'math': _math, 'random': _random}}
    exec(compile(_code, '<sandbox>', 'exec'), _g)
"""
# run_code appends:  "\n_run(" + repr(code) + ")"
```

Verified behavior:
- `open`, `eval`, `exec`, `__import__`, `dir`, `getattr`, `vars` not defined → `NameError: name 'X' is not defined`
- `os`/`sys` not reachable (no `__import__`)
- `math.*`, `random.*` pre-injected as globals → work by direct reference
- Timeout still enforced by `subprocess.run(timeout=5)` on the outer subprocess

## Gotcha: blocking `__import__` also kills the `import` statement
`import math` inside user code fails with `ImportError: __import__ not found` because `import`
routes through `__import__`. That is consistent with a whitelist model: pre-inject the allowed
modules as globals; user code refers to `math`/`random` directly rather than `import`-ing.

## String-formatting pitfall while building the preamble
Mixing `%`-formatting with `{{`/`}}` escape sequences (which only `.format()`/f-strings collapse)
produces invalid code (`{{` stays literally `{{` under `%` → `_g = {{'__builtins__': ...}}` is a
set literal containing a dict → `TypeError: unhashable type: 'dict'`). Use an f-string with
`{{...}}` for literal braces and `{{{expr}}}` for interpolated dict literals, and keep literals
built with `", ".join(repr(x) for x in ...)`.

## Lesson for spec-driven work
When a brief claims a security/safety property ("blocks dangerous builtins"), **verify it
empirically** (try `print(open)` in the sandbox) rather than trusting the code shape. The
failure symptom (code tasks returning `False`) looks like a logic bug but is really a broken /
non-restricting sandbox. Fix intent-preserving: same `FORBIDDEN_BUILTINS` set, same subprocess +
timeout isolation, same `run_code -> str` contract — only the mechanism changed.

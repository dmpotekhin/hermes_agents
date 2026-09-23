# A launcher that changes cwd/sys.path breaks project-root imports

## Symptom

`streamlit run ui/dashboard.py` fails with
`ModuleNotFoundError: No module named 'core'` (or `modules`) even though `core/` and
`modules/` live in the project root and you launched from the project root. The same
script imports fine under `python -c` from the project root.

## Cause

Streamlit executes the script by path and puts the script's OWN directory (`ui/`) on
`sys.path`, NOT the project root where the packages live. Any tool that prepends the
script dir to sys.path (rather than using the shell's cwd) triggers this.

## Fix

Bootstrap the project root at the very top of the script, before ANY project import:

```python
import os, sys
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
```

`__file__` is the actual script path, so `_ROOT` is correct regardless of where the
launcher runs from.

## Verify under the SAME launch mode as production

A module may import cleanly via `python -c` / `python script.py` from the project root but
fail under `streamlit run`. Test by simulating the launcher's sys.path (put only the `ui/`
dir on sys.path, then `import dashboard`), or just launch streamlit and curl the port.
Don't trust a `python -c` import as proof.

## Same class of bug

Any launcher/web-server that sets cwd or sys.path differently from the shell (Docker
WORKDIR, uvicorn `--app-dir`, systemd `WorkingDirectory`) reintroduces this. When a
package-based script fails to import under a runner, ASK "what's on sys.path / what's cwd
under the runner?" before chasing imports.

## Worked example

travel-blog-app `references/streamlit-dashboard.md` (under
travel-blog-automation-platform) has the concrete fix and the dashboard wiring.

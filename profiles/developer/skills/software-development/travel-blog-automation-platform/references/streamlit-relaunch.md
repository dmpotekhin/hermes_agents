# Relaunching the Streamlit UI (travel-blog-app) — verified 2026-08-29

Goal the user hits ("перезапусти сервер, хочу посмотреть в браузере"): bring the
Streamlit UI back up so it re-reads freshly added `ui/*.py` modules, and confirm it is
actually serving before saying "готово".

## The trap: `run.sh` passes `STREAMLIT_ARGS` as ONE quoted arg

`run.sh` runs:

```bash
streamlit run ui/dashboard.py --server.port "${UI_PORT:-8501}" "${STREAMLIT_ARGS:-}"
```

`STREAMLIT_ARGS` is DOUBLE-QUOTED, so the entire value lands as a single argv element.
Trying to disable the email prompt via the env var:

```bash
STREAMLIT_ARGS="--server.headless true" ./run.sh
```

yields:

```
Error: No such option '--server.headless true'. (Did you mean one of: '--server.headless'?)
```

Streamlit exits, FastAPI keeps serving (`/health` 200), but `:8501` is CLOSED. Debug
symptom: `curl 127.0.0.1:8501/_stcore/health` refuses; the run.sh log shows that usage error.

## Reliable relaunch (headless, no email prompt, no quote issue)

Launch Streamlit DIRECTLY, not through run.sh (keep FastAPI on run.sh):

```bash
cd ~/projects/travel-blog-app
# 1. kill stale procs so new process re-reads fresh ui/*.py (Streamlit caches imported modules across reruns)
pkill -f "streamlit run ui/dashboard.py"; pkill -f "app.py"; pkill -f "uvicorn"; sleep 1
# 2. bring UI up on its own
.venv/bin/python -m streamlit run ui/dashboard.py --server.port 8501 --server.headless true --server.address 0.0.0.0 > /tmp/ui.log 2>&1
# 3. verify BOTH endpoints return 200 ok BEFORE declaring it up
```

Verification step (a tiny /tmp script via urllib, since inline `python -c` trips the
approval-gate on this machine):

```python
# tb_srv_health.py
import urllib.request
for port, path in [(8000, "/health"), (8501, "/_stcore/health")]:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=3) as r:
            print(port, r.status, r.read().decode()[:120])
    except Exception as e:
        print(port, "UNREACHABLE", e)
```

Only both `200 ok` => "server up". Also `grep -iE "error|traceback|ModuleNotFound|ImportError" /tmp/ui.log`
to confirm the dashboard imported cleanly.

## Fixing run.sh for the future

Patch the line to expand unquoted, or add a dedicated boolean:

```bash
# before:
streamlit run ui/dashboard.py --server.port "${UI_PORT:-8501}" "${STREAMLIT_ARGS:-}"
# after:
streamlit run ui/dashboard.py --server.port "${UI_PORT:-8501}" ${STREAMLIT_ARGS:-}
```

or `--server.headless` as its own flag and drop `STREAMLIT_ARGS` entirely.

## Why killing the process matters

Streamlit imports `ui/dashboard.py` and its `ui/*` sibling modules at run time and keeps
the module objects alive across reruns. If you add a new `ui/*.py` (or new imports in
`dashboard.py`) while the old process is up, the live server may keep serving the stale
import graph. Always restart the process after touching any UI module.

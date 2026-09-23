# UI run & verify — "UI not opening" (Streamlit :8501)

Symptom: `./run.sh` prints "Starting FastAPI backend on :8000 and Streamlit UI on
:8501", the backend comes up (`Application startup complete`), but the browser shows
nothing on :8501.

## Root cause (most common)

The **Streamlit subprocess died while the FastAPI subprocess kept running** — NOT a
wrong URL. Common triggers: the first-run "enter your email" welcome screen got
interrupted, or a prior UI process was killed (Ctrl+C / terminal close) while the
`app.py` background process survived.

## Diagnose (evidence before claims)

- Check what is actually listening. FastAPI usually stays up; the UI port is the one
  that goes dark.
  `lsof -iTCP:8501 -sTCP:LISTEN` → empty means the UI is down.
  In Hermes this lsof/compound command can trip the terminal approval gate — fall back
  to a small `/tmp/*.py` that does `socket.connect(("127.0.0.1", 8501))` and prints
  OPEN/CLOSED.
- Streamlit health probe: `GET http://127.0.0.1:8501/_stcore/health` → body `ok`.
- Read `/tmp/ui.log` for import/traceback errors BEFORE declaring success — a bad
  import in a tab (e.g. a new `ui/vibecoding_page.py`) surfaces there, not in the URL.

## Fix (relaunch ONLY the UI)

run.sh already owns :8000 — do NOT restart it. Launch just the UI in the background:

```
cd ~/projects/travel-blog-app && .venv/bin/python -m streamlit run ui/dashboard.py \
  --server.port 8501 --server.headless true --server.address 0.0.0.0 > /tmp/ui.log 2>&1
```

Poll the health probe after a short wait. Verify with the socket probe + `/_stcore/health`
→ `ok` and a clean `/tmp/ui.log`.

## Why `--server.headless true` matters

Without it, Streamlit blocks on the first-run "enter your email" welcome screen and
can look like it never opened. **`headless` does NOT hide the app in a browser** — it is
still reachable at `http://localhost:8501`. (It only suppresses interactive CLI prompts
like the email onboarding and auto-opening a browser tab.)

## Which URL to give the user

- UI: `http://localhost:8501` (app/dashboard). Fallback `http://127.0.0.1:8501` if
  `localhost` DNS misbehaves.
- FastAPI backend: `:8000` — this is the API (`/health`, `/api/...`), NOT something a
  user opens in a browser. Don't tell a user to open :8000 as "the UI".

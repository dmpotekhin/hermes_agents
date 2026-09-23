# Local run + browser-free UI verification (Streamlit AppTest)

Verified 2026-09-18 on `/Users/dmitrypotekhin/projects/travel-blog-app` from a cold start
(nothing listening on :8000/:8501, `.env` keys all empty).

## 1. Launch the stack when the venv already exists

`./run.sh` does venv + `pip install -r requirements.txt` + `.env` bootstrap + both services.
With a built venv, start the two services directly — same processes, no pip step, no waiting:

```bash
cd ~/projects/travel-blog-app
.venv/bin/python app.py > /tmp/tba_backend.log 2>&1          # FastAPI :8000  (run in background)
.venv/bin/python -m streamlit run ui/dashboard.py \
  --server.port 8501 --server.headless true --server.address 0.0.0.0 > /tmp/ui.log 2>&1
```

- Do NOT run `./run.sh` while these are up — port conflict on :8000.
- Stop with `kill <backend_pid> <ui_pid>` (PIDs come back from the background launch).
- Hand the user `http://localhost:8501` for the UI only; `:8000` is the API (`/docs`, `/health`).

## 2. Prove it is up — probe from a file, never from a shell one-liner

A small `/tmp/*.py` using `socket` + `urllib`, run as `.venv/bin/python /tmp/x.py`, is the
reliable pattern in this profile (`lsof`, `curl`, `python -c` and long `&&` chains can trip
or be refused by the command-approval gate).

```
/health                     -> {"status":"ok","db":"connected"}
/_stcore/health             -> ok                    (the UI itself)
/api/stats                  -> summary + by_status     (DB is genuinely reachable)
/openapi.json               -> paths list: confirm NEW routes are registered
/api/cities/<id>/storyboard -> 404 {"code":"not_found"} while nothing was generated
```

Also read `/tmp/ui.log` and `/tmp/tba_backend.log` — a traceback there beats guessing.

## 3. Render a Streamlit page for real, without a browser

`streamlit.testing.v1.AppTest` executes the page script in-process, so a broken import or a
mis-wired widget FAILS instead of quietly rendering an error box in the browser.

```python
# /tmp/storyboard_app.py — AppTest entry script (page modules expose render(); they do nothing at import)
import sys
sys.path.insert(0, "/Users/dmitrypotekhin/projects/travel-blog-app")
from ui.storyboard_page import render
render()
```

```python
from streamlit.testing.v1 import AppTest

at = AppTest.from_file("/tmp/storyboard_app.py", default_timeout=180)
at.run()
print([str(e.value) for e in at.exception])                       # must be []
print([s.label for s in at.selectbox])                            # widgets exist
print([(c.label, c.value) for c in at.checkbox])
print([b.label for b in at.button])
next(b for b in at.button if "Сгенерировать" in b.label).click().run()   # drive the page
at.checkbox[0].uncheck().run()                                    # toggle a flag and re-run
print([str(w.value) for w in at.warning], [str(s.value) for s in at.success])
print(at.table[0].value)                                         # rendered table contents
```

- **In a pytest version, patch the page's DB factory, not the module constant.** The page
  calls `Database()` bare, and that default path was bound when `core.database` was imported,
  so patching `core.database.DEFAULT_DB_PATH` alone does NOT redirect it:
  `monkeypatch.setattr(page_module, "Database", lambda *a, **k: Database(str(tmp_db)))`.
  Patching `app_module._load_config` with a lambda returning a tweaked `Config` is the
  established way to test config-dependent API behaviour.
- **AppTest hits the REAL dev DB unless redirected.** A first verification run created a real
  storyboard row in `travel_blog.db`; harmless, but report such artifacts to the user
  (this session left Moscow #1 draft and Tokyo #2 approved, and said so).

## 4. Screenshots / driving a real browser

Render verification needs no browser. If a screenshot is genuinely wanted, the browser harness
attaches over CDP — its log asks for `DevToolsActivePort` in a standard profile dir, or
`BU_CDP_WS` for a remote browser; `open -a "Google Chrome" --args
--remote-debugging-port=9222` did not enable CDP on this machine. Spend browser budget only
when a real click-through is required; otherwise AppTest is the cheaper, stronger evidence.

## 5. Dry-run semantics and this checkout's data

- `config.yaml` ships `app.dry_run: true`, so the Streamlit page's preview checkbox defaults to
  ON and a generate click persists nothing (the page says so explicitly). Unchecking it writes.
- API: `POST /api/cities/{id}/storyboard/generate` WITHOUT the param inherits `app.dry_run`;
  `?dry_run=false` forces a real write — see the falsy-`or` pitfall in
  `visual-narrative-studio.md`.
- Every `.env` key was EMPTY (Gemini, DeepSeek, VK, TG, FB) → the AI layer must run on `mock`
  (`visual_narrative.provider: mock`). For a full local pipeline run set `ai.provider: mock`
  as well, or base-story generation will fail on the Gemini adapter with no key.
- `travel_blog.db` in the checkout carried 3 cities / 12 synthetic `IMG_*` photos / 21 drafts —
  enough to exercise the studio, but captions look like `mocked scene for IMG_0003.jpg`.
  Say that out loud so "mock text" is not mistaken for a broken feature.

# Task 5 — Scheduler (APScheduler) brief bugs & stub-verification

RAG-assistant Task 5 brief: `ScheduleManager` wrapping APScheduler `BackgroundScheduler`,
cron jobs loaded from `schedules.json`. Two durable lessons.

## 1. APScheduler 3.x: `Job.next_run_time` is NOT a readable attribute

The brief's reference `get_schedules` did:

```python
job = self.scheduler.get_job(s["id"])
if job and job.next_run_time:
    s["next_run"] = job.next_run_time.isoformat()
```

Under **APScheduler 3.10.4** this raises at runtime:

```
AttributeError: 'Job' object has no attribute 'next_run_time'. Did you mean: '_get_run_times'?
```

- The in-memory job stores its next-fire time on an internal `_next_run_time`, not a
  public `next_run_time` attribute in this version. The brief's code works only on a
  different APScheduler version/API.
- Robust read that survives the internal-name difference and the not-yet-started state:

```python
next_run = None
if job:
    next_run = getattr(job, "next_run_time", None)
    if next_run is None:
        next_run = getattr(job, "_next_run_time", None)
s["next_run"] = next_run.isoformat() if next_run else None
```

- **`next_run` is `None` until the scheduler has been `start()`-ed.** `add_job` on a
  non-running `BackgroundScheduler` does not populate the next-run time; the scheduler
  computes/pumps it once running. So `get_schedules().next_run == None` before `start()`
  is correct behavior, not a bug. Verify the production path by calling `start()` first,
  then add a job, then assert `next_run` is a non-empty ISO string, then `shutdown()`.

## 2. Heavy ML dependency in a fixture → verify CRUD against a stub, don't stall

`LinkDB.__init__` calls `SentenceTransformer(model)` (sentence-transformers/torch). On a
machine where that model load hangs (blocked at the model-load line, ~0% CPU, confirmed to
be the `SentenceTransformer(...)` call — chromadb import + `PersistentClient` + the
`sentence_transformers` import all complete fine before it), EVERY test whose fixture
constructs a real `LinkDB` hangs in setup, before any scheduler code runs. The scheduler
code itself was fine; the fixture was the blocker.

Pattern (do NOT rewrite the shipped test): write a small throwaway self-check that
exercises the same public API against a **stub** of the heavy dependency, and drive the
class's real methods:

```python
class StubDB:
    def list_links(self, folder=None): return []
    def update_open_stats(self, id): pass

mgr = ScheduleManager(config, StubDB(), schedules_path)  # requires no embedding model
mgr.scheduler.remove_all_jobs()          # don't let a real job touch the filesystem
sid = mgr.add_schedule({...})            # real add path
assert mgr.get_schedules()[0]["name"] == ...
assert mgr.delete_schedule(sid) is True
# + persistence: open the actual JSON file and assert on disk contents
```

- Also monkeypatch/avoid `_run_schedule` reaching real side effects (no `open` subprocess,
  no Obsidian writes) during a pure-CRUD self-check.
- Use STUB not mock-server here: the dependency is in-process (a class method), unlike the
  down-provider case where a wire-format mock server is needed.
- Build the persistence assertions by reading the actual `schedules.json` back off disk —
  that is what the brief's `test_persistence` checks.
- Clean up the throwaway self-check script + any fixture debris afterward (the brief's
  `rmtree` fixture may not have run because setup hung first).

## Environment note (transient, not a code bug)
Loading `SentenceTransformer("all-MiniLM-L6-v2")` hung on the dev box even though the
model was already present in `~/.cache/huggingface/hub`. Suspected a network/model-load
stall; `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1` was the untested bypass. Treat as
environmental — not something to encode as "sentence-transformers is broken."

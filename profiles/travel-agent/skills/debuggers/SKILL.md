---
name: debuggers
description: "Debugger setup and usage for Python (pdb, debugpy, remote-pdb) and Node.js (node inspect, Chrome DevTools Protocol). Tool-focused companion to systematic-debugging methodology."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, python, nodejs, pdb, debugpy, node-inspect, CDP, breakpoints]
    related_skills: [systematic-debugging]
---

# Debuggers — Python & Node.js

Tool-specific debugger guides for Python and Node.js. Use these when you need to set breakpoints, inspect state, or step through code in a running process. For the *methodology* of systematic debugging (root cause analysis, hypothesis testing), load `systematic-debugging` instead.

---

## A. Python Debugging: pdb, debugpy, remote-pdb

Three tools, picked by situation:

| Tool | Best for |
|------|----------|
| **`breakpoint()` + pdb** | Local, interactive, simplest. Add `breakpoint()` in source, run normally, get a REPL at that line. |
| **`python -m pdb`** | Launch an existing script under pdb with no source edits. |
| **`debugpy`** | Remote / headless / attach to running process. Talks DAP, scriptable from terminal. |
| **`remote-pdb`** | Agent-friendliest remote debug — `nc` into a port, get a plain pdb prompt. |

**Start with `breakpoint()`.** It's the cheapest thing that works.

### pdb Quick Reference

Inside any pdb prompt (`(Pdb)`):

| Command | Action |
|---|---|
| `n` / `next` | Step over |
| `s` / `step` | Step into |
| `r` / `return` | Return from current function |
| `c` / `cont` | Continue |
| `unt N` | Continue until line N |
| `j N` | Jump to line N (same function only) |
| `l` / `ll` | List source / full function |
| `w` / `where` | Stack trace |
| `u` / `d` | Move up/down in stack |
| `a` / `args` | Print function arguments |
| `p expr` / `pp expr` | Print / pretty-print |
| `display expr` | Auto-print expr on every stop |
| `b file:line` | Set breakpoint |
| `b func` | Break on function entry |
| `cl N` | Clear breakpoint N |
| `!stmt` | Execute arbitrary Python |
| `interact` | Drop into full Python REPL |
| `q` / `quit` | Exit |

### Recipe: Local breakpoint

```python
def compute(x, y):
    result = some_helper(x)
    breakpoint()           # drops into pdb here
    return result + y
```

**Always remove `breakpoint()` before committing.** Use `rg -n 'breakpoint\(\)' --type py`.

### Recipe: Launch script under pdb

```bash
python -m pdb path/to/script.py arg1 arg2
(Pdb) b path/to/script.py:42
(Pdb) c
```

### Recipe: Debug a pytest test

```bash
# Drop to pdb on failure
scripts/run_tests.sh tests/path/to/test.py::test_name --pdb -p no:xdist

# Show locals without pdb
scripts/run_tests.sh tests/ --showlocals --tb=long

# Note: xdist and pdb don't mix — use -p no:xdist or -n 0
```

### Recipe: Post-mortem on exception

```python
import pdb, sys
try:
    run_the_thing()
except Exception:
    pdb.post_mortem(sys.exc_info()[2])
```

### Recipe: Remote debug with debugpy

```bash
pip install debugpy
```

**Source-edit pattern:**
```python
import debugpy
debugpy.listen(("127.0.0.1", 5678))
print("debugpy listening on 5678...", flush=True)
debugpy.wait_for_client()
debugpy.breakpoint()
```

**No-edit launch:**
```bash
python -m debugpy --listen 127.0.0.1:5678 --wait-for-client your_script.py
```

**Attach to running process by PID:**
```bash
python -m debugpy --listen 127.0.0.1:5678 --pid <pid>
```

### Recipe: remote-pdb (agent-friendliest)

```bash
pip install remote-pdb
```

```python
from remote_pdb import set_trace
set_trace(host="127.0.0.1", port=4444)
```

Then connect: `nc 127.0.0.1 4444` — you get a plain `(Pdb)` prompt.

### Python Debugging Pitfalls

1. **pdb under pytest-xdist silently does nothing.** Always use `-p no:xdist` or `-n 0`.
2. **`PYTHONBREAKPOINT=0`** disables all `breakpoint()` calls.
3. **`debugpy.listen` blocks only if `wait_for_client()` is also called.**
4. **Attach to PID fails on hardened kernels** (`ptrace_scope=1`). Workaround: `echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope` or launch under debugpy from the start.
5. **pdb only debugs the current thread.** For multithreaded code, use debugpy (thread-aware) or `threading.settrace()` per thread.
6. **asyncio:** `breakpoint()` works in coroutines; `await` inside pdb requires Python 3.13+ or use `interact` mode.
7. **`scripts/run_tests.sh` strips credentials and sets `HOME=<tmpdir>`.** Debug with raw `pytest` first.

---

## B. Node.js Debugging: `node inspect` + CDP

Two tools, pick one:

- **`node inspect`** — built-in, zero install, CLI REPL. Best for quick poking.
- **CDP via `chrome-remote-interface`** — scriptable from Node/Python; best for automation.

**Prefer `node inspect` first.**

### `node inspect` REPL

Launch paused on first line:
```bash
node inspect path/to/script.js
# or with tsx:
node --inspect-brk $(which tsx) path/to/script.ts
```

Inside the `debug>` prompt:

| Command | Action |
|---|---|
| `c` / `cont` | Continue |
| `n` / `next` | Step over |
| `s` / `step` | Step into |
| `o` / `out` | Step out |
| `sb('file.js', 42)` | Set breakpoint file:line |
| `sb(42)` | Break at current file line 42 |
| `sb('fnName')` | Break on function entry |
| `cb('file.js', 42)` | Clear breakpoint |
| `bt` | Backtrace (call stack) |
| `list(5)` | Show 5 source lines around current pos |
| `watch('expr')` | Evaluate expr on every pause |
| `repl` | Full JS REPL in current scope |
| `exec expr` | Evaluate expression once |
| `restart` | Restart script |
| `kill` | Kill the script |

### Attaching to running process

```bash
# Enable inspector on running process
kill -SIGUSR1 <pid>

# Find WS URL
curl -s http://127.0.0.1:9229/json/list

# Attach
node inspect -p <pid>
# or: node inspect ws://127.0.0.1:9229/<uuid>
```

Launch with inspector enabled:
```bash
node --inspect script.js          # keep running
node --inspect-brk script.js      # pause on first line
```

### Programmatic CDP (automation)

```bash
npm i -g chrome-remote-interface
```

Driver pattern:
```javascript
const CDP = require('chrome-remote-interface');
(async () => {
  const client = await CDP({ port: 9229 });
  const { Debugger, Runtime } = client;

  Debugger.paused(async ({ callFrames, reason }) => {
    const top = callFrames[0];
    console.log(`PAUSED: ${reason} @ ${top.url}:${top.location.lineNumber + 1}`);
    // Inspect locals, scopes, evaluate expressions
    await Debugger.resume();
  });

  await Debugger.enable();
  await Debugger.setBreakpointByUrl({ urlRegex: '.*app\\.tsx$', lineNumber: 119 });
  await Runtime.runIfWaitingForDebugger();
})();
```

### Debugging Hermes TUI (ui-tui)

```bash
# Start with inspector
node --inspect-brk dist/entry.js

# Attach to running --tui
kill -SIGUSR1 $(pgrep -f 'ui-tui/dist/entry')
node inspect -p <pid>
```

### Vitest under debugger

```bash
node --inspect-brk ./node_modules/vitest/vitest.mjs run --no-file-parallelism src/app/foo.test.tsx
```

### Heap snapshots & CPU profiles

```javascript
// CPU profile (5 seconds)
await client.Profiler.enable();
await client.Profiler.start();
await new Promise(r => setTimeout(r, 5000));
const { profile } = await client.Profiler.stop();
require('fs').writeFileSync('/tmp/cpu.cpuprofile', JSON.stringify(profile));

// Heap snapshot
const chunks = [];
client.HeapProfiler.addHeapSnapshotChunk(({ chunk }) => chunks.push(chunk));
await client.HeapProfiler.takeHeapSnapshot({ reportProgress: false });
require('fs').writeFileSync('/tmp/heap.heapsnapshot', chunks.join(''));
```

### Node.js Debugging Pitfalls

1. **Wrong TS source line numbers.** Breakpoints hit emitted JS, not `.ts`. Use `node --enable-source-maps` and break on `dist/*.js`.
2. **`--inspect-brk` vs `--inspect`.** Use `-brk` when you need to set breakpoints before any code runs.
3. **Port collisions.** Default is `9229`. Use `--inspect=0` for random port. Read actual URL from `/json/list`.
4. **Child processes.** `--inspect` on a parent does NOT inspect children. Use `NODE_OPTIONS='--inspect-brk'`.
5. **`Ctrl+C` from `node inspect` leaves the target paused.** `cont` first, then exit.
6. **Security.** `--inspect=0.0.0.0` exposes arbitrary code execution. Bind to `127.0.0.1`.

---

## C. Hermes-Specific Debugging Patterns

### Debugging a pytest test in Hermes

```bash
scripts/run_tests.sh tests/tools/test_foo.py::test_bar --pdb -p no:xdist
```

### Debugging `run_agent.py` / CLI

Add `breakpoint()` near the suspect line, run `hermes` normally. Control returns to your terminal at the pause point.

### Debugging Gateway / daemon

Use `remote-pdb` for the cleanest agent-friendly experience:
```python
from remote_pdb import set_trace
set_trace(host="127.0.0.1", port=4444)
```

Then `nc 127.0.0.1 4444` from another terminal.

### Debugging TUI gateway subprocess

Source-edit the gateway or use `remote-pdb` at the handler. The TUI will freeze (its backend is waiting). Connect and continue.

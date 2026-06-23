---
name: debugging-tools
description: "Interactive debugging for Python (pdb, debugpy, remote-pdb) and Node.js (node inspect, CDP). Breakpoints, stepping, scope inspection, heap snapshots, CPU profiles."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, python, nodejs, pdb, debugpy, node-inspect, cdp, breakpoints, post-mortem]
    category: software-development
---

# Debugging Tools — Python & Node.js

---

## Section 1: Python Debugging (pdb + debugpy + remote-pdb)

| Tool | When |
|---|---|
| `breakpoint()` + pdb | Local, interactive, simplest |
| `python -m pdb` | Launch under pdb with no source edits |
| `debugpy` | Remote / headless / DAP protocol |
| `remote-pdb` | Remote REPL over TCP (cleanest agent-friendly) |

### pdb Quick Reference
- `n` next, `s` step into, `c` continue, `r` return
- `l`/`ll` list source, `w` stack trace
- `p expr`/`pp expr` print, `b file:line` breakpoint
- `interact` full Python REPL, `!stmt` exec arbitrary code
- `q` quit

### Recipe: Local breakpoint
```python
breakpoint()  # drops into pdb
```
Run normally. Remove before committing.

### Recipe: pytest
```bash
pytest tests/test_file.py::test_name --pdb -p no:xdist
# -p no:xdist required: pdb breaks under xdist
```

### Recipe: Remote debug (debugpy)
```bash
python -m debugpy --listen 127.0.0.1:5678 --wait-for-client your_script.py
python -m debugpy --listen 127.0.0.1:5678 --pid <pid>
```

### Recipe: remote-pdb (cleanest for agents)
```bash
pip install remote-pdb
# In code:
from remote_pdb import set_trace
set_trace(host="127.0.0.1", port=4444)
# In another terminal:
nc 127.0.0.1 4444
```

---

## Section 2: Node.js Debugging (node inspect + CDP)

### node inspect REPL
```bash
node inspect path/to/script.js
node --inspect-brk $(which tsx) path/to/script.ts
```

Commands: `c` continue, `n` next, `s` step, `sb('file', N)` breakpoint, `bt` backtrace, `repl` scope REPL, `exec expr`

### Attach to Running Process
```bash
kill -SIGUSR1 <pid>
node inspect -p <pid>
node --inspect script.js   # start with inspector (no pause)
node --inspect-brk script.js  # start + pause on first line
```

### Programmatic CDP
```bash
npm i -g chrome-remote-interface
```
Use for automated breakpoints, scope dumps, heap snapshots, CPU profiles.

### One-Shot: "Why is variable undefined?"
```bash
node --inspect-brk script.js &
node inspect -p $!
# sb('script.js', X) → cont → repl → myVariable
```

### Pitfalls
1. `node inspect` CLI doesn't follow sourcemaps — break on JS output
2. Use `--inspect-brk` to pause before any code runs
3. Default port 9229; use `--inspect=0` for random port
4. Child processes: `NODE_OPTIONS='--inspect-brk' node parent.js`
5. `--inspect=0.0.0.0` exposes code execution — bind to 127.0.0.1

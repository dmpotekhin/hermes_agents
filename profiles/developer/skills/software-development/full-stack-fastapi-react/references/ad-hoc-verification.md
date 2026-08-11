# Ad-Hoc Verification for Testless Projects

Pattern that emerged across 13 SDD tasks building a full-stack app with no test suite.

## The Temp Script Pattern

```python
import tempfile, os, subprocess

code = r'''
import sys, json, urllib.request

BASE = "http://localhost:8000"
ok = fail = 0

def check(name, cond):
    global ok, fail
    if cond: ok += 1; print(f"PASS {name}")
    else: fail += 1; print(f"FAIL {name}")

# --- verification ---
resp = json.loads(urllib.request.urlopen(f"{BASE}/api/health").read())
check("health endpoint", resp.get("status") == "ok")
# ... more checks ...

print(f"\n{ok}/{ok+fail} PASSED")
sys.exit(0 if fail == 0 else 1)
'''

fd, path = tempfile.mkstemp(prefix="hermes-verify-", suffix=".py")
with os.fdopen(fd, 'w') as f: f.write(code)
result = subprocess.run(["python3", path], capture_output=True, text=True, timeout=30)
print(result.stdout)
os.unlink(path)
print(f"exit={result.returncode} | cleaned: {not os.path.exists(path)}")
```

## Conventions

| Rule | Reason |
|------|--------|
| `hermes-verify-*.py` prefix | Signals verification artifact to the system |
| `PASS/FAIL <name>` per line | Machine-parseable, human-readable |
| `N/M PASSED` final line | Quick green/red check |
| Exit 0 on all-pass | Shell-friendly for automation |
| `os.unlink()` after run | No temp file litter |
| `timeout=30` | Avoid hanging on network calls |

## Subagent Integration

In SDD, subagents should use this pattern for self-verification:
- Write the temp script, run it, report `N/M PASSED` in the report file
- Include the actual check names, not just the count
- Clean up before reporting DONE

Controller verification:
- Run a fresh temp script against the changed code (not reusing subagent's script)
- Focus on the task's touch points (endpoints, files, build)
- Regressions: verify public API didn't break

## Regression Checks

After each backend task, verify:
```python
# Public API still hides answers
pub = get("/api/lessons/some_lesson")
leak = any("correct_answer" in t for t in pub["tasks"])
check("no answer leak", not leak)
```

After each frontend task, verify:
```python
result = subprocess.run(["npm", "run", "build"], cwd="frontend", ...)
check("build succeeds", "built in" in result.stdout)
```

## Late Delegates in SDD

When `delegate_task` results arrive after you've moved past that task:

1. **Skim** — is the task already marked complete in the progress ledger?
2. **Acknowledge** — brief one-liner: "Task N — уже учтён."
3. **Never** re-dispatch, re-open, or change state based on late delegates
4. **Trust** the progress ledger over delegate summaries

Late delegates are informational noise, not actionable items. The ledger is authoritative.

# Worked Diagnosis: stuck `xcode-select` + stale `.update-incomplete`

Real session (2026-09-03, profile `developer`). Symptom the user reported: every request
"burns ~50k tokens on tool descriptions," and Hermes felt slow. Root cause turned out to be
recovery noise, not tool schemas.

## Trace of the actual inputs

### 1. `xcode-select` stuck on a deleted full Xcode.app

```
$ xcode-select -p
/Applications/Xcode.app/Contents/Developer        # path points here...

$ ls -ld /Applications/Xcode.app
ls: /Applications/Xcode.app: No such file or directory    # ...but it doesn't exist

$ ls -ld /Library/Developer/CommandLineTools
drwxr-xr-x  5 root wheel  160 29 дек  2021 /Library/Developer/CommandLineTools   # CLT IS installed

$ xcrun --find cc
xcrun: error: active developer path ("/Applications/Xcode.app/Contents/Developer") does not exist
```

Diagnosis: CLT present, but `xcode-select` path left pointing at a removed full Xcode.
The `"does not exist"` error from `xcrun` is the signature. `xcode-select --install` is the
WRONG fix here (it errors "command line tools are already installed") — the path was merely stuck.

### 2. Crypto build failing because of the stuck path

```
$ venv/bin/python3 -m pip install -e '.[all]'
...Building wheel for cryptography (pyproject.toml): started
...active developer path ("/Applications/Xcode.app/Contents/Developer") does not exist
...error: linking with `cc` failed
✗ Update failed: Command ['.../uv', 'pip', 'install', '-e', '.'] returned non-zero exit status 1
```

### 3. Stale recovery marker driving the noise

```
$ cat ~/.hermes/hermes-agent/.update-incomplete
{"attempts": 3}

$ hermes --version
⚠ Pending interrupted-update install has already failed 3 times in the early pass — leaving it for the post-import recovery path.
```

The marker's `attempts: 3` counter is what produced "failed 3 times" on every launch. Note the
same recovery also fires inside `hermes config check` and `hermes --version`.

## Applied fixes (in order)

1. **Toolchain** — switch the active path to the real CLT via the native macOS admin dialog
   (privileged; never pass the password in chat):
   ```bash
   osascript -e 'do shell script "xcode-select --switch /Library/Developer/CommandLineTools" with administrator privileges'
   # verify (checked after each step):
   #   xcode-select -p                     -> /Library/Developer/CommandLineTools
   #   xcrun --find cc                     -> /Library/Developer/CommandLineTools/usr/bin/cc
   #   echo 'int main(){return 0;}' | cc -x c - -o /tmp/_t  -> C compile OK
   ```
   `xcode-select --switch` REQUIRES root (`--switch must be run as root`) — hence osascript, not plain shell.

2. **Reinstall deps** (now the native build succeeds):
   ```bash
   cd ~/.hermes/hermes-agent
   venv/bin/python3 -m pip install -e '.[all]'
   ```
   Output confirmations:
   - `Successfully built cryptography hermes-agent`
   - `Successfully installed ... cryptography-50.0.0 hermes-agent-0.20.5 ...`
   - `hermes-agent 0.19.0` -> `0.20.5` (version bump is expected, not an error)

3. **Clear the marker** (backup first, then reset the counter):
   ```bash
   cp -v .update-incomplete .update-incomplete.bak
   printf '{"attempts": 0}' > .update-incomplete
   hermes --version
   ```
   After the successful reinstall the next clean launch removed the marker entirely:
   `cat .update-incomplete` -> `No such file or directory`.

## Final state check

```
$ hermes --version
Hermes Agent v0.20.5 (2026.8.19) · upstream 057dcdf2
Install directory: /Users/dmitrypotekhin/.hermes/hermes-agent
Python: 3.11.7
OpenAI SDK: 2.24.0
$ venv/bin/python3 -c "import cryptography; print(cryptography.__version__)"
50.0.0
```
No recovery lines. Clean.

## Lesson

The symptom ("slow Hermes / lots of tokens") was mis-attributed to tool descriptions. The real
costs were the recovery retries on every launch (blocking startup) plus the deep-ish cost model:
`cache_read` ~98% of tokens, not the tool schemas. Diagnose the launch path before touching
toolset config.

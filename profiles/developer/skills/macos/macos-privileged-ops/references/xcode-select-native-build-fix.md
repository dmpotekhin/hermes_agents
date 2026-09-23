# Fix: xcode-select stuck on a deleted full Xcode → native/rust builds fail

## Symptom (class of failure)
Every invocation of the tool prints a recovery banner and hangs/slow-starts:
```
⚠ Pending interrupted-update install has already failed 3 times in the early pass —
  leaving it for the post-import recovery path.
⚠ A previous `hermes update` was interrupted mid-install — finishing dependency installation now...
```
Any native extension build (cryptography/rust via maturin/cargo, openssl bindings, etc.)
fails with:
```
xcrun: error: active developer path ("/Applications/Xcode.app/Contents/Developer") does not exist
  Use `sudo xcode-select --switch path/to/Xcode.app` ... or `xcode-select --install`
```
This also breaks `pip install` / building wheels that compile C/Rust.

## Root cause
`xcode-select -p` points at a **full Xcode.app that has been deleted**. The path is still
recorded in the system developer choice, but the app directory is gone. Meanwhile the
**Command Line Tools are actually installed** at `/Library/Developer/CommandLineTools`.
So the toolchain is fine — only the pointer is wrong. Fixing the pointer (not installing
Xcode, not installing CLT) resolves it.

## Diagnose (verify the mismatch, don't guess)
```bash
xcode-select -p                              # what path is currently recorded
ls -ld /Applications/Xcode.app               # does full Xcode actually exist? (No = deleted)
ls -ld /Library/Developer/CommandLineTools   # does CLT actually exist? (Yes = toolchain present)
xcrun --find cc                              # fails if active path is bogus
echo 'int main(){return 0;}' > /tmp/_t.c && cc /tmp/_t.c -o /tmp/_t && echo "C compile OK"  # real probe
```

## Fix (one privileged command)
`xcode-select --switch` requires root. Do NOT take the sudo password in chat — use the
native admin prompt so the user types it (see SKILL.md):
```bash
sudo -n true 2>/dev/null || osascript -e 'do shell script \
  "xcode-select --switch /Library/Developer/CommandLineTools" \
  with administrator privileges'
osascript -e 'do shell script "xcode-select --switch /Library/Developer/CommandLineTools" \
  with administrator privileges'
verify: xcode-select -p   # now /Library/Developer/CommandLineTools
        xcrun --find cc   # resolves
```
CLT auth is cached ~5 min, so bundle any follow-up privileged steps into the SAME
`do shell script`.

## Then finish the interrupted install
After the pointer is fixed, re-run whatever the recovery was trying to do:
```bash
cd <install_dir>          # e.g. ~/.hermes/hermes-agent
venv/bin/python3 -m pip install -e '.[all]'
```
This now compiles natively instead of failing.

## Clear the retry counter (stop the early-pass banner)
The "already failed 3 times" come from a marker file holding an attempt count:
```
<install_dir>/.update-incomplete    → {"attempts": 3}
```
Back it up, reset to 0, then the next run proceeds to actually finish instead of giving up:
```bash
cp <install_dir>/.update-incomplete <install_dir>/.update-incomplete.bak
printf '{"attempts": 0}' > <install_dir>/.update-incomplete
<tool> --version    # banner gone; the tool finishes the install cleanly
```
On a genuinely successful finish the tool deletes `.update-incomplete` itself.

## Notes
- `--switch` without sudo → `error: --switch must be run as root`.
- A plain `xcode-select --install` is NOT the right move here and may error
  ("already installed") — the CLT is present; only the pointer is stale.
- After the fix the tool generally upgrades to its newer version (the prior
  interrupted update finally lands).

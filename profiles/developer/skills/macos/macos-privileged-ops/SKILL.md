---
name: macos-privileged-ops
description: Run macOS admin commands without a password in chat.
---

# macOS Privileged Operations

Techniques for running root-level operations on macOS when you cannot (and must not) ask the user for their sudo password in chat.

## Elevate via osascript GUI prompt (no password handling)
Use the native macOS admin prompt instead of sudo-in-terminal:
```bash
osascript -e 'do shell script "<cmd1> && <cmd2> && <cmd3>" with administrator privileges'
```
- Pops a system "…wants to make changes / enter password" dialog; the user types their password there — you never see or handle it.
- Bundle MULTIPLE root commands into ONE `do shell script` = a single password prompt (auth is cached ~5 min after the first).
- `sudo -n true` first to test whether sudo is already passwordless; if "a password is required", fall back to osascript admin.
- Exit `1` with `execution error: Отменено пользователем. (-128)` means the user clicked Cancel — simply re-run.

## launchd / PrivilegedHelperTools helper repair
Symptom: a LaunchDaemon plist points at `/Library/PrivilegedHelperTools/<name>` but the binary is missing, so the service silently never runs (a daemon gets stuck "pinging <helper>").
Diagnose:
```bash
ls -la /Library/PrivilegedHelperTools/          # is the binary present?
ls -la /Library/LaunchDaemons/                  # is the plist present?
launchctl print system/<label>                  # state: running?
find /Applications/<App>.app -name "<helper>"   # binary usually lives INSIDE the bundle
```
Fix (copy the helper out of the bundle, via the osascript admin prompt above):
```bash
osascript -e 'do shell script "cp /Applications/X.app/.../<helper> /Library/PrivilegedHelperTools/<helper> && chown root:wheel /Library/PrivilegedHelperTools/<helper> && chmod 711 /Library/PrivilegedHelperTools/<helper> && launchctl load -w /Library/LaunchDaemons/<label>.plist" with administrator privileges'
```
Match perms to an existing sibling helper (Docker Desktop uses `-rwx--x--x` = 711).

## Docker Desktop recovery on macOS
See `references/docker-desktop-recovery.md` for the full recipe (log paths, error signatures, factory reset). Quick version:
- "pinging vmnetd" in backend log → vmnetd helper binary missing (fix above; it lives at `/Applications/Docker.app/Contents/Library/LaunchServices/com.docker.vmnetd`).
- VM stuck in "still waiting for disk to be ready" loop → corrupted/empty data disk → factory reset: pkill backend + virtualization, delete `~/Library/Containers/com.docker.docker/Data/vms`, reopen Docker.
- Runtime alternatives: current OrbStack needs macOS 14+; Docker Desktop 26 supports macOS 12; Colima on Intel needs QEMU (via brew, which needs Xcode CLT).

## Pitfalls
- `osascript -e 'quit app "Docker"'` does NOT reliably stop a hung backend — verify with `pgrep -f com.docker.backend` and use `pkill` if it lingers.
- `launchctl load` returns success even when the service hasn't actually started yet; confirm with `launchctl print system/<label>` (look for `state = running`).

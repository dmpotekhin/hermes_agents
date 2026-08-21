# Docker Desktop macOS Repair

Two distinct failure modes hit a Docker Desktop install on an old Intel Mac (macOS 12.7.6), plus a general elevated-command technique. All were diagnosed from logs under `~/Library/Containers/com.docker.docker/Data/log/` (host backend: `host/com.docker.backend.log`; VM console: `vm/console.log`).

## 1. Daemon hangs on "pinging vmnetd" → missing vmnetd binary

**Symptom:** backend process starts, but `docker info` = "Cannot connect to the Docker daemon"; backend log ends at `pinging vmnetd`; `launchctl list | grep vmnetd` is empty.

**Root cause:** `/Library/PrivilegedHelperTools/com.docker.vmnetd` is missing — the launchd plist `/Library/LaunchDaemons/com.docker.vmnetd.plist` points at it, but it was never copied during install. The binary lives inside the app bundle at `/Applications/Docker.app/Contents/Library/LaunchServices/com.docker.vmnetd` (Mach-O x86_64, ~6 MB).

**Fix:**
```bash
sudo cp "/Applications/Docker.app/Contents/Library/LaunchServices/com.docker.vmnetd" /Library/PrivilegedHelperTools/com.docker.vmnetd
sudo chown root:wheel /Library/PrivilegedHelperTools/com.docker.vmnetd
sudo chmod 711 /Library/PrivilegedHelperTools/com.docker.vmnetd   # match com.docker.socket (rwx--x--x = 711)
sudo launchctl load -w /Library/LaunchDaemons/com.docker.vmnetd.plist
```
**Verify:** `launchctl print system/com.docker.vmnetd` → `state = running`.

## 2. VM stuck "still waiting for disk to be ready" → corrupted VM disk

**Symptom:** VM boots (kernel, network `eth0`, cgroup, QEMU binfmt all log fine), but `docker info` returns "Internal Server Error" forever, and `Data/log/vm/console.log` loops `still waiting for disk to be ready` / `still waiting for services to be ready` every 10s.

**Root cause:** corrupted/failed `Data/vms/0/data/Docker.raw` (a broken fresh disk is ~4 KB sparse, `du -sh` confirms — the 64 GB file is empty).

**Fix (factory reset):**
1. Quit Docker; force-kill the stuck backend if a graceful quit is ignored (`pkill -f com.docker.backend`).
2. **Rename** (not `rm -rf` — renaming avoids destructive-approval prompts and is reversible): `mv ~/Library/Containers/com.docker.docker/Data/vms ~/.../vms.bak`
3. `open -a Docker` — it recreates the disk and boots. First boot on Intel takes 1–3 min.

Check the disk is empty first so you know the reset is safe.

## 3. Running elevated commands without the user's password in chat

Use macOS's native authorization dialog — the user types their password into a GUI prompt, the agent never sees or stores it:
```bash
osascript -e 'do shell script "<cmd1> && <cmd2> && <cmd3>" with administrator privileges'
```
- One `do shell script` call = one password prompt (auth is cached ~5 min), so combine all elevated steps into a single call.
- Exit `-128` means the user cancelled the dialog (they hit Cancel / didn't recognize it) — retry after explaining it's a normal macOS "wants to make changes" prompt.
- Probe first with `sudo -n true` to learn whether passwordless sudo is even available (avoids pointless prompts).

Never ask the user to paste a password into chat; prefer this osascript path for any root-only step (writing to `/Library/PrivilegedHelperTools`, `launchctl load` into the system domain, etc.).

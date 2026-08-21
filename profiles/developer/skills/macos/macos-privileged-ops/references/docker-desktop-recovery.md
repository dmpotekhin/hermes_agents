# Docker Desktop recovery on macOS (worked example)

## Log locations
- Backend: `~/Library/Containers/com.docker.docker/Data/log/host/com.docker.backend.log`
- VM console: `~/Library/Containers/com.docker.docker/Data/log/vm/console.log`
- VM init: `~/Library/Containers/com.docker.docker/Data/log/vm/init.log`
- VM data disk: `~/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw`

## Symptom 1: backend stuck at "pinging vmnetd"
Backend log shows `pinging vmnetd` then nothing; daemon never comes up. Root cause:
`/Library/PrivilegedHelperTools/com.docker.vmnetd` is missing (only its plist is present in
`/Library/LaunchDaemons`). The binary lives inside the app bundle and just wasn't copied.
Fix (copy out + load, via osascript admin prompt):
```bash
osascript -e 'do shell script "cp /Applications/Docker.app/Contents/Library/LaunchServices/com.docker.vmnetd /Library/PrivilegedHelperTools/com.docker.vmnetd && chown root:wheel /Library/PrivilegedHelperTools/com.docker.vmnetd && chmod 711 /Library/PrivilegedHelperTools/com.docker.vmnetd && launchctl load -w /Library/LaunchDaemons/com.docker.vmnetd.plist" with administrator privileges'
```
Verify: `launchctl print system/com.docker.vmnetd` → `state = running`.

## Symptom 2: VM boots but stuck "still waiting for disk to be ready"
VM console.log repeats every 10s:
```
[init][W] still waiting for disk to be ready after 10s
[init][W] still waiting for services to be ready after 10s
```
`docker info` returns `Internal Server Error ... /info` (daemon socket answers, engine not
ready), while the backend log shows `Proxy error ... connect tcp 192.168.65.7:2375:
connection refused` (VM is up, dockerd inside it is not listening).
Root cause: corrupted/empty data disk. Confirm nothing to lose first — if
`du -sh ~/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw` reports ~4.0K
(sparse, empty), a reset is safe. Factory reset:
```bash
pkill -f com.docker.backend; pkill -f com.docker.virtualization
rm -rf ~/Library/Containers/com.docker.docker/Data/vms
open -a Docker
```
Docker recreates the disk and boots fresh. Intel Mac VM boot takes 30–90s; poll
`docker info` for `Server Version` (not just socket reachability).

## Notes
- `docker info` blocks for seconds when the daemon is unreachable — don't call it in a
  tight poll loop without a bounded wait.
- macOS has no GNU `timeout`; use `sleep N; check` patterns, or background + notify for
  long waits.
- The `rm -rf` of the vms dir is destructive (though empty-disk-safe) and will trigger a
  confirmation prompt — get explicit user consent first.

# Docker Desktop macOS — "pinging vmnetd" hang (missing helper binary)

Symptom: Docker Desktop backend (`com.docker.backend`) runs, but the daemon never comes up.
`docker info`/`docker ps` fail with "Cannot connect to the Docker daemon at
unix:///var/run/docker.sock". Backend log
(`~/Library/Containers/com.docker.docker/Data/log/host/com.docker.backend.log`) ends at:
`[com.docker.backend] pinging vmnetd` and goes no further.

## Root cause
The privileged helper binary is missing. The LaunchDaemon plist
`/Library/LaunchDaemons/com.docker.vmnetd.plist` points at:
`/Library/PrivilegedHelperTools/com.docker.vmnetd`
…but that file was never copied there at install time (only `com.docker.socket` and the plists
landed). The real binary ships inside the app bundle at:
`/Applications/Docker.app/Contents/Library/LaunchServices/com.docker.vmnetd`
(a Mach-O x86_64 executable, ~6 MB).

## Diagnostic commands (read-only, no sudo)
```bash
docker info 2>&1 | head -3                     # connection refused => daemon down
ps aux | grep -i vmnetd | grep -v grep         # empty => vmnetd not running
ls -la /Library/PrivilegedHelperTools/ | grep -i docker   # missing com.docker.vmnetd?
ls -la /Applications/Docker.app/Contents/Library/LaunchServices/com.docker.vmnetd  # source present?
```

## Fix (needs sudo — hand these to the user to run in THEIR terminal)
```bash
sudo cp "/Applications/Docker.app/Contents/Library/LaunchServices/com.docker.vmnetd" \
        /Library/PrivilegedHelperTools/com.docker.vmnetd
sudo chown root:wheel /Library/PrivilegedHelperTools/com.docker.vmnetd
sudo chmod 711 /Library/PrivilegedHelperTools/com.docker.vmnetd   # match com.docker.socket (rwx--x--x)
sudo launchctl load -w /Library/LaunchDaemons/com.docker.vmnetd.plist
```
Then fully Quit Docker Desktop (menu-bar whale → Quit) and reopen; wait for
"Docker Desktop is running".

If `launchctl load` reports "service already loaded", that's harmless — skip to Quit/reopen.
If vmnetd still won't start after the copy, try
`sudo launchctl kickstart -k system/com.docker.vmnetd`.

## Notes
- The agent's own terminal cannot supply the sudo password — this fix must be delegated to the
  user's interactive terminal. Provide the exact copy-paste block, don't attempt sudo from the
  agent shell.
- This Docker Desktop version (26.0.0) fully supports macOS 12 (Monterey); the "old Mac can't
  install Docker Desktop" objection is usually a red herring — the install is just incomplete.

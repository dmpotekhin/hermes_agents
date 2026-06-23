# Telegram Gateway Setup — japanese-tutor Profile

Initial setup performed 2026-06-16. Gateway running on macOS 12.7.6 (local terminal backend, no systemd).

## Initial Config

The profile's config.yaml was inherited from default profile and had no telegram platform configured. Steps taken:

1. **Add bot token to `.env`**
   - Appended `TELEGRAM_BOT_TOKEN=<token>` to `~/.hermes/profiles/japanese-tutor/.env`
   - Token format: `123456:ABC-def...` from BotFather

2. **Enable reactions**
   ```bash
   hermes config set telegram.reactions true --profile japanese-tutor
   ```

3. **Enable rich messages**
   ```bash
   hermes config set telegram.extra.rich_messages true --profile japanese-tutor
   ```

4. **Restrict access**
   ```bash
   hermes config set telegram.allowed_chats 222651048 --profile japanese-tutor
   ```
   This prevents unauthorized users from talking to the bot.

5. **Approve DM pairing**
   ```bash
   hermes pairing approve telegram <code> --profile japanese-tutor
   ```

## Profile Logs

All logs live under `~/.hermes/profiles/japanese-tutor/logs/`:

| File | Purpose |
|------|---------|
| `gateway.log` | Normal activity — look for `✓ telegram connected` to confirm running |
| `agent.log` | Per-session agent interaction logs (API calls, tool outputs) |
| `errors.log` | Warnings and errors — Telegram network failures, auxiliary model errors |
| `gateway-exit-diag.log` | JSON crash diagnostics — start/shutdown/exit timestamps with PIDs |

## Background-Start Pitfall

When launching via `terminal(background=true)`, the bash wrapper exits immediately, but the actual gateway Python process keeps running as a subprocess. `hermes gateway status` may say "not running" right after launch because it detects the dead wrapper.

**Workaround**: Wait 5 seconds, then check status again. Or verify directly:
```bash
ps aux | grep "hermes.*gateway" | grep -v grep
```

## Diagnostic Flow (gateway crashes silently)

1. Check if the Python process is alive: `ps aux | grep hermes.*gateway`
2. Read `gateway_state.json` (quick health check):
   ```bash
   cat ~/.hermes/profiles/japanese-tutor/gateway_state.json | python3 -c "import sys,json; d=json.load(sys.stdin); print('Gateway:', d['gateway_state']); print('Telegram:', d['platforms']['telegram']['state'])"
   ```
3. Read `gateway-exit-diag.log` — look for `exit_clean` vs `exit_nonzero`
4. Read `gateway.log` — see if connection to Telegram succeeded
5. Read `errors.log` — search for `connection failed` or `fallback IP failed`

### Pitfall: Gateway "Zombie State" (SIGTERM on macOS)

When gateway receives SIGTERM, it writes `gateway_state=running` to `gateway_state.json` **even though the process is dead**. This is designed for systemd auto-restart, but on macOS without systemd the stale JSON is misleading:

- `gateway_state.json` says `running` / `Telegram: connected` — **stale**
- The actual Python process is gone — `ps aux | grep hermes.*gateway` returns nothing
- No polling happens, no delivery works

**Always cross-check with `ps aux | grep hermes.*gateway | grep -v grep`** before trusting gateway_state.json.

## Successful Connection Signature

In `gateway.log`:
```
INFO  gateway.platforms.telegram: [Telegram] Connected to Telegram (polling mode)
INFO  gateway.run: ✓ telegram connected
INFO  gateway.run: Gateway running with 1 platform(s)
```

In `gateway_state.json`:
```
Gateway: running
Telegram: connected
```

If you see both, the bot is operational.

## Cron Delivery Verification

After running a cron job with `deliver=telegram:CHAT_ID`, verify delivery in `agent.log`:
```
INFO cron.scheduler: Job '<id>': delivered to telegram:CHAT_ID via live adapter
```
If instead you see:
```
WARNING cron.scheduler: Job '<id>': no delivery target resolved for deliver=telegram
```
The gateway's delivery channel registry hasn't caught up. See main SKILL.md "Delivery Target Fails After Restart" for recovery.

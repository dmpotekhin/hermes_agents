---
name: japanese-tutor
description: "Operate the japanese-tutor Hermes profile: Telegram gateway, access control, STT/voice support, and daily operations for a Russian-speaking Japanese tutor."
version: 1.1.0
author: Hermes Agent
metadata:
  hermes:
    tags: [japanese-tutor, telegram, gateway, stt, language-learning]
    profile: japanese-tutor
---

# Japanese Tutor Profile

This skill covers maintaining the `japanese-tutor` Hermes profile — a Telegram-based Japanese tutor bot for a Russian-speaking user. The profile uses DeepSeek as its primary model and runs a Telegram gateway with STT support for voice messages.

## Quick Reference

```bash
# Start gateway
hermes gateway run --profile japanese-tutor

# Check status
hermes gateway status --profile japanese-tutor

# Restart (after config/env changes)
hermes gateway restart --profile japanese-tutor

# Install as persistent service
hermes gateway install --profile japanese-tutor
```

## Profile Structure

```
~/.hermes/profiles/japanese-tutor/
├── config.yaml          # Main config (model, telegram, stt, etc.)
├── .env                 # API keys and secrets
├── sessions.db          # Session store (auto)
├── logs/                # Gateway and agent logs
│   ├── gateway.log      # Normal activity — look for "✓ telegram connected"
│   ├── agent.log        # Per-session interaction logs
│   ├── errors.log       # Warnings and errors
│   └── gateway-exit-diag.log  # JSON crash diagnostics
├── skills/              # Profile-specific skills
└── # ... other standard profile directories
```

## Telegram Bot Setup

### Prerequisites
1. Bot token from [@BotFather](https://t.me/BotFather)
2. Add `TELEGRAM_BOT_TOKEN=<token>` to `.env`

### Configuration

Key telegram settings in `config.yaml`:
```yaml
telegram:
  reactions: true                       # React to messages with emoji
  channel_prompts: {}
  allowed_chats: 222651048              # Restrict to specific Telegram IDs
  extra:
    rich_messages: true                 # Enable rich formatting
```

Set via CLI:
```bash
hermes config set telegram.reactions true --profile japanese-tutor
hermes config set telegram.extra.rich_messages true --profile japanese-tutor
hermes config set telegram.allowed_chats <user_id> --profile japanese-tutor
```

### Access Control

- Set `telegram.allowed_chats` to a single Telegram user ID (numeric)
- To add more users, comma-separate IDs or add later
- After changing, **restart the gateway** for changes to take effect

### Pairing (DM Authorization)

Pair a Telegram user after allowed_chats is configured:
```bash
hermes pairing approve telegram <pairing_code> --profile japanese-tutor
```

## Voice Messages (STT)

### Install faster-whisper (if not present)
```bash
python3 -m pip install faster-whisper
```

### Config (already enabled)
```yaml
stt:
  enabled: true
  provider: local          # faster-whisper is the local provider
  local:
    model: base            # Options: tiny, base, small, medium, large-v3
```

Model size tradeoffs:
- `base` (default): good balance for Russian + Japanese
- `small`/`medium`: better accuracy, slower
- `large-v3`: best accuracy, significant RAM/CPU usage

### Testing
Send a voice message in Telegram — the bot will transcribe and respond.

## Gateway Lifecycle

### Starting

```bash
# Foreground (blocking)
hermes gateway run --profile japanese-tutor

# Background (via terminal tool)
terminal(command="hermes gateway run --profile japanese-tutor", background=true)
```

### Background-Start Caveat

When launched via `terminal(background=true)`, two processes are created:
1. A bash wrapper (exits quickly after launching)
2. The actual hermes gateway Python process (the real one)

`hermes gateway status` may report "not running" immediately after background launch because it checks for the wrapper. Wait **5 seconds**, then check again. To verify the gateway is actually alive:

```bash
ps aux | grep "hermes.*gateway" | grep -v grep
```

If a Python process running `hermes gateway run` is alive, the gateway **is** running.

### Quick Diagnostic (when gateway won't stay running)

```bash
# 1. Check process directly
ps aux | grep "hermes.*gateway" | grep -v grep

# 2. Read exit diagnostics
tail -20 ~/.hermes/profiles/japanese-tutor/logs/gateway-exit-diag.log

# 3. Read last session logs for crash cause
tail -30 ~/.hermes/profiles/japanese-tutor/logs/gateway.log

# 4. Check for network/telegram errors
tail -30 ~/.hermes/profiles/japanese-tutor/logs/errors.log
```

Common causes of silent crash:
- **Network**: Telegram API unreachable (check `errors.log` for `connection failed` / `fallback IP failed`)
- **Token invalid**: Bot token from BotFather is wrong or revoked
- **Auth denied**: Ungated user tries to DM — connection OK but session denied

### Checking Status

```bash
hermes gateway status --profile japanese-tutor
```

If it says "✓ Gateway is running (PID: ...)", the bot is connected and polling Telegram.

### Restart (e.g. after config/.env changes)

```bash
hermes gateway restart --profile japanese-tutor
```

### Restart Caveats

- `hermes gateway restart` sends SIGTERM and may **time out** (124 exit code) — this is normal
- The command prints deprecation warnings about `TERMINAL_CWD` in `.env` — these are cosmetic, ignore them
- After a restart timeout:
  1. Wait ~10 seconds
  2. Check `hermes gateway status --profile japanese-tutor`
  3. If not running, start fresh: `hermes gateway run --profile japanese-tutor`

### Delivery Target Fails After Restart (known pitfall)

When gateway was down (e.g. Telegram API blocked / DNS failure) and then restarted, cron jobs may fail with:

```
WARNING cron.scheduler: Job '<id>': no delivery target resolved for deliver=telegram
```

**This happens even when** the gateway is alive, Telegram state shows `"state":"connected"`, and the bot responds to DMs. The cron scheduler's platform registry doesn't pick up the newly-connected Telegram platform immediately — its delivery channel registration lags behind gateway reconnection.

#### Root Cause: Gateway "Zombie State"

When gateway receives SIGTERM (e.g. `process(action='kill')` or macOS shutdown), it writes `gateway_state=running` to `gateway_state.json` **even though the process is dead**. This is by design (for systemd auto-restart), but on macOS without systemd it means:
- `gateway_state.json` says `running` — misleading
- Telegram says `connected` in the stale JSON — misleading
- The actual Python process is gone — `ps aux | grep hermes.*gateway` returns nothing
- No polling happens, no delivery works

**Always verify with `ps aux | grep hermes.*gateway | grep -v grep`** — do not trust `gateway_state.json` alone.

#### Reliable Recovery Pattern (tested 2026-06-17)

**Сначала попробуй простой фикс (1 шаг) — обычно этого достаточно:**

Обнови deliver у существующей cron-задачи на `telegram:CHAT_ID`:
```bash
hermes cronjob update <job_id> --deliver telegram:222651048
```
После этого следующий запланированный запуск отработает — не нужно перезапускать gateway.

**Если не помогло — полная процедура:**

1. **Verify gateway is actually dead**:
   ```bash
   ps aux | grep "hermes.*gateway" | grep -v grep
   ```

2. **Launch fresh gateway**:
   ```bash
   terminal(command="hermes gateway run --profile japanese-tutor", background=true)
   ```

3. **Wait 10-15 seconds, then verify Telegram state via JSON** (more reliable than log grepping):
   ```bash
   cat ~/.hermes/profiles/japanese-tutor/gateway_state.json | python3 -c "import sys,json; d=json.load(sys.stdin); print('Gateway:', d['gateway_state']); print('Telegram:', d['platforms']['telegram']['state'])"
   ```
   Look for: `Gateway: running` and `Telegram: connected`

4. **Use specific chat ID in deliver target** — when creating/updating cron jobs, prefer `deliver=telegram:CHAT_ID` over bare `deliver=telegram`. The explicit target binds to the live adapter when the channel is ready. This format is auto-applied when you update a cron job while the gateway is connected.

5. **Run the cron job immediately** (works once Telegram shows `connected`):
   ```bash
   cronjob(action='run', job_id='...')
   ```
   Verify in logs: `delivered to telegram:CHAT_ID via live adapter`

#### Fallback (when Telegram delivery won't resolve)

Run the script directly in CLI as a fallback:
```bash
python3 ~/Downloads/jp_rag_data/daily_lesson.py
```
Show the output to the user in the current conversation.

### Gateway Logs

Located at `~/.hermes/profiles/japanese-tutor/logs/`.

| File | Purpose |
|------|---------|
| `gateway.log` | Normal gateway activity — look for `✓ telegram connected` |
| `agent.log` | Per-session agent interaction logs |
| `errors.log` | Warnings and errors — Telegram network, auxiliary models, etc. |
| `gateway-exit-diag.log` | Crash diagnostics — JSON records of start/shutdown/exit events |

## Memory

The user's profile in memory contains:
- Target language: Japanese
- Interface language: Russian
- Current topic: hiragana
- Telegram ID for access control
- Gateway running status

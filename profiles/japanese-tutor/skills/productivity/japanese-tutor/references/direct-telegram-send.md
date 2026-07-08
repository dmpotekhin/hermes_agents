# Direct Telegram Bot API Messaging

Send one-off messages to Telegram without going through the gateway or cron delivery.
Useful when you need to push content immediately (e.g. lesson prompts, alerts) but don't
want to spawn a full agent session or wait for cron to tick.

## Prerequisites

- Bot token in `~/.hermes/profiles/japanese-tutor/.env` as `TELEGRAM_BOT_TOKEN`
- `requests` library (`pip install requests` if missing)
- Target chat ID (for this profile: `222651048`)

## One-liner Pattern

Extract token from `.env` and send in one terminal command:

```bash
cd ~/.hermes/profiles/japanese-tutor \
  && export $(grep -v '^#' .env | xargs) \
  && python3 -c "
import os, requests
token = os.environ['TELEGRAM_BOT_TOKEN']
chat_id = 222651048
msg = '''Your message here'''
r = requests.post(f'https://api.telegram.org/bot{token}/sendMessage',
    data={'chat_id': chat_id, 'text': msg, 'parse_mode': 'Markdown'})
print(r.status_code, r.json().get('ok'))
"
```

## Rich Markdown Messages

Telegram Bot API supports **Markdown** (`parse_mode='Markdown'`) and **HTML** (`parse_mode='HTML'`).

### Markdown formatting

| Style | Syntax |
|-------|--------|
| **Bold** | `**text**` |
| *Italic* | `*text*` |
| `Code` | `` `code` `` |
| ```Block``` | ` ``` ` `` ` `` ` ` ``` ` |
| Headers | `# H1`, `## H2` |
| Links | `[text](url)` |

### Multi-line messages

Use Python triple-quoted strings for multi-line messages. Each line break becomes
a Telegram line break. Separate sections with blank lines.

## Plain Text Fallback

When Markdown formatting causes `{"ok": false, "description": "can't parse entities"}`,
omit `parse_mode` — Telegram sends the text as-is:

```python
r = requests.post(f'https://api.telegram.org/bot{token}/sendMessage',
    data={'chat_id': chat_id, 'text': msg})
```

## When to Use vs. Cron Delivery

| Situation | Approach |
|-----------|----------|
| One-off push now | Direct API (this reference) |
| Scheduled recurring delivery | Cron job with `deliver=telegram:CHAT_ID` |
| Interactive agent conversation | Gateway (already polling) |
| Gateway unreachable, need to deliver | Direct API — bypasses gateway entirely |

## Safety

- Token is available via `cat .env` (defense-in-depth only) — the terminal tool
  has access regardless. Treat it as a secret.
- Always test with a small message first if you're unsure about Markdown parsing.
- The API endpoint is `https://api.telegram.org/bot<TOKEN>/sendMessage` — no auth
  beyond the token in the URL path.

---
name: telegram-bot-setup
description: Set up Telegram bot connected to Hermes gateway.
version: 1.0.0
---

# Telegram Bot Setup for Hermes

Full workflow: create bot in @BotFather, connect to Hermes Gateway, handle
pairing, VPN/proxy, and multi-profile routing.

## Quick Start

```bash
# 1. Create bot: @BotFather → /newbot → get token
# 2. Configure Hermes
hermes config set gateway.platforms.telegram.token "TOKEN"
hermes config set gateway.platforms.telegram.enabled true

# 3. Start gateway
hermes gateway

# 4. Send /start to bot in Telegram → get pairing code
# 5. Approve pairing
hermes pairing approve telegram CODE
```

## VPN / Proxy (Russia)

Telegram API (`api.telegram.org`) is blocked in Russia. The gateway must
reach it:

- **VPN on host machine** — simplest, just enable before starting gateway
- **Proxy** — `hermes config set gateway.platforms.telegram.proxy "socks5://127.0.0.1:1080"`
- Hermes auto-retries with DNS-over-HTTPS fallback (8 attempts)

Verify: `curl https://api.telegram.org/botTOKEN/getMe` should return JSON.

## Token Security

- **Never send token in chat** — it gets logged. Use @BotFather `/revoke`
  immediately if exposed
- Token lives in `config.yaml`, NOT `.env` (gateway reads config)
- After `/revoke`, update: `hermes config set gateway.platforms.telegram.token "NEW"`

## Pairing & Allowlists

First message from new user → pairing code. Approve:
```bash
hermes pairing approve telegram CODE
```

For open access (team bots):
```bash
hermes config set gateway.platforms.telegram.dm_policy open
export GATEWAY_ALLOW_ALL_USERS=true
```

## Profile Routing

Bot routes messages to the active profile. To switch:
```bash
hermes --profile marketing gateway    # marketing profile answers
hermes --profile german-tutor gateway # tutor profile answers
```

## SOUL.md for Telegram Assistant

Add a personal assistant section to the profile's SOUL.md for
auto-categorization of messages (notes, reminders, tasks, ideas, bookmarks,
YouTube links).

## Troubleshooting

| Problem | Check |
|---------|-------|
| Token rejected | Token was revoked — get new from @BotFather |
| Timeout connecting | VPN off? Try `curl api.telegram.org` |
| Bot doesn't respond | `/start` in bot chat first |
| Unknown sender | Pairing not approved — `hermes pairing approve` |
| SQLite WAL warnings | `hermes update` to upgrade SQLite |

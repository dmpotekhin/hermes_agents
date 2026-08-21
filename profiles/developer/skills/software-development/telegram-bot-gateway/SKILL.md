---
name: telegram-bot-gateway
description: Set up Telegram bot via Hermes. Pair, config, pitfalls.
version: 1.0.0
---

# Telegram Bot via Hermes Gateway

Connect a Telegram bot to Hermes as a personal assistant: notes, tasks, reminders, YouTube downloads — all saved to Obsidian.

## Setup

### 1. Create bot in @BotFather
- `/newbot` → name → username (must end in `bot`)
- Copy the API token

### 2. Configure Hermes
```bash
hermes config set gateway.platforms.telegram.token "TOKEN"
hermes config set gateway.platforms.telegram.enabled true
```

### 3. Start gateway
```bash
hermes gateway
```

### 4. Pair with user
- User sends `/start` to the bot in Telegram
- Bot responds with pairing code
- Owner approves: `hermes pairing approve telegram CODE`

## Russia/VPN workaround

Telegram API is blocked in Russia. A VPN on the host machine is required.
Verify: `curl https://api.telegram.org/botTOKEN/getMe`

## SOUL.md pattern for personal assistant

The developer profile SOUL.md must include a workflow section:

```
1. ОПРЕДЕЛИ категорию (заметка/задача/идея/напоминание/контакт/закладка/видео)
2. ЗАПИШИ в Obsidian через write_file (ОБЯЗАТЕЛЬНО, до ответа)
3. ОТВЕТЬ кратко (1-3 строки, эмодзи категории)
```

**Critical: step 2 BEFORE step 3.** "Write after responding" causes the LLM to skip writes.

### Category routing

| Keywords | Category | File |
|----------|----------|------|
| «напомни», remind | ⏰ Reminder | `reminders.md` + cronjob |
| «задача», «task» | ☐ Task | `tasks.md` |
| «идея», «idea» | 💡 Idea | `ideas.md` |
| «контакт», phone | 👤 Contact | `contacts.md` |
| youtube.com / youtu.be | 🎬 Video | `videos.md` + yt-dlp |
| Any URL | 🔗 Bookmark | `bookmarks.md` |
| Everything else | 📝 Note | `notes.md` |

### Obsidian path
`~/Odsidian/obsidians/Obsidian Vault/Brain/notes/bot/<file>.md`

Format: `| HH:MM | Message text |` — append, create if missing.

## YouTube
```bash
yt-dlp -f best -o ~/Downloads/bot/%(title)s.%(ext)s URL
```
≤50 MB → send in chat; >50 MB → tell disk path.

## Pitfalls

- **LLM skips writes**: workflow must be "write BEFORE respond", not after
- **Token 404**: revoked — get new from @BotFather
- **No brain MCP in gateway**: use `write_file`/`read_file` to Obsidian path directly
- **Gateway foreground**: use `background=true` or daemon
- **Missed cron windows**: one-shot jobs don't retrigger after gateway restart

---
name: telegram-bot-assistant
description: Build Telegram personal assistant bot via Hermes gateway.
version: 1.0.0
---

# Telegram Bot Personal Assistant

Build a Telegram bot that acts as a personal assistant through Hermes gateway.
Handles notes, tasks, ideas, reminders, YouTube downloads, and voice messages.

## Architecture

```
Telegram ←→ Bot ←→ Hermes Gateway ←→ Profile (developer)
                      ↑
                      ├ cronjob (reminders)
                      ├ Obsidian (write_file)
                      ├ yt-dlp (YouTube)
                      └ STT/TTS (voice)
```

## Setup

### 1. Create bot via @BotFather
```
/newbot → name → username (ends in 'bot') → copy token
```

### 2. Configure Hermes
```bash
hermes config set gateway.platforms.telegram.token "<token>"
hermes config set gateway.platforms.telegram.enabled true
```

### 3. Start gateway
```bash
hermes gateway
```

### 4. Pair user
On first message, bot sends pairing code. Approve:
```bash
hermes pairing approve telegram <CODE>
```

## SOUL.md Assistant Persona

Add to the profile's SOUL.md for auto-categorization:

```markdown
## Режим персонального ассистента (Telegram)

| Ключевые слова | Категория | Куда сохранить |
|---------------|----------|---------------|
| «напомни», время/дата | ⏰ Напоминание | cronjob + reminders.md |
| «задача», «сделать» | ☐ Задача | tasks.md |
| «идея», «можно сделать» | 💡 Идея | ideas.md |
| «контакт», телефон + имя | 👤 Контакт | contacts.md |
| YouTube-ссылка | 🎬 Видео | yt-dlp → ~/Downloads/bot/ |
| Любая URL-ссылка | 🔗 Закладка | bookmarks.md |
| Голосовое | 🎤→📝 | STT → категория |
| Всё остальное | 📝 Заметка | notes.md |
```

## Storage (Obsidian via write_file)

Bot uses `write_file` directly (MCP brain tools may not be available in gateway sessions):

```
~/Odsidian/obsidians/Obsidian Vault/Brain/notes/bot/
  notes.md, tasks.md, ideas.md, contacts.md, bookmarks.md,
  videos.md, reminders.md
```

**Always APPEND** (read_file → add line → write_file), never overwrite.

## YouTube Download

```bash
yt-dlp -f best -o ~/Downloads/bot/%(title)s.%(ext)s <URL>
```

- If ≤50 MB: send file directly in Telegram chat
- If >50 MB: "Saved to ~/Downloads/bot/filename.mp4"
- Save link + metadata to `videos.md`

## Voice Messages

Gateway auto-transcribes voice messages via STT. Bot processes transcribed text
as normal message (categorization applies).

## Reminders via cronjob

Parse date/time from message → create one-shot cronjob:
```python
cronjob(action='create', schedule='<ISO timestamp>',
        prompt='Send reminder: <text>', deliver='telegram')
```

## Russia-specific

- Telegram API blocked — requires VPN on host machine
- Gateway uses DNS-over-HTTPS fallback for Telegram IPs
- Token must be kept secret — never share in chat, store in .env

## Pitfalls

- MCP brain tools unavailable in gateway sessions — use write_file directly
- Token exposed in chat → revoke immediately via @BotFather `/revoke`
- Gateway needs restart after SOUL.md changes
- Obsidian path: use FULL path, not shortened (`~` not `$HOME`)

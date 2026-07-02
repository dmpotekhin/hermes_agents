---
name: apple
description: "macOS Apple ecosystem tools: Notes, Reminders, FindMy, iMessage. CLIs for Apple-native apps via memo, remindctl, AppleScript, and imsg."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [Apple, macOS, Notes, Reminders, FindMy, iMessage, CLI]
    related_skills: [macos-computer-use]
---

# Apple Ecosystem Tools (macOS)

Manage Apple-native apps from the terminal using macOS-specific CLI tools. All tools sync via iCloud.

**Structure:** This umbrella covers four Apple app CLI tools as labeled sections below.

---

## A. Apple Notes (`memo`)

Manage Apple Notes via the `memo` CLI. Notes sync across all Apple devices via iCloud.

### Prerequisites
```bash
brew tap antoniorodr/memo && brew install antoniorodr/memo/memo
```
Grant Automation access to Notes.app when prompted (System Settings → Privacy → Automation).

### Quick Reference

```bash
# View notes
memo notes                        # List all notes
memo notes -f "Folder Name"       # Filter by folder
memo notes -s "query"             # Search notes (fuzzy)

# Create notes
memo notes -a                     # Interactive editor
memo notes -a "Note Title"        # Quick add with title

# Edit / delete / move
memo notes -e                     # Interactive selection to edit
memo notes -d                     # Interactive selection to delete
memo notes -m                     # Move note to folder (interactive)

# Export
memo notes -ex                    # Export to HTML/Markdown
```

### Limitations
- Cannot edit notes containing images or attachments
- Interactive prompts require terminal access (use pty=true if needed)
- macOS only — requires Apple Notes.app

---

## B. Apple Reminders (`remindctl`)

Manage Apple Reminders via the `remindctl` CLI. Tasks sync across all Apple devices via iCloud.

### Prerequisites
```bash
brew install steipete/tap/remindctl
```
Grant Reminders permission when prompted. Check: `remindctl status` / Request: `remindctl authorize`.

### Quick Reference

```bash
# View reminders
remindctl                    # Today's reminders
remindctl today              # Today
remindctl tomorrow           # Tomorrow
remindctl week               # This week
remindctl overdue            # Past due
remindctl all                # Everything
remindctl 2026-01-04         # Specific date

# Manage lists
remindctl list               # List all lists
remindctl list Work          # Show specific list
remindctl list Projects --create    # Create list
remindctl list Work --delete        # Delete list

# Create reminders
remindctl add "Buy milk"
remindctl add --title "Call mom" --list Personal --due tomorrow
remindctl add --title "Meeting prep" --due "2026-02-15 09:00"

# Due Time vs Alarm / Early Nudge
# --due sets the reminder's due date/time.
# --alarm sets the EventKit alarm/notification trigger.
remindctl add --title "Hairdresser" --due "2026-05-15 14:00" --alarm "2026-05-15 13:30"

# Complete / Delete
remindctl complete 1 2 3          # Complete by ID
remindctl delete 4A83 --force     # Delete by ID

# Output formats
remindctl today --json       # JSON for scripting
remindctl today --plain      # TSV format
remindctl today --quiet      # Counts only
```

### Date Formats
Accepted by `--due` and date filters: `today`, `tomorrow`, `yesterday`, `YYYY-MM-DD`, `YYYY-MM-DD HH:mm`, ISO 8601.

---

## C. Find My (Apple) — AirTags & Devices

Track Apple devices and AirTags via FindMy.app on macOS. No native CLI — uses AppleScript + screenshot/vision.

### Prerequisites
- **macOS** with Find My app and iCloud signed in
- Screen Recording permission for terminal (System Settings → Privacy → Screen Recording)
- Optional: `brew install steipete/tap/peekaboo` for better UI automation

### Method 1: AppleScript + Screenshot

```bash
# Open Find My app
osascript -e 'tell application "FindMy" to activate'
sleep 3

# Take a screenshot
screencapture -w -o /tmp/findmy.png

# Switch between tabs
osascript -e '
tell application "System Events"
    tell process "FindMy"
        click button "Devices" of toolbar 1 of window 1
    end tell
end tell'
```

Then use `vision_analyze` to read the screenshot.

### Method 2: Peekaboo UI Automation (Recommended)

```bash
# Open Find My
osascript -e 'tell application "FindMy" to activate'
sleep 3

# Capture and annotate
peekaboo see --app "FindMy" --annotate --path /tmp/findmy-ui.png

# Click on a specific device/item by element ID
peekaboo click --on B3 --app "FindMy"

# Capture the detail view
peekaboo image --app "FindMy" --path /tmp/findmy-detail.png
```

### Limitations
- FindMy has **no CLI or API** — must use UI automation
- AirTags only update location while the FindMy page is actively displayed
- Keep FindMy app in the foreground when tracking AirTags (updates stop when minimized)
- Use `vision_analyze` to read screenshot content

---

## D. iMessage / SMS (`imsg`)

Send and receive iMessage/SMS via macOS Messages.app using the `imsg` CLI.

### Prerequisites
```bash
brew install steipete/tap/imsg
```
Grant Full Disk Access for terminal (System Settings → Privacy → Full Disk Access).
Grant Automation permission for Messages.app when prompted.

### Quick Reference

```bash
# List chats
imsg chats --limit 10 --json

# View history
imsg history --chat-id 1 --limit 20 --json
imsg history --chat-id 1 --limit 20 --attachments --json

# Send messages
imsg send --to "+14155551212" --text "Hello!"
imsg send --to "+14155551212" --text "Check this" --file /path/to/image.jpg

# Force iMessage or SMS
imsg send --to "+14155551212" --text "Hi" --service imessage
imsg send --to "+14155551212" --text "Hi" --service sms

# Watch for new messages
imsg watch --chat-id 1 --attachments
```

### Service Options
- `--service imessage` — Force iMessage (requires recipient has iMessage)
- `--service sms` — Force SMS (green bubble)
- `--service auto` — Let Messages.app decide (default)

### Rules
1. **Always confirm recipient and message content** before sending
2. **Never send to unknown numbers** without explicit user approval
3. **Verify file paths** exist before attaching
4. **Don't spam** — rate-limit yourself

---

## Cross-Section Rules

1. **When to use Apple Notes:** user needs cross-device sync (iPhone/iPad/Mac), saving information to Notes.app
2. **When to use Reminders:** user says "remind me" but means Apple Reminders (syncs to phone), not agent cronjob
3. **When to use FindMy:** user asks "where is my [device/cat/keys/bag]?"
4. **When to use iMessage:** user asks to send an iMessage or SMS
5. Prefer the `memory` tool for agent-internal notes that don't need to sync
6. For agent scheduling, use the `cronjob` tool instead of Reminders
7. For non-Apple messaging (Telegram/Discord/Slack), use the appropriate gateway channel

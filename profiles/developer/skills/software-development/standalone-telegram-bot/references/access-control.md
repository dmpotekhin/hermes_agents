# Access control for a private aiogram bot

## Env contract

```env
ACCESS_MODE=allowlist          # allowlist | group | both | off
OWNER_TG_ID=                   # numeric id; empty = access commands disabled
ALLOWED_USER_IDS=              # static list, comma-separated: 123456789,987654321
ALLOWLIST_PATH=allowlist.json
ALLOWED_GROUP_CHAT_ID=         # -100... for supergroups/channels
ALLOWED_GROUP_INVITE_LINK=     # optional, shown on denial in group/both modes
```

Document in `.env.example` and `README.md` that the id is numeric and that the
bot must be a member of the group (admin for channels).

## Modes

| mode | who gets in |
|------|-------------|
| `allowlist` | id in the whitelist (default) |
| `group` | members of `ALLOWED_GROUP_CHAT_ID` |
| `both` | whitelist OR group |
| `off` | everyone — only when explicitly configured |

Unknown value → `allowlist`, and log the normalization at warning level.

## Middleware decision order

1. not a `Message` → pass (don't touch other update types)
2. command name in `PUBLIC_COMMANDS` → pass
3. mode `off` → pass
4. `from_user is None` (channel post / anonymous) → deny with a dedicated message
5. `await is_user_allowed(from_user.id)` → pass
6. deny: reply with the numeric id, plus the invite link when the mode is
   `group`/`both` and `ALLOWED_GROUP_INVITE_LINK` is set; log `user_id` + action
   + mode at warning level.

`is_user_allowed`: owner → True; `allowlist` → id in effective list; `group` →
`is_group_member`; `both` → union of both.

## Storage

```json
{
  "users": []
}
```

Effective list = env ids ∪ file ids (env wins for reporting purposes, see
`/deny`). Atomic write, same directory so `os.replace` stays on one filesystem:

```python
def save_allowlist(ids: set[int]) -> None:
    path = allowlist_file_path()
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".allowlist-", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump({"users": sorted(ids)}, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
```

`load_allowlist_from_file()` returns `set()` for: missing file, invalid JSON, a
JSON non-object, `users` missing or not a list, non-integer entries (accept
string digits). Each case logs a warning, none raises. `ensure_allowlist_file()`
runs at startup so the user sees the file and can edit it by hand.

## Commands

Public: `/whoami` (numeric id, username, full name + note that the id is the
stable identity), `/access` (mode + own verdict; on deny the message must carry
the numeric id so the owner knows whom to allow).

Owner only: `/allow <id>`, `/deny <id>`, `/list`, `/reload_access`. With
`OWNER_TG_ID` empty every one of them answers a dedicated "owner not
configured" message (never a silent ignore, never a crash). Invalid id argument
→ usage message with an example, not a stack trace.

## Semantics worth keeping

- The owner bypasses every mode — otherwise a mid-edit allowlist locks the owner
  out of `/allow`.
- `/deny` on an env-provided id replies that `.env` is the only place to remove
  it; it must not claim a successful removal.
- Group membership cache ~60 s and error → deny (log at warning).
- `/reload_access` re-reads the `.env` file (`load_dotenv(override=True)`).
  Values apply immediately; the token and the running `Bot` instance do not, so
  the reply/README must say what needs a restart. Note this also means the
  project `.env` overrides process env from then on.
- Startup log: `Доступ: режим=<mode> | владелец=<id> | разрешённых ID=<n> |
  группа=<id|не задана>` + a warning when mode is `allowlist` and the list is
  empty (the bot will answer nobody).
- `allowlist.json` belongs in `.gitignore`.

## Test hooks

Module-global settings with `get/set_access_settings()`, plus `set_bot_instance()`
for `get_chat_member` when there is no update context (e.g. startup checks), and
`access: AccessSettings` on `Config` so handlers reach it through
`dispatcher.workflow_data`.

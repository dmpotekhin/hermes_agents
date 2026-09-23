# Testing an aiogram 3 bot offline (real Dispatcher, fake session)

A bot cannot send itself updates, but the whole gate — middleware, handlers,
replies — can be exercised for real: build the actual `Dispatcher`, include the
real router, register the fake session on a `Bot`, and feed updates through
`feed_update`. Nothing is mocked above the HTTP transport, so the test proves
the wiring and not a copy of it.

## Harness

```python
import os, sys
sys.path.insert(0, str(PROJECT))
os.environ["TELEGRAM_BOT_TOKEN"] = "123456:TESTTOKEN"   # before importing bot
os.environ["ALLOWLIST_PATH"] = str(TMP / "allowlist.json")
import bot

class FakeSession(BaseSession):
    def __init__(self):
        super().__init__()
        self.sent: list[tuple[str, object]] = []
        self.member_status = "member"

    async def close(self) -> None: ...
    async def stream_content(self, *a, **k): raise NotImplementedError

    async def make_request(self, bot, method, timeout=None):
        name = type(method).__name__
        self.sent.append((name, method))
        if name == "GetMe":
            return User(id=123456, is_bot=True, first_name="TestBot", username="test_bot")
        if name == "GetChatMember":
            return _member_of(self.member_status, method.user_id)
        if name in ("SendMessage", "EditMessageText"):
            return Message(message_id=len(self.sent), date=datetime.now(),
                           chat=Chat(id=method.chat_id, type="private"),
                           text=getattr(method, "text", None))
        if name == "SendChatAction":
            return True
        raise AssertionError(f"unexpected method: {name}")
```

```python
session_bot = Bot(token="123456:TESTTOKEN", session=FakeSession())
dp = Dispatcher()
dp.include_router(bot.build_router())
dp.workflow_data.update(config=cfg)

async def send(dp, bot_, user_id, text=None, video=False):
    msg = Message(message_id=1, date=datetime.now(),
                  chat=Chat(id=user_id, type="private"),
                  from_user=User(id=user_id, is_bot=False, first_name="U"),
                  text=text, video=Video(...) if video else None)
    await dp.feed_update(bot_, Update(update_id=1, message=msg))
```

Assertions read the captured methods, not the code:
`[m.text for n, m in bot_.session.sent if n == "SendMessage"]`.

## Pitfalls that cost real time

- **`GetMe` is mandatory.** aiogram resolves `@botname` mentions in outgoing
  text through `bot.me()`; with a fake session the reply raises instead of being
  sent. Answer `GetMe` with a `User(is_bot=True, username=...)`.
- **A hand-built `Message` cannot `answer()`** unless it is mounted to a bot:
  `Message(...).as_(session_bot)`. Otherwise the middleware's `event.answer(...)`
  blows up outside a dispatcher call.
- **Fake `GetChatMember` must return the matching subclass** (`ChatMemberMember`
  / `ChatMemberOwner` / `ChatMemberAdministrator` / `ChatMemberLeft` /
  `ChatMemberBanned`). `ChatMemberAdministrator` also needs
  `can_post_stories`, `can_edit_stories`, `can_delete_stories`,
  `can_send_welcome_messages`; a missing field is a pydantic
  `ValidationError`.
- **An exception-swallowing code path turns a broken stub into a green test.**
  If the group check does `except Exception: return False`, a `ValidationError`
  from the fake looks exactly like "not a member". Always assert the positive
  direction too (`member`/`administrator`/`creator` → allowed), so a stub that
  cannot build a member type fails loudly.
- `ChatMemberStatus` is not exported from `aiogram.types`; compare status by
  `getattr(status, "value", status)` instead of importing the enum.
- **Env isolation breaks at `/reload_access`.** That handler calling
  `load_dotenv(override=True)` re-reads the project `.env`, which then overrides
  the test's `ALLOWLIST_PATH` / `ALLOWED_USER_IDS`. Re-apply the test env right
  after asserting the reload behavior, and assert the override itself as
  intended behavior rather than being surprised by it.
- Settings are read once into a module global: after changing `os.environ` in a
  test, call the module's `set_access_settings(read_access_settings())` (and
  clear any membership cache) — otherwise every scenario silently reuses the
  first one's config.
- **A per-case reset must clear the config env vars too, not just the file
  paths.** A scenario that sets a limit to prove exhaustion (`DAILY_*_LIMIT=1`)
  leaks into every later case: those cases then fail with "quota exceeded" and
  look like router bugs. Reset the whole set the module reads — paths, limits,
  flags, modes — in the reset helper, then rebuild every singleton
  (`set_settings(None)`, `reset_tracker()`, `reset_cache()`, `set_store(None)`)
  against a fresh temp dir so each case starts from defaults.
- A reset helper whose `None` branch constructs the object with its parameter
  default silently ignores the configured path — state files land in the project
  cwd and the temp dir stays empty. Assert the temp file exists after the first
  write; that check is what catches it.
- Own the test's files: point `ALLOWLIST_PATH` at a temp dir, and restore/clear
  the project's real `allowlist.json` at the end if a reload or startup path
  touched it — tests must not leave a real user id whitelisted in the repo.

## Run and verify

- `python -m py_compile bot.py` first (catches seam damage from block inserts),
  then the suite: a per-check `PASS/FAIL` counter printed at the end, total
  asserted against zero failures.
- Re-run the existing feature suite unchanged after adding the gate: it proves
  the new middleware did not start blocking the previously working flows.
- Treat every FAIL as a test defect until proven otherwise: in this class of
  suite the usual causes are a wrong expected message (a non-owner allowed into
  the router gets the "owner only" reply, not the access denial) and the fake
  session returning an invalid type.

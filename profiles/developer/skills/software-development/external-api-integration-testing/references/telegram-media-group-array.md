--- Working case: Telegram Bot API sendMediaGroup returns an ARRAY, not an object.
Project: travel-blog-app, modules/publishers/telegram.py (ADR-104 album publishing).

## The bug

Code did:
```python
msg = r.json().get("result", {})
external_id = str(msg.get("message_id", ""))
```
Real Telegram:
- sendMessage / sendPhoto  -> {"result": {"message_id": N}}  (object)
- sendMediaGroup           -> {"result": [Message, Message, ...]}  (ARRAY)

So for an album (2-10 photos) the code hit `AttributeError: 'list' object has no attribute 'get'`
AFTER Telegram already accepted the post. Prod posted the album, then the app crashed.

The unit test was green because the fake returned only the object shape:
```python
class _FakeResp:  # OLD — too generous, only ever returns the object form
    def json(self):
        return {"result": {"message_id": 7}}
```

## The fix
1. Normalize both shapes in the publisher:
```python
res = r.json().get("result", {})
if isinstance(res, list):          # sendMediaGroup -> array of Messages
    first = res[0] if res else {}
else:
    first = res if isinstance(res, dict) else {}
external_id = str(first.get("message_id", ""))
```
2. Make the fake configurable and give it a REALISTIC value for the batch case:
```python
class _FakeResp:
    def __init__(self, result=None):
        self._result = result if result is not None else {"message_id": 7}
    def json(self):
        return {"result": self._result}

class _FakeClient:
    def __init__(self, result=None):
        self._result = result
        self.posts = []
    async def post(self, url, **kw):
        self.posts.append((url, kw))
        return _FakeResp(self._result)
```
3. Assert on the consumed field, with the realistic array response:
```python
cli = _FakeClient(result=[{"message_id": 7}, {"message_id": 8}])
...
assert res.external_id == "7"   # taken from result[0] of the album array
```

## Regression-test gap (the second bug the reviewer caught)
A text-only guard for "no false degraded signal" must use content in the FAILING band,
not a trivially-short happy path. The old test used content="hello world" which was NEVER
the problem. Use the band the bug lives in (e.g. 1500 chars, inside 1025..4096) so the
test genuinely reproduces the old FALSE degraded signal:
```python
draft = _draft(content="x"*1500)   # would-be false-degraded band
assert res.degraded is False
assert cli.posts[0][1]["json"]["text"] == "x"*1500
```

## Lesson
A reviewer working from manual trace (no test run) can catch a prod crash the green suite
missed. When they do, trust it: the root cause is almost always that the double models the
provider response too simply. Fix code + double + test together, then re-run the full suite.
---
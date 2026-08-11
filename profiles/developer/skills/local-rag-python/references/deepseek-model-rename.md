# DeepSeek Model Rename + Silent Error Pattern

## The Problem

DeepSeek renamed their model names. Old name `deepseek-flash` was rejected with
400 Bad Request. The error was silently swallowed by the LLM parser, making
every command return "unknown" with no visible error.

## The Error

```
openai.BadRequestError: Error code: 400 - {
  'error': {
    'message': 'The supported API model names are deepseek-v4-pro or deepseek-v4-flash, but you passed deepseek-flash.',
    'type': 'invalid_request_error'
  }
}
```

## The Fix

1. Read the API error message body — it tells you the supported model names
2. Update `config.yaml`: `model: "deepseek-v4-flash"`
3. Check the DeepSeek docs for current model names before deploying

## The Silent Swallowing Pattern (anti-pattern)

```python
def parse(self, text: str) -> Command:
    try:
        response = self.client.chat.completions.create(...)
        data = json.loads(response.choices[0].message.content)
        return Command(intent=data["intent"], params=data.get("params", {}))
    except Exception:
        return Command(intent="unknown")  # SILENT — no log, no traceback
```

## The Fix (with logging)

```python
def parse(self, text: str) -> Command:
    try:
        response = self.client.chat.completions.create(...)
        data = json.loads(response.choices[0].message.content)
        return Command(intent=data["intent"], params=data.get("params", {}))
    except Exception:
        import traceback
        traceback.print_exc()  # show the real error in server logs
        return Command(intent="unknown")
```

Without the traceback, the API error was invisible — the server returned 200 OK
with `{"reply": "Не понял команду"}` and the only clue was in the uvicorn log
(which wasn't being checked).

## Lesson

When an LLM parser starts returning "unknown" for every command, the first
thing to check is the server log for API errors. Model renames, auth failures,
and rate limits all produce the same silent fallback.

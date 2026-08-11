# Debugging Silent LLM Parser Failures

## Symptom

`/api/chat` returns `{"reply": "Не понял команду", "action": "unknown"}` for every input, even valid commands. Server log shows only `200 OK` — no error output.

## Root Cause

The command parser wraps the LLM call in a blanket `except Exception` that catches ALL errors (auth, network, model not found) and returns `Command(intent="unknown")`:

```python
def parse(self, text: str) -> Command:
    try:
        response = self.client.chat.completions.create(...)
        ...
        return Command(intent=data["intent"], ...)
    except Exception:                          # <-- swallows everything
        return Command(intent="unknown")       # <-- no logging
```

Common triggers:
- Wrong model name (API 400)
- Invalid/expired API key (API 401)
- Network timeout
- JSON parse error on LLM response

## Fix

Add traceback logging to the except block so the real error surfaces in server output:

```python
    except Exception:
        import traceback
        traceback.print_exc()                  # logs to stderr (visible in uvicorn output)
        return Command(intent="unknown")
```

After adding this, re-send a chat command and check the server log — the actual error (e.g., `openai.BadRequestError: The supported API model names are...`) will be visible.

## Example Session

**Before fix:** `curl -X POST /api/chat -d '{"text":"что такое Python"}'` → `{"action":"unknown"}` every time. Server log: `200 OK`, nothing else.

**After fix:** Same curl → same response, but server log now shows:
```
Traceback (most recent call last):
  File "commands.py", line 49, in parse
    response = self.client.chat.completions.create(...)
  ...
openai.BadRequestError: Error code: 400 - {'error': {'message': 'The supported API model names are deepseek-v4-pro or deepseek-v4-flash, but you passed deepseek-flash.'}}
```

**Resolution:** Update model name in `config.yaml` from `deepseek-flash` to `deepseek-v4-flash`. Chat works immediately.

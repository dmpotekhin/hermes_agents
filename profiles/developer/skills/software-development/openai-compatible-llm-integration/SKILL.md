---
name: openai-compatible-llm-integration
description: "Use when wiring an OpenAI-compatible LLM endpoint."
version: 1.0.0
tags: [llm, openai-compatible, deepseek, huggingface, vllm, ollama, chat-completions, provider]
platforms: [linux, macos]
---

# OpenAI-Compatible LLM Integration

Wiring any `/v1/chat/completions`-style endpoint (DeepSeek, HuggingFace Inference router, vLLM, Ollama, LM Studio) into a backend or Hermes. The protocol is identical across providers — only base URL, key, model id, and body quirks differ.

## Triggers
- "Подключи бесплатную модель / free model" (HF Inference, DeepSeek, ...)
- Adding an LLM call to a FastAPI/Node backend
- Configuring a new provider in Hermes (`hermes auth add`, `model.aliases`)
- Swapping an LLM provider without touching call sites

## Core pattern

1. **Identify the endpoint**: base URL is whatever responds to `POST <base>/chat/completions` with `{"model","messages","temperature","stream"}` and a Bearer key.
   - DeepSeek: `https://api.deepseek.com/chat/completions`, model `deepseek-chat`
   - HF Inference: `https://router.huggingface.co/v1`, OpenAI-compatible (see references/huggingface-inference-free-tier.md)
   - vLLM/Ollama local: `http://127.0.0.1:8000/v1` / `http://127.0.0.1:11434/v1`
2. **Env-config, provider-agnostic** (never hardcode URL/model in code):
   ```python
   LLM_API_KEY  = os.getenv("LLM_API_KEY", os.getenv("DEEPSEEK_API_KEY", "")).strip()
   LLM_MODEL    = os.getenv("LLM_MODEL", os.getenv("DEEPSEEK_MODEL", "deepseek-chat")).strip()
   LLM_URL      = os.getenv("LLM_URL", os.getenv("DEEPSEEK_URL", "https://api.deepseek.com/chat/completions")).strip()
   LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1024"))
   # Extra body JSON, e.g. {"chat_template_kwargs":{"enable_thinking":false}} for Qwen on HF
   _extra = os.getenv("LLM_EXTRA_JSON", "").strip()
   LLM_EXTRA_JSON = json.loads(_extra) if _extra else {}
   # Legacy aliases so old .env / tests keep working
   DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_URL = LLM_API_KEY, LLM_MODEL, LLM_URL
   ```
   Send `**config.LLM_EXTRA_JSON` inside the request body. Never store the key in code — `.env` only.
3. **Live-probe BEFORE wiring** (a 10-line script, not a unit test): POST one real request, print `status_code`, `message.content`, `reasoning_content` length, `finish_reason`. A mocked test tells you nothing about the provider's actual behavior.
4. **Hermes**: `hermes auth add <provider> --type api-key --api-key <KEY>` then `hermes config set model.aliases.<name> '<provider>/<org>/<model>'`. Verify with `hermes -z "..." -m <alias>` (short probe).

## Pitfalls (all hit in production)

- **Reasoning models eat max_tokens**: models like GLM-4.7-Flash, Qwen3 with thinking enabled emit `reasoning_content` first. With small `max_tokens` the answer is cut off: `content=''`, `finish_reason='length'`, reasoning thousands of chars. Fixes: (a) raise `max_tokens`, (b) disable thinking — Qwen: `LLM_EXTRA_JSON={"chat_template_kwargs":{"enable_thinking":false}}` → plain fast answer.
- **`HTTP 402` from HF Inference = model NOT free / credits depleted** — NOT a network error. `/v1/models` lists all models, but most return 402 on a free account. Only a handful are actually free (see HF reference).
- **Rate-limit can masquerade as 402/busy**: after a burst of probes models start failing with 402/429; a single retry after a pause succeeds. Don't conclude "credits gone" from one failing batch.
- **Timeout too small**: free-tier reasoning models can take 30s+; use 60–120s in probes, and a sane timeout (30s) in the app, configured not hardcoded.
- **Empty content is a real failure mode**: `httpx` returns 200 with `content: ''` — always check `finish_reason` and content, not just status code.
- **Don't log secrets**: mask `Authorization: Bearer` and API keys in every command; never echo `.env` values into chat.

## Verification
- Canonical test suite must pass (the provider is mocked in unit tests).
- One live probe (script in temp dir, `hermes-verify-*` prefix) exercising: env parsing → payload shape (mocked httpx, assert `max_tokens` and `**LLM_EXTRA_JSON` land in body) → one real call.
- Report latency: a fast free model answers in ~1s; reasoning models 30s+.

## References
- `references/huggingface-inference-free-tier.md` — HF Inference router specifics: what's actually free, 402 semantics, thinking-disable per model, account checks.

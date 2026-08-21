# HuggingFace Inference — free tier specifics (verified 2026-08)

Findings from connecting a free HF account (no PRO) to the Inference router as an
OpenAI-compatible LLM provider. All checks done against `https://router.huggingface.co/v1`.

## Endpoint & auth
- OpenAI-compatible base: `https://router.huggingface.co/v1`
  - `GET /v1/models` — lists models the router knows (133 on free account)
  - `POST /v1/chat/completions` — standard OpenAI body + Bearer HF token
- Send header `X-Request-Origin: hermes` (or any app name) with API calls.
- Account check: `GET https://huggingface.co/api/whoami-v2` with Bearer token
  → `type: free` vs `isPro`, `canReadGatedRepos`, token scopes. A fine-grained token
  needs `inference.serverless.write` (+ `inference.endpoints.infer.write`) to call the router.
- Classic serverless endpoint `https://api-inference.huggingface.co` is legacy/unreliable —
  prefer the router.

## What is ACTUALLY free (2026-08-19, free account)
`/v1/models` lists everything, but most models return `HTTP 402` on a free account.
Verified working free (HTTP 200, real content):
- `zai-org/GLM-4.7-Flash` — but it is a reasoning model (see thinking pitfall)
- `Qwen/Qwen3.5-35B-A3B` — with thinking disabled answers in ~1s

Verified NOT free (402): Qwen3-8B, Gemma-4-31B-it, Qwen3-Coder, DeepSeek-V3.2/V4-Flash
(through this router), Kimi, Llama variants, Mistral variants.
Rule: never trust the model list; probe each candidate with one real chat request.

## 402 vs rate-limit — how to tell
- `402 {"error":{"message":"You have depleted your monthly included credits..."}}`
  → model is paid on this account (or the tiny monthly free credit bucket ran out).
- `429 engine_overloaded` / busy → transient, retry after a pause.
- A burst of probes can trigger 429/402-style failures; one retry after ~30–60s usually
  succeeds on the truly-free models. Don't burn credits probing dozens of models in a loop —
  probe 2–3 candidates, then stop.

## Thinking/reasoning pitfall (critical)
Free reasoning models (GLM-4.7-Flash, Qwen3.5 with thinking on) emit `reasoning_content`
BEFORE `content`. With small `max_tokens` you get:
- `content: ''`, `finish_reason: 'length'`, `reasoning_content` thousands of chars
- Response latency 10–35s even for a trivial prompt

Fixes, per model:
- Qwen family: `"chat_template_kwargs": {"enable_thinking": false}` in the request body
  → plain answer, ~1s. (Verified on Qwen/Qwen3.5-35B-A3B.)
- GLM-4.7-Flash: `"thinking": {"type": "disabled"}` returned `engine_overloaded` 429;
  `chat_template_kwargs` was ignored. Only reliable fix: raise `max_tokens` (1024 was
  insufficient; the reasoning alone can exceed it). Prefer Qwen with thinking disabled
  for parsing/extraction jobs.
- Always check `finish_reason` and content, never just HTTP 200.

## Hermes integration
- `hermes auth add huggingface --type api-key --api-key <HF_TOKEN>` — registers provider.
- Aliases: `hermes config set model.aliases.hf-glm 'huggingface/zai-org/GLM-4.7-Flash'`
  (or hf-qwen → `huggingface/Qwen/Qwen3.5-35B-A3B`).
- Verify: `hermes -z "..." -m hf-qwen`.

## Cost notes
Free account includes a tiny monthly credit bucket; a single probe of a big model can
consume a meaningful share. `whoami-v2` returns `canPay`/`periodEnd` — check before
planning heavy use. For serious volume, prefer local inference (llama.cpp/vLLM) or a paid tier.

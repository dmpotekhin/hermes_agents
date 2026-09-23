# Perplexity & non-built-in providers in Hermes

Verified 2026-09-08 (web_search of Perplexity docs / aipricing.guru / cloudzero; the
`hermes-agent` providers-and-models.md table confirms Perplexity is NOT a built-in
provider profile).

## Adding Perplexity to Hermes

- No `perplexity:` provider profile ships with Hermes. Two supported paths:
  1. Add a **user-defined model alias** with own `base_url` + `key_env` (preferred;
     keeps the free HF default untouched). See SKILL.md "Provider with no built-in
     Hermes entry" section for the exact `hermes config set` commands and the
     `providers-and-models.md` note that an alias with its own base_url authenticates
     with its own key — never carried over from the previously-active provider.
  2. Route through `openrouter` (which lists Perplexity models) with a single
     OpenRouter key — but that's an extra middleman + same per-token cost.
- Base URL: `https://api.perplexity.ai` (OpenAI-compatible `/chat/completions`).
  API key prefix: `pplx-`. Create/set at https://www.perplexity.ai/settings/api
  (requires account + card: NO free API tier).
- Keyword to use Perplexity as a SEARCH (not model) provider in Hermes: the bundled
  `web-search-plus` plugin already has a Perplexity search path
  (`~/.hermes/plugins/web-search-plus/search.py` → `search_perplexity()`), keyed on
  `PERPLEXITY_API_KEY`, model `sonar-pro`, endpoint `https://api.perplexity.ai/chat/completions`.
  It also has a DISTINCT `kilo-perplexity` routing provider that uses
  `KILOCODE_API_KEY` + `https://api.kilo.ai/api/gateway/chat/completions` with model
  `perplexity/sonar-pro`. Don't conflate the two keys/providers.

## Perplexity API pricing (pay-as-you-go, per million tokens)

| Model | input | output | notes |
|-------|-------|--------|-------|
| sonar | $1 | $1 | |
| sonar-pro | $3 | $15 | most-used; matches GPT-5.4 on output |
| sonar-reasoning-pro | $2 | $8 | |
| sonar-deep-research | $2 | $8 | + separate citation / reasoning / search fees |

Plus a request fee that varies by search-context size (Low / Medium / High).
`sonar-deep-research` and large search contexts add fees on top of token cost.
Consumer Pro subscription ($20/mo) is the better deal for individual research but
is the chat/web search product, NOT the API — API bills separately per token.

## "FireClaw" — name collision (3 DIFFERENT projects)

When the user says "FireClaw", disambiguate before acting:

1. **Eldergenix/FireClaw** (github.com/Eldergenix/FireClaw) — open-source AI pair
   programmer, analogous to Claude Code / Codex / OpenCode. Free (open-source), but
   needs YOUR OWN LLM API key. Most likely meaning for a user who vibecodes via
   OpenCode/KiloCode.
2. **fireclaw.app / raiph-ai/fireclaw** — security proxy, "a firewall for your
   agent's brain", protects against prompt injection. Open-source, community
   endpoint built in, no API keys. (Also "fireclaw" = a Firecrawl browser extension.)
3. **fireclaw.ai** — packages OpenClaw into a portable single-binary/microVM.
   Open-source, needs own LLM key.

All three are open-source/free to install; you pay only for whatever LLM you point
them at via your own key.

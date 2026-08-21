# OmniRoute — self-hosted AI gateway (verified install, 2026-08-21)

OmniRoute = free/open-source AI gateway: one OpenAI-compatible endpoint
(`http://localhost:20128/v1`), 342 providers, ~90 free tiers, auto-fallback,
token compression. Repo `github.com/diegosouzapw/OmniRoute` (default branch
`release/vX.Y.Z`, repo is ~422 MB — do NOT `git clone` it to install).

## Install (npm global)

```bash
export PATH="$HOME/.nvm/versions/node/v22.23.2/bin:$PATH"   # REQUIRED, see below
npm install -g omniroute
omniroute
```

- Dashboard: `http://localhost:20128` · API: `http://localhost:20128/v1`
  (base_url for any OpenAI-compatible tool).
- Package is HUGE: node_modules grows past 2 GB (antd, lobehub/ui, react 19,
  better-sqlite3, swc). On slow links expect 20+ min. It is normal — not a hang.

## Node version — must be v22

- `undici@8.10.0` (dep) declares `node >=22.19.0`; on v20.20.0 npm only warns
  EBADENGINE but the safer path is v22.23.2 (both are in nvm on this machine:
  `~/.nvm/versions/node/v22.23.2/bin`).
- System node is v14 — breaks everything; always export the nvm PATH first.

## Pitfalls hit during install

- **ENOTEMPTY after killing an interrupted install**: npm fails with
  `rename .../node_modules/omniroute -> .omniroute-XXX: directory not empty`.
  Fix: `rm -rf ~/.nvm/versions/node/<ver>/lib/node_modules/omniroute
  ~/.nvm/versions/node/<ver>/lib/node_modules/.omniroute-*` and re-run.
- **@swc/core postinstall dies with SIGBUS** (verified 2026-08-21, node v22.23.2):
  `npm error command sh -c node postinstall.js` / `signal SIGBUS` — the
  prebuilt swc binary is corrupted on download through the VPN/proxy. Official
  fix from their README: `OMNIROUTE_SKIP_POSTINSTALL=1 npm install -g omniroute`.
  swc is a build-time dep; the app runs fine without it (verified: v3.8.49
  starts, `/v1/models` answers). Do NOT retry plain install — it fails the same
  way every time on this machine.
- **VPN on this machine breaks web_extract**: with VPN active, DNS resolves
  github.com / omniroute.online to 198.18.x.x and web_extract/web tools refuse
  them as «private network address». Workaround: `curl -s URL -o /tmp/f.md`
  directly, or ask the user to disable VPN (default route then goes via en0 and
  downloads are ~10x faster).
- Peer-dep warnings (react 19 vs @emoji-mart/react) are harmless per README —
  ERESOLVE warnings don't block install.

## Adding provider keys (CLI — verified 2026-08-21)

Two DIFFERENT keys — do not confuse them when the user says «у меня есть токен» (a THIRD key exists, see Radar section below):

1. **Provider key** (DeepSeek/OpenRouter/OpenAI/...): added INTO OmniRoute so it
   can call upstream models. CLI:
   `omniroute keys add <provider> <key>`
   Safe (key never lands in shell history): `echo "<key>" | omniroute keys add <provider> --stdin`
   Provider slugs: `deepseek`, `openrouter`, `openai`, `anthropic`, `groq`, `xai`,
   `moonshot` ... (342 in catalog, see `omniroute keys add --help`).
2. **OmniRoute client token**: the key CODING TOOLS use to talk to the gateway
   (Dashboard → Endpoints). It is consumed by the client, NOT added into OmniRoute.

Inspect/remove: `omniroute keys list` · `omniroute keys remove <provider>`.
Other useful CLI: `nodes list|add` (custom endpoints), `oauth start` (OAuth
providers), `chat "hi"` (one-shot test), `simulate "hi"` (dry-run routing without
calling upstream). After adding a provider key, model `auto` picks it up
automatically with fallbacks.

## Radar subscription key (the «omniroute.online» token, verified 2026-08-21)

THIRD key type: **OmniRoute Radar** — a paid subscription bought at
`radar.omniroute.online/planos` (pt-BR page; prices as of 2026-08-21:
Semestral $10 / Anual $18.90 / Vitalício $47.90). It is NOT a provider key and
NOT a client token. It activates a **signed live-catalog overlay** (curated
free-model offers refreshed between releases, `radar.omniroute.online` is a
real Cloudflare-hosted site; `omniroute.online` main site is a static landing
page with no /v1 API of its own).

- **Radar keys are NOT usable in v3.8.49**: the feature (feat #9515 + «paste-key
  input on the activation screen» #9758) only exists in v3.8.50. In v3.8.49 the
  word «Radar» appears in the bundle ONLY as recharts radar charts — there is no
  code path to enter a Radar key, no env var (`grep -r OMNIROUTE_` finds none),
  nothing in storage.sqlite `key_value`.
- **npm latest is still 3.8.49** (as of 2026-08-21); v3.8.50 is marked TBD in
  CHANGELOG. Do NOT burn an hour building the branch from source: the git
  tarball of `release/v3.8.50` (62 MB download) requires a full `npm install`
  of devDependencies (~4 GB: eslint, playwright, stryker...) which on a slow
  link takes 50+ min and dies with `ECONNRESET`. Correct play: check
  `npm view omniroute version`; when it says 3.8.50, upgrade with
  `OMNIROUTE_SKIP_POSTINSTALL=1 npm install -g omniroute` and the user enters
  their Radar key on the Dashboard activation screen.
- When the user says «у меня токен от omniroute.online» → they mean a Radar key.
  Explain the three-key distinction (provider / client / Radar) before promising
  anything, and check the installed version first.

## First-run flow (per README, verify on first `omniroute` run)

1. Dashboard → Providers → connect **Kiro AI** (free Claude, ~50 credits/mo) or
   **OpenCode Free** (no auth) for a zero-config start.
2. Point a coding tool at: `Base URL http://localhost:20128/v1`, key from
   Dashboard → Endpoints, `model: auto`.
3. Verify: `curl http://localhost:20128/v1/models -H "Authorization: Bearer <key>"`

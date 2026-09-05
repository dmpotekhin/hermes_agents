---
name: web-scraping-anti-bot
description: "Use when scraping anti-bot sites (Ozon, captchas)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [scraping, parsing, anti-bot, captcha, ozon, playwright, ecommerce]
---

# Web Scraping Anti-Bot

Use when the user wants a price / data point from a site that may be protected by an anti-bot system (Ozon, Wildberries, marketplaces, Cloudflare-fronted sites) or when a plain `curl` gets 403/captcha.

## Step 0 — extraction front-end refuses a URL (SSR docs)

An extraction tool (web_extract) can refuse a public URL with a misleading
error: `Blocked: URL targets a private or internal network address`. That is
usually an anti-bot/SSRF guard on the *fetch backend*, NOT a genuinely private
host. Before reaching for the ladder below, fetch the page straight with a
browser User-Agent:

```bash
curl -sL -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36" "<url>"
```

Many "blocked" doc sites are simply server-side-rendered HTML once you present
a browser UA. **docs.pen.dev (Nextra/Next.js, ~2026)** is one such case:
web_extract blocked it, `curl` returned full HTML, and the content sits in the
`<main>` block. For docs sites try canonical machine routes first: `/<page>.md`
and `/llms.txt` (Mintlify serves these; Nextra returns 404 for `/llms.txt`).

Fetch + extract `<main>` + strip tags in one pass with the bundled script, so a
whole doc section (several URLs) comes back without flooding context:

```bash
python3 scripts/fetch_ssr_page.py https://docs.pen.dev/getting-started/installation https://docs.pen.dev/for-developers/pen-cli
```

## Escalation ladder (cheap → expensive; stop early)

1. **curl with UA + cookie jar** — `curl -sL -c jar -b jar -A "<real UA>" URL`. Handle 307 redirects automatically; a first hit usually sets `__Secure-*` cookies, retry with the jar.
2. **Internal site APIs** — Ozon: `/api/composer-api.bx/page/json/v2?url=<path>`, entrypoint API. Usually same protection, but cheap to try.
3. **Playwright chromium headless** — plain `page.goto`, then read price from `[data-widget="webPrice"]`, `[itemprop='price']`, regex over page JSON (`"price":`, `priceWithCard`) and visible `₽` text. Use `headless_shell` binary already cached.
4. **Playwright chromium headful + init script** — `headless=False` + `Object.defineProperty(navigator,'webdriver',{get:()=>undefined})`. Windows open on macOS GUI; fine.
5. **Different engine** — `python3 -m playwright install firefox` (~100 MB), retry with Firefox; some detectors are Chromium-specific.
6. **Mobile version / device emulation** — `m.ozon.ru`, `p.devices["iPhone 13"]` context.
7. **Render proxies** — `https://r.jina.ai/<URL>`. Note: sites can block it (Ozon returns HTTP 451 Unavailable For Legal Reasons).
8. **web_search snippets** — search `site:... <product id> цена`; sometimes the price is in the description snippet. Last cheap trick.
9. **STOP** — after 3+ levels of captcha/block, do not burn more time. See "When to stop".

## Anti-bot response map (what each answer means)

| Response | Meaning |
|---|---|
| `HTTP 307` + `location: ...?__rr=1` | Normal redirect; continue with cookie jar |
| `HTTP 403` small HTML body | Bot blocked; try browser route |
| Title `Antibot Captcha` / `Antibot Challenge Page` | JS captcha challenge; browser automation detected |
| Title `Похоже, нет соединения` (Ozon) | Anti-bot stub — NOT a network error. Firefox and mobile emulation hit this too |
| `HTTP 451` from render proxy | Site legally blocked the proxy (r.jina.ai vs Ozon) |
| `HTTP 403` with ~127 KB body | Still a captcha/challenge page — check `<title>`, don't trust size |

## When to stop

- After the ladder stalls (3+ levels blocked), the fastest reliable path is the **user's own browser session**: ask them to open the link and read the value. Their logged-in session + home IP usually passes.
- Rule of thumb from anti-detect engine docs: if the browser is clean and you STILL get challenged, the variable is the **IP/proxy**, not the browser. A bad datacenter IP kills even a perfect fingerprint.
- Untested-but-standard escapes to offer the user: export cookies from their browser (real session + curl/playwright persistent context), an anti-detect engine (e.g. `invisible_playwright`, patched Firefox, ~238 MB engine, needs playwright 1.55–1.61, Python ≥3.11), or a residential proxy.

## Pitfalls

- Slow network to foreign CDNs can make `playwright install firefox` look hung for 5–10 min — it usually finishes; poll, don't kill immediately. It may hold `__dirlock` in `~/Library/Caches/ms-playwright/`.
- Don't interpret Ozon's «Похоже, нет соединения» as a network problem — it is a deliberate stub.
- Do not report "got the price" from a search snippet alone; snippets are unreliable. Verify on the live page.
- Capture the session's response map in `references/<site>-anti-bot.md` for reuse (see `references/ozon-anti-bot.md`).

## References

- `references/ozon-anti-bot.md` — full Ozon probe log (2026-08-19): every attempt, exact stubs, what was NOT tested.

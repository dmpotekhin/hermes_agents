---
name: antibot-web-scraping
description: "Use when scraping antibot-protected sites (Ozon)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [scraping, parsing, antibot, playwright, ozon, invisible-playwright, price]
---

# Antibot Web Scraping

Use when the task is to extract data (especially prices) from sites that block automation: Ozon, Wildberries, Cloudflare/DataDome-protected shops, etc. Also use when a plain `curl`/`requests` fetch returns 403/captcha and you need to know which browser-level tool will actually get through.

## Escalation ladder (cheapest first)

Try each step only long enough to confirm it fails; do not burn 20 minutes on a step the previous one already ruled out. A fresh-headless `playwright` run costs ~30s; a full engine download costs minutes-to-hours on a slow link — escalate deliberately.

1. **curl with real browser UA + cookie jar** (`-L -c jar -b jar`). Sites like Ozon return a `307 → ?__rr=1` redirect then `403` antibot page. Confirm the body: `<title>Antibot ...</title>` means stop.
2. **Internal/mobile APIs** — e.g. Ozon's `https://www.ozon.ru/api/composer-api.bx/page/json/v2?url=<path>` — usually also `403` with an `incidentId` JSON. Cheap to try, rarely works.
3. **Playwright Chromium headless** — expect `<title>Antibot Captcha</title>` / `Antibot Challenge Page` on strong antibot.
4. **Playwright Chromium headful** (visible window) + `navigator.webdriver` spoof via `add_init_script` — Ozon still blocks.
5. **Playwright Firefox** (`python3 -m playwright install firefox`) and **mobile emulation** (`p.devices["iPhone 13"]`, `m.<site>.ru`) — Ozon answers both with the stub `<title>Похоже, нет соединения</title>` (its generic automated-client block; this is NOT a network error — retrying does not help).
6. **Rendering proxies** (`https://r.jina.ai/<url>`) — can return `HTTP 451 Unavailable For Legal Reasons` for RU marketplaces that legally demanded removal. Do not retry.
7. **invisible_playwright** (patched Firefox, C++-level fingerprint spoofing, deterministic seed, humanized cursor) — the strongest free option. Install + engine seeding: see `references/invisible-playwright-engine-install.md`.
8. **User's own session** — if everything above is blocked, the fastest reliable route is often asking the user to open the URL in their own logged-in browser and read the price, or to export cookies and hand them over. Do this early when the goal is a one-off price check, not a pipeline.

## Key mental model

- **When even a pristine browser gets a captcha/stub, part of the problem is the IP**, not just the fingerprint. invisible_playwright's own README: ~90% of remaining challenges trace to proxy/IP reputation. A residential RU IP matters for RU marketplaces; datacenter IPs are burned from the start.
- **Escalation is about cost**: every failed browser attempt is cheap until you start downloading engines. Decide first whether this is a one-off (→ step 8) or a recurring pipeline (→ step 7).
- The price lives in page state even on normal pages: look for `[data-widget="webPrice"]` / `[data-widget="webSinglePrice"]` DOM widgets and JSON keys `price`, `priceValue`, `priceWithCard`, `priceWithoutCard` in `page.content()`.

## Ozon specifics

Full observed antibot behavior, stub strings, and the price-widget selectors: `references/ozon-antibot.md`.

## Pitfalls

- **"Похоже, нет соединения" / "no connection" stubs are deliberate antibot replies**, not transient network failures. Do not loop retries on them.
- **Trickle-slow connections hang Python downloaders**: `requests`' per-read `timeout=` does not trip when a byte arrives every ~60s. For any large download on a slow/unstable link use `curl -C - --speed-limit 1024 --speed-time 60 --retry 10 --retry-all-errors` (resume + abort-and-retry on stalls).
- **Don't promise a scrape result before the engine/flow actually produced data.** A pipeline whose final fetch never completed is "in progress", not "works".
- **Search engines rarely surface live prices** for product pages — don't rely on `web_search` snippets for a current price.

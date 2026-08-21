---
name: ecommerce-price-scraping
description: Use when scraping prices from antibot marketplaces.
version: 1.0.0
---

# E-commerce price scraping (antibot marketplaces)

Use when the user asks for a product price from Ozon, Wildberries or another heavily protected marketplace, or when plain curl/Playwright gets captcha/skeleton pages.

## Strategy: cheap-first escalation ladder

1. curl with browser UA + cookie jar (`-L -c cookies.txt`) — handles Ozon 307 redirect `?__rr=1`; often 403 → escalate
2. Internal/known APIs (5 min max, then move on):
   - Ozon composer-api `https://www.ozon.ru/api/composer-api.bx/page/json/v2?url=%2Fproduct%2F...` → 403 (dead end)
   - WB `card.wb.ru/cards/v1|v2/detail?nm=<id>` → 404 (dead end, do not retry)
   - m.* mobile subdomains (m.ozon.ru, m.wildberries.ru) → connection failure / no data (dead end)
3. Plain Playwright headless → headful: both get "Antibot Captcha" (Ozon) / home-page skeleton (WB)
4. **InvisiblePlaywright** (patched Firefox stealth) — the working hammer for both

## Install & engine (slow-network safe)

```bash
pip3 install --user invisible-playwright   # pins invisible-core
```

First launch downloads a ~237 MB engine from GitHub Releases. On slow/unstable networks the built-in `requests` downloader hangs (per-socket timeout, 30-min wall-clock deadline; override `INVISIBLE_DOWNLOAD_DEADLINE`). Preload it manually instead:

1. Read `site-packages/invisible_core/seal.json` → tag, upstream_version, build_id, asset name + sha256 for your platform
2. URL: `https://github.com/feder-cr/firefox_antidetect_patch/releases/download/{tag}/{asset}`
3. `curl -L --retry 10 --retry-delay 5 --retry-all-errors -C - --speed-limit 1024 --speed-time 60 -o /tmp/<asset> "<url>"` (resume + abort-stalled + retry)
4. Verify sha256 against seal.json
5. Extract into `~/Library/Caches/invisible-playwright/{tag}_{upstream}_{build_id}/` — `ensure_binary` adopts an existing tree (verify_engine → stamp) instead of downloading
6. macOS: `xattr -dr com.apple.quarantine` on the extracted tree

Worked detail: `references/engine-preload.md`. Per-site code: `references/ozon-wildberries-recipes.md`. Copy-ready WB parser (change URL, run): `templates/wb_price.py`.

## Site recipes (short)

**Ozon** — single pass works:
- `InvisiblePlaywright(seed=42, headless=True, locale="ru-RU")`, goto product URL, wait ~8s, wait_for_selector `[data-widget="webPrice"]`
- Extract: `page.title()`, webPrice widget `inner_text`, regex `"price..."` from HTML, visible `₽` Counter from body text
- Result shows main price, bank price, old price

**Wildberries** — needs TWO passes:
- Pass 1: goto `https://www.wildberries.ru/` (establishes cookies / passes bot gate), wait ~5s
- Pass 2: goto `/catalog/<id>/detail.aspx`, then wait up to 45s for `h1` (SPA render)
- Product `<title>` embeds the final price ("купить за 4 695 ₽")
- Visible-₽ Counter + `.price__lowered` selectors; card API is dead (404)

## Pitfalls

- Headless gets detected more often (WB shows empty skeleton) — use `headless=False` (headful) for stubborn sites
- First WB goto can return home-page skeleton with empty title; the two-pass pattern fixes it
- GitHub CDN is flaky from RU networks — curl with `--speed-limit/--speed-time/-C -` is the only reliable downloader; `requests`-based downloads stall silently (check with `lsof -p <pid> | grep ESTAB` + cache dir growth)
- Engine cache persists in `~/Library/Caches/invisible-playwright/` — check before re-downloading; subsequent launches are instant
- On this user's machine, long multi-part shell one-liners (joined with `;`/`&&`) hit command timeouts — split into single-purpose commands; use `patch` for JSON edits; write ad-hoc verify scripts that self-delete (`os.remove(__file__)`)
- Never fabricate a price: if the page shows captcha/skeleton, say so and escalate — don't invent output

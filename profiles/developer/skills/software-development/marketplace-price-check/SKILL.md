---
name: marketplace-price-check
description: "Get Ozon/WB prices via invisible_playwright."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [price, marketplace, ozon, wildberries, scraping, invisible-playwright, antibot]
---

# Marketplace Price Check (Ozon / Wildberries)

Use when the user drops a product URL from Ozon or Wildberries (or another RU
marketplace with anti-bot) and asks for the price. Also the general strategy for
"какой там антибот, что пройдёт".

## Strategy ladder (cheap first, heavy artillery last)

1. **web_search** the article number — sometimes price is in the snippet (rare).
2. **curl** the product URL with a Chrome UA (`curl -sL -A "<chrome-ua>"`).
   Ozon → 307/403; WB → skeleton homepage (25 KB, og:title = main page, no `<title>`).
3. **Marketplace API endpoints** (fast if alive):
   - Ozon composer: `https://www.ozon.ru/api/composer-api.bx/page/json/v2?url=%2Fproduct%2F...` → 403
   - WB card: `https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm=<article>` → 404 (both v1 and v2; card.wb.ru is dead/blocked as of 2026-08)
   - m.wildberries.ru → no response (HTTP 000) via curl
4. **InvisiblePlaywright** (proven to pass both Ozon and WB anti-bot) — go straight here for Ozon/WB; don't waste time on plain curl/Playwright/Firefox.

## Working pattern: InvisiblePlaywright

Environment (macOS x86_64): Python 3.11.7, Playwright 1.58.0,
invisible-playwright 0.7.2, engine cached at
`~/Library/Caches/invisible-playwright/firefox-20_151.0_20260817150639/` —
launches instantly, NO download on first run. First-ever run downloads a GeoIP
db (~122 MB) automatically.

```python
from invisible_playwright import InvisiblePlaywright
with InvisiblePlaywright(seed=42, headless=True, locale="ru-RU") as browser:
    page = browser.new_page()
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(8000)
    print("TITLE:", page.title()[:120])
    # visible price candidates via regex on body text:
    # re.findall(r'\b[\d][\d\s]{1,7}\s*(?:₽|руб)', body_text) → Counter
```

Ozon specifics (full script): `references/ozon.md`
Wildberries two-pass scheme (homepage → card, headful, long render wait):
`references/wildberries.md`
Engine install / slow-GitHub download recipe: `references/invisible-playwright-setup.md`

## Extraction heuristics (both sites)

- Read `page.title()` — WB embeds the price in the title: «... купить за 4 695 ₽ ...».
- Regex visible ₽ amounts on body text, dedupe with `Counter.most_common(10)`.
  Multiple prices are normal: current price, price with bank/wallet discount,
  old crossed-out price — report all three, don't collapse.
- Save `page.content()` to /tmp for later grep when extraction is ambiguous.

## Standalone script (user self-run / PyCharm)

- Ready-made runner: `scripts/ozon_price.py` in this skill (copy to e.g.
  `~/ozon-price-check/ozon_price.py` for the user). Takes the product URL as
  argv — no per-product code editing; report all prices (main, bank-discount,
  crossed-out old).
- PyCharm config: File → Open project folder → Settings → Python Interpreter →
  **System Interpreter → /usr/local/bin/python3** (NOT a fresh venv —
  `invisible_playwright` lives in user site-packages `~/Library/Python/3.11/`).
  Run → Edit Configurations → Parameters = quoted URL; or just run from the
  built-in terminal: `python3 ozon_price.py "<url>"`.
- If a venv is created anyway: `pip install invisible-playwright` inside it —
  the engine is reused from `~/Library/Caches/invisible-playwright` (no re-download).
- ~15-20 s per run (stealth engine startup) is normal. "no price widget" ⇒
  captcha → just rerun.

## Pitfalls

- **Do NOT start with plain headless Chromium on Ozon** — «Antibot Captcha»;
  Firefox vanilla — «Похоже, нет соединения»; all waste. Go InvisiblePlaywright.
- **WB direct product URL returns the homepage skeleton** — see two-pass in
  references/wildberries.md; the fix is visiting the homepage first (cookies/gate),
  then the card, then waiting up to 45 s for the rendered product page.
- **GitHub downloads are slow (~100–215 KB/s)** — engine must be fetched with
  curl resume flags, not the built-in downloader (it hangs). See setup reference.
- card.wb.ru API can die/change without notice — verify with `-w "HTTP %{http_code}"`
  before writing parser logic around it.
- Long compound terminal commands can time out/block on this machine — prefer
  single commands or `write_file` + short runner script.

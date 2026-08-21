# Ozon & Wildberries price extraction — verified recipes (2026-08-19)

Both worked first try with InvisiblePlaywright after the engine preload (see `engine-preload.md`). Run with `python3 -u script.py 2>&1` from /tmp.

## Ozon — single pass

```python
import re
from collections import Counter
from invisible_playwright import InvisiblePlaywright

URL = "https://www.ozon.ru/product/<slug>-<article_id>/"

with InvisiblePlaywright(seed=42, headless=True, locale="ru-RU") as browser:
    page = browser.new_page()
    try:
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print("goto exc:", repr(e)[:300])
    page.wait_for_timeout(8000)
    try:
        page.wait_for_selector('[data-widget="webPrice"], [data-widget="webSinglePrice"]', timeout=15000)
        print("PRICE WIDGET FOUND")
    except Exception:
        print("no price widget (maybe captcha)")
    print("TITLE:", page.title()[:120])
    print("webPrice =>", page.locator('[data-widget="webPrice"]').first.inner_text()[:300])
    html = page.content()
    pats = re.findall(r'"(?:price|priceValue|price_with_card|salePrice)"\s*:\s*"?(\d[\d\s]*(?:\.\d+)?)"?', html)
    print("json-price:", pats[:12])
    body_txt = page.locator("body").inner_text(timeout=5000)[:150000]
    print("visible-₽:", Counter(re.findall(r'\b[\d][\d\s]{1,7}\s*(?:₽|руб)', body_txt)).most_common(10))
```

Result: main price, bank price, old (strikethrough) price, "with other banks" price. One pass is enough.

## Wildberries — TWO passes

```python
import re
from collections import Counter
from invisible_playwright import InvisiblePlaywright

URL = "https://www.wildberries.ru/catalog/<id>/detail.aspx"

with InvisiblePlaywright(seed=42, headless=False, locale="ru-RU") as browser:
    page = browser.new_page()
    # PASS 1 — home page: cookies + bot gate
    page.goto("https://www.wildberries.ru/", wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(5000)
    # PASS 2 — product card
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    # SPA render: wait for h1 (full page appears with it)
    page.wait_for_selector("h1", timeout=45000)
    print("TITLE:", page.title()[:160])   # contains "купить за N ₽"
    body_txt = page.locator("body").inner_text(timeout=10000)[:200000]
    print("visible-₽:", Counter(re.findall(r'\b[\d][\d\s]{1,7}\s*(?:₽|руб)', body_txt)).most_common(12))
    # optional selectors: .price__lowered, .price-block__price, .price-block__wallet-price
```

Result: current price (also embedded in <title>), discount price, old price.

## Dead ends (do not retry)

- Ozon composer-api (`/api/composer-api.bx/page/json/v2?url=...`) → 403 even with cookies
- WB `card.wb.ru/cards/v1|v2/detail?nm=<id>` → 404 (both versions)
- m.ozon.ru / m.wildberries.ru → connection failure
- r.jina.ai proxy for Ozon → HTTP 451 "Unavailable For Legal Reasons"
- Wayback Machine for Ozon product pages → no snapshots of price

## Generic pattern that worked for both

1. `InvisiblePlaywright(seed=42, locale="ru-RU")` (seed fixed → consistent fingerprint)
2. headful when headless shows skeleton/captcha
3. wait_for_selector on a page-structure marker (h1 for WB, [data-widget=webPrice] for Ozon) rather than fixed sleep
4. multiple independent extraction channels: <title>, widget inner_text, JSON regex on HTML, visible-₽ Counter on body text

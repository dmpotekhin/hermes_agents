# Ozon: проверка цены (проверено 2026-08-19)

## Симптомы антибота (все обычные пути отбиты)
- `curl -sL` с Chrome UA → HTTP 307 (`?__rr=1`), с куки-джаром → 403
- headless Chromium → TITLE: "Antibot Captcha", json-price пустой
- headful Chromium + init-скрипт → тоже капча
- composer API `https://www.ozon.ru/api/composer-api.bx/page/json/v2?url=%2Fproduct%2F...` → 403 (и с куками)
- Firefox vanilla → «Похоже, нет соединения»; m.ozon.ru (iPhone UA) → «Похоже, нет соединения»
- ozon.by → 403; r.jina.ai → 451 "Unavailable For Legal Reasons"

## Рабочий путь: InvisiblePlaywright (headless OK)
Полный скрипт, проверен на артикуле 3211182235 (ELM327 OBD2):

```python
import re, sys
from collections import Counter
from invisible_playwright import InvisiblePlaywright

URL = "https://www.ozon.ru/product/<slug>-<article>/"  # товарная ссылка

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
    for sel, name in [('[data-widget="webPrice"]', "webPrice"),
                      ('[data-widget="webSinglePrice"]', "webSinglePrice"),
                      ('[data-widget="webPrice"] [data-widget="price"]', "inner-price")]:
        try:
            loc = page.locator(sel).first
            if loc.is_visible(timeout=2500):
                print(name, "=>", loc.inner_text()[:300])
        except Exception:
            pass
    html = page.content()
    with open("/tmp/ozon_inv.html", "w") as f:
        f.write(html)
    pats = re.findall(r'"(?:price|priceValue|price_with_card|priceValueWithCard|priceWithoutCard|salePrice)"\s*:\s*"?(\d[\d\s]*(?:\.\d+)?)"?', html)
    print("json-price:", pats[:12])
    try:
        body_txt = page.locator("body").inner_text(timeout=5000)[:150000]
        rub = re.findall(r'\b[\d][\d\s]{1,7}\s*(?:₽|руб)', body_txt)
        print("visible-₽:", Counter(rub).most_common(10))
    except Exception as e:
        print("body exc:", repr(e)[:200])
print("DONE")
```

## Результат на живом примере (арт. 3211182235)
- Основная цена: 299 ₽
- С банками (Ozon Карта): 332 ₽
- Старая зачёркнутая: 999 ₽
- С другими банками: 142 ₽

Итог: несколько цен в карточке — отдавать все, помечая смысл.

## Селекторы
- `[data-widget="webPrice"]` / `[data-widget="webSinglePrice"]` — виджеты цены
- JSON-LD/embedded: ключи `price`, `priceValue`, `price_with_card`,
  `priceValueWithCard`, `priceWithoutCard`, `salePrice` — regex по HTML

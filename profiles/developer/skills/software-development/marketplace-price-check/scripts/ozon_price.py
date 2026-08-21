#!/usr/bin/env python3
"""Парсер цены товара Ozon. Запуск:
    python3 ozon_price.py <URL товара>

Пример:
    python3 ozon_price.py https://www.ozon.ru/product/tochilka-dlya-nozhey-3886003827/

Примечания:
- URL передаётся аргументом — под любой товар, код не редактируется.
- ~15-20 с на запуск (stealth-браузер) — это нормально.
- "no price widget" => капча; просто перезапустить.
- Для PyCharm: System Interpreter /usr/local/bin/python3 (НЕ свежий venv —
  invisible_playwright стоит в user site-packages ~/Library/Python/3.11/).
  Если venv всё же создан: pip install invisible-playwright, движок
  подхватится из кэша ~/Library/Caches/invisible-playwright без перекачки.
"""
import re
import sys
from collections import Counter
from invisible_playwright import InvisiblePlaywright

URL = sys.argv[1] if len(sys.argv) > 1 else None
if not URL or "ozon.ru" not in URL:
    print("Укажи ссылку на товар Ozon:\n  python3 ozon_price.py https://www.ozon.ru/product/...")
    sys.exit(1)

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
    print("TITLE:", page.title()[:150])
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

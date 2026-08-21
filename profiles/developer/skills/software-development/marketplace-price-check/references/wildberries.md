# Wildberries: проверка цены (проверено 2026-08-19)

## Симптомы антибота
- Прямой `page.goto(карточка)` через InvisiblePlaywright (headless) → отдаётся
  СКЕЛЕТ ГЛАВНОЙ: 25 KB HTML, og:title «Интернет‑магазин Wildberries», пустой
  `<title>`, пустые visible-₽. URL при этом НЕ редиректится (FINAL_URL верный).
- card.wb.ru API: и v1 и v2 `/cards/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm=<артикул>` → HTTP 404 (мёртв, 2026-08)
- m.wildberries.ru через curl → HTTP 000 (не отвечает)

## Рабочий путь: двухпроходная схема (headful!)

Ключевое отличие от Ozon: нужен ПЕРВЫЙ заход на главную (ставит куки/проходит
гейт), потом переход на карточку, и долгий wait рендера (до 45 с). И headful
(не headless).

```python
import re
from collections import Counter
from invisible_playwright import InvisiblePlaywright

URL = "https://www.wildberries.ru/catalog/<article>/detail.aspx?targetUrl=MI"

with InvisiblePlaywright(seed=42, headless=False, locale="ru-RU") as browser:
    page = browser.new_page()
    # ПРОХОД 1: главная — куки/гейт
    try:
        page.goto("https://www.wildberries.ru/", wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print("home goto exc:", repr(e)[:200])
    page.wait_for_timeout(4000)
    # ПРОХОД 2: карточка
    try:
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print("card goto exc:", repr(e)[:300])
    print("FINAL_URL:", page.url[:200])
    # ждём реальный рендер карточки (не скелет)
    try:
        page.wait_for_selector(".product-page, .price-block, .product-card__price", timeout=45000)
        print("RENDERED")
    except Exception:
        print("no render (still skeleton?)")
    print("TITLE:", page.title()[:160])
    try:
        body_txt = page.locator("body").inner_text(timeout=5000)[:150000]
        rub = re.findall(r'\b[\d][\d\s]{1,7}\s*(?:₽|руб)', body_txt)
        print("visible-₽:", Counter(rub).most_common(10))
    except Exception as e:
        print("body exc:", repr(e)[:200])
    html = page.content()
    with open("/tmp/wb_inv.html", "w") as f:
        f.write(html)
    print("HTML_SAVED size", len(html))
print("DONE")
```

## Живой пример (арт. 1095634978, вентилятор voochi)
- TITLE: «Вентилятор безлопастной напольный с пультом мощный voochi 1095634978
  купить за 4 695 ₽ в интернет‑магазине Wildberries» — цена прямо в title!
- visible-₽: 4 601 ₽ (x2, со скидкой/кошельком), 4 695 ₽ (x2, основная),
  11 000 ₽ (x2, старая зачёркнутая)
- Полный рендер: ~1.1 MB HTML

## Признаки успеха
- `<title>` непустой и содержит «купить за N ₽»
- visible-₽ Counter непустой, обычно три группы (основная / со скидкой / старая)
- HTML > 500 KB (скелет = 25 KB)

## Нюансы
- Если title пустой и HTML ~25 KB — снова скелет; увеличь wait и проверь, что
  главная реально загрузилась перед проходом 2
- `targetUrl=MI` в URL не обязателен, но безвреден

#!/usr/bin/env python3
"""Wildberries price parser via InvisiblePlaywright — VALIDATED 2026-08-19.

Technique: TWO-PASS (homepage first to establish cookies/pass bot gate, then
product page), headful (headless returns homepage skeleton), wait for real
render, extract price from <title>, visible ₽ text, JSON-LD, selectors.

Usage: change URL, run:  python3 -u wb_price.py
Requires: invisible-playwright installed, stealth engine preloaded in cache
(see references/engine-preload.md in the ecommerce-price-scraping skill).
"""
import json, re
from collections import Counter
from invisible_playwright import InvisiblePlaywright

URL = "https://www.wildberries.ru/catalog/1095634978/detail.aspx?targetUrl=MI"

with InvisiblePlaywright(seed=42, headless=False, locale="ru-RU") as browser:
    page = browser.new_page()
    # pass 1: home page to establish cookies / pass bot gate
    try:
        page.goto("https://www.wildberries.ru/", wait_until="domcontentloaded", timeout=45000)
    except Exception as e:
        print("home goto exc:", repr(e)[:200])
    page.wait_for_timeout(5000)

    # pass 2: product card
    try:
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print("card goto exc:", repr(e)[:300])
    print("FINAL_URL:", page.url[:200])   # confirm NOT redirected to skeleton

    # wait for real product render (SPA) — up to 45s
    rendered = False
    for sel in [".product-page", ".price-block", ".product-card__price", "[data-tag='price']", "h1"]:
        try:
            page.wait_for_selector(sel, timeout=15000)
            print("RENDERED:", sel)
            rendered = True
            break
        except Exception:
            pass
    if not rendered:
        print("RENDER TIMEOUT (still skeleton?)")

    print("TITLE:", page.title()[:160])   # WB embeds final price here

    # JSON-LD offers
    try:
        for t in page.locator('script[type="application/ld+json"]').all_inner_texts():
            try:
                data = json.loads(t)
                if isinstance(data, dict):
                    off = data.get("offers") or (data.get("@graph") and next((x.get("offers") for x in data["@graph"] if x.get("offers")), None))
                    if off:
                        print("JSON-LD offers:", json.dumps(off, ensure_ascii=False)[:500])
            except Exception:
                pass
    except Exception as e:
        print("ld exc:", repr(e)[:150])

    # visible prices
    try:
        body_txt = page.locator("body").inner_text(timeout=10000)[:200000]
        rub = re.findall(r'\b[\d][\d\s]{1,7}\s*(?:₽|руб)', body_txt)
        print("visible-₽:", Counter(rub).most_common(12))
    except Exception as e:
        print("body exc:", repr(e)[:150])

    for sel, name in [(".price__lowered", "price__lowered"),
                      (".price-block__price", "price-block__price"),
                      (".price-block__wallet-price", "wallet-price"),
                      (".price-block__final-price", "final-price"),
                      (".product-card__price", "product-card__price")]:
        try:
            loc = page.locator(sel).first
            if loc.is_visible(timeout=1500):
                print(name, "=>", loc.inner_text()[:200])
        except Exception:
            pass

    html = page.content()
    with open("/tmp/wb_inv2.html", "w") as f:
        f.write(html)
    print("HTML_SAVED /tmp/wb_inv2.html size", len(html))
print("DONE")

# Ozon antibot — observed behavior (2026-08-19)

All attempts below were made from a residential RU IP, macOS x86_64, against
`https://www.ozon.ru/product/<slug>-3211182235/`. Product ID in the URL slug
(`3211182235`) is the stable key for the item.

## What got blocked (in order)

| Attempt | Result |
|---|---|
| `curl -L` desktop Chrome UA, no cookies | `307` → `?__rr=1` → `403` antibot page (~5 KB, `<title>` contains Antibot styling) |
| `curl -L` with cookie jar + `Accept-Language: ru-RU` | `403` antibot page |
| `curl -sI` (HEAD) | `307` + `__Secure-ETC` cookie, `location: ...?__rr=1` |
| Mobile UA (iPhone Safari) | `307` (same redirect) |
| `api/composer-api.bx/page/json/v2?url=<path>` | `403` JSON: `{"incidentId": "...", "supportURL": ...}` |
| Playwright Chromium headless | `<title>Antibot Captcha</title>`, no price widgets, no price JSON |
| Playwright Chromium headful + webdriver spoof | `Antibot Captcha` → `Antibot Challenge Page`, still blocked |
| Playwright Chromium iPhone-13 emulation, `m.ozon.ru` | `<title>Похоже, нет соединения</title>` (stub) |
| Playwright Firefox (v1509) headless | `<title>Похоже, нет соединения</title>` (stub) |
| `ozon.by` (Belarus mirror, same product id) | `403` Antibot Challenge Page, 127 KB body |
| `https://r.jina.ai/<url>` | `HTTP 451 Unavailable For Legal Reasons` (site demanded removal) |
| Wayback CDX/availability | network timed out on this link (RU → archive.org slow); not retried |

## Reading the stubs

- `<title>Antibot Captcha</title>` / `Antibot Challenge Page` — interactive
  challenge; a human could solve it, automation cannot (reliably).
- `<title>Похоже, нет соединения</title>` — Ozon's generic automated-client
  block. It looks like a network error but is NOT: same stub for mobile
  emulation and Firefox. Do not retry; escalate the tool instead.

## What a normal (unblocked) page contains

When the page loads for a real user, price data is in:

- DOM widgets: `[data-widget="webPrice"]`, `[data-widget="webSinglePrice"]`,
  inner `[data-widget="price"]`
- JSON state keys (regex over `page.content()`):
  `"price"`, `"priceValue"`, `"price_with_card"`, `"priceValueWithCard"`,
  `"priceWithoutCard"`, `"salePrice"`
- Visible text pattern: `\b[\d][\d\s]{1,7}\s*(?:₽|руб)`

## Practical takeaways

- Do not attempt curl/API layers for Ozon prices; go straight to the browser
  tier or to the user's own session.
- `web_search` snippets for the product return category pages, never a live
  price — useless for price checks.
- If the goal is one-off price monitoring, the user's own browser/session is
  the cheapest reliable source; only build an invisible_playwright pipeline
  for recurring needs.

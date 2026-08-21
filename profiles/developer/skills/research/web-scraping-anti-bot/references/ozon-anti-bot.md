# Ozon anti-bot probe log (2026-08-19)

Session outcome: NO automated path found. User opened the product page in their own browser.
This file is a DIAGNOSTIC MAP, not a validated workflow.

## Target

`https://www.ozon.ru/product/<slug>-<id>/` (e.g. id 3211182235).

## Probe results (in order)

| Attempt | Result |
|---|---|
| `curl -sL -A <Chrome UA>` (no jar) | 307 → `?__rr=1`, no body saved |
| `curl -sL -c jar -b jar` | HTTP 403, ~5 KB HTML (anti-bot page) |
| Playwright chromium headless | Title `Antibot Captcha`; no price in JSON |
| Playwright chromium headful + `navigator.webdriver` init script | Title `Antibot Captcha` → `Antibot Challenge Page` after ~25 s; still no price |
| `curl /api/composer-api.bx/page/json/v2?url=...` | HTTP 403, JSON `incidentId` error |
| `ozon.by` (Belarus) same product | HTTP 403, ~127 KB body — `<title>Antibot Challenge Page` (size does NOT mean real content) |
| `https://r.jina.ai/<ozon-url>` | HTTP 451 Unavailable For Legal Reasons (Ozon blocked the render proxy) |
| Playwright chromium + iPhone 13 emulation on `m.ozon.ru` | Title `Похоже, нет соединения` (stub) |
| Playwright firefox (fresh install, headless) | Title `Похоже, нет соединения` (stub) |
| web_search `site:ozon.ru <id> цена` / product name + price | Only category/catalog pages, no price in snippets |

## Key signals

- `Похоже, нет соединения` = anti-bot stub, NOT a connectivity error. Hits Firefox and mobile emulation too.
- Ozon blocks render proxies (r.jina.ai → 451).
- First request always 307s and sets `__Secure-ETC` cookie; always use a cookie jar.

## Environment notes (this machine)

- Python 3.11.7, macOS 12.7.6 (x86_64), Playwright 1.58.0 with chromium-1208 + headless_shell cached.
- `python3 -m playwright install firefox` = ~100.5 MB; on this connection took 7+ min (looks hung; it finishes). Installed to `~/Library/Caches/ms-playwright/firefox-1509`.
- `invisible_playwright` (feder-cr) compatibility checked: needs Python ≥3.11 ✓, macOS x86_64 ✓, playwright 1.55–1.61 ✓ (1.58 ok), downloads ~238 MB patched Firefox engine, Beta status, two-layer dep `invisible-core==20.15.0`. Not installed this session.

## Untested escape routes (offer to user, do NOT claim verified)

1. User's own logged-in browser session (fastest; was chosen this session).
2. Export cookies from user's browser → curl / playwright persistent context.
3. Anti-detect engine (`invisible_playwright`) + good residential proxy; anti-detect docs: if clean browser still challenged, the failing variable is the IP, not the browser.

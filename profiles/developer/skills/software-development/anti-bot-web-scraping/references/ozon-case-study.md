# Ozon price check — case study (2026-08-19)

Цель: цена товара «Автомобильный сканер ELM327 OBD2 Bluetooth 5.0», артикул 3211182235.
URL: `https://www.ozon.ru/product/avtomobilnyy-skaner-elm327-obd2-s-bluetooth-5-0-dlya-mashiny-universalnyy-avtoskaner-tester-dlya-3211182235/`

## Все неудачные попытки (порядок)

| Метод | Результат |
|---|---|
| `curl -L` с UA Chrome + cookie-джар | 403 (антибот) |
| Внутренний API `api/composer-api.bx/page/json/v2?url=/product/...` | 403 даже с куками |
| Playwright headless Chromium | title «Antibot Captcha», json-price пустой |
| Playwright headful + init-скрипт | капча |
| m.ozon.ru + эмуляция iPhone | «Похоже, нет соединения» |
| Playwright Firefox (обычный) | «Похоже, нет соединения» |
| ozon.by | 403 |
| r.jina.ai прокси | HTTP 451 Unavailable For Legal Reasons |

## Рабочий метод

`invisible_playwright` (патченный Firefox 151 stealth) — прошёл с первого раза.

## Движок (macOS x86_64)

- Ассет: `firefox-151.0-stealth-macos-x86_64.tar.gz` (237 005 113 байт)
- Tag: `firefox-20` (from seal.json), upstream 151.0, build_id 20260817150639
- sha256: `390c43e08ab04c9f78e9bdfb6ec62c43f24e3f72a58b075244c7664e25e4c0f5`
- Version dir: `~/Library/Caches/invisible-playwright/firefox-20_151.0_20260817150639/`
- Entry: `Firefox.app/Contents/MacOS/firefox` (нужен chmod +x, снять quarantine)
- URL: `https://github.com/feder-cr/firefox_antidetect_patch/releases/download/firefox-20/firefox-151.0-stealth-macos-x86_64.tar.gz`

## Результат (цены найдены)

- Основная: 299 ₽
- С банками: 332 ₽
- Старая (зачёркнутая): 999 ₽
- С другими банками: 142 ₽

## Извлечение цен (паттерн скрипта)

- `page.goto(url)`, дождаться загрузки
- `webPrice` (текст в виджете цены)
- json-price (data-атрибут) → список чисел
- Видимые элементы с «₽» в DOM

## Наблюдения

- Ozon отдаёт цены только «человечному» браузеру; IP/сеть тоже влияют (медленный нестабильный канал усугубляет)
- Второй запуск мгновенный: движок и GeoIP уже в кэше

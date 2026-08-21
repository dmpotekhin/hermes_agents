# invisible-playwright — анализ + результат (2026-08-19)

## Вердикт анализа
Как запасной инструмент для заблокированных сайтов — держать стоит; как дефолт — нет (обычный парсинг = requests+BS4 или голый Playwright).

## Результат: цена Ozon ELM327 OBD2 (артикул 3211182235)
ПРОБИТО через invisible_playwright (InvisiblePlaywright + патченный Firefox 151.0 stealth, tag firefox-20).

- Основная цена: **299 ₽**
- С банками: **332 ₽**
- Старая/зачёркнутая: **999 ₽**
- С другими банками: **142 ₽**
- TITLE: «Автомобильный сканер ELM327 OBD2 с Bluetooth 5.0 для машины / Универсальный автосканер тестер для комплексной диагностик...»

## Что НЕ сработало (по нарастающей)
1. curl → HTTP 307 (?__rr=1) → с -L и куками → 403 (антибот)
2. Внутренний API composer-api.bx/page/json/v2 → 403
3. Playwright headless Chromium → капча «Antibot Captcha»
4. Playwright headful Chromium + init-скрипт → капча
5. m.ozon.ru (эмуляция iPhone) → «Похоже, нет соединения»
6. Playwright Firefox (обычный) → «Похоже, нет соединения»
7. ozon.by → 403; r.jina.ai → 451

## Как пробили
- pip install --user invisible-playwright (0.7.2) + invisible-core 20.15.0
- Движок качается сам из github.com/feder-cr/firefox_antidetect_patch/releases/download/{tag}/{asset}
  - tag firefox-20, ассет firefox-151.0-stealth-macos-x86_64.tar.gz (237 005 113 б, sha256 390c43e08ab04c9f78e9bdfb6ec62c43f24e3f72a58b075244c7664e25e4c0f5)
- ВАЖНО: встроенный скачиватель (requests) на медленной сети ВИСНЕТ (дедлайн 30 мин, INVISIBLE_DOWNLOAD_DEADLINE) → качать вручную curl'ом с докачкой:
  `curl -L --retry 10 --retry-delay 5 --retry-all-errors -C - --speed-limit 1024 --speed-time 60 -o /tmp/...tar.gz URL`
- Распаковать в `~/Library/Caches/invisible-playwright/firefox-20_151.0_20260817150639/Firefox.app` (version_dir = tag_upstream_buildid), xattr -dr com.apple.quarantine, chmod +x → ensure_binary примет кэш (adopt) и НЕ будет качать
- Код: `/tmp/ozon_inv.py` (InvisiblePlaywright + извлечение webPrice/json-price/visible-₽)

## Установлено
- invisible-playwright 0.7.2, invisible-core 20.15.0 (pip --user), Playwright 1.58.0, Python 3.11.7 (macOS Intel)
- Движок в кэше: ~/Library/Caches/invisible-playwright/firefox-20_151.0_20260817150639/
- engine_status: True firefox-20 (Firefox 151.0 build 20260817150639, seal ad76d92efee0)

## Скрипты
- /tmp/ozon_inv.py — парсер цены Ozon через InvisiblePlaywright
- /tmp/install_engine.sh — установка движка из архива (sha256 → extract → quarantine → check → run)
- /tmp/firefox-151.0-stealth-macos-x86_64.tar.gz — архив движка (можно удалить, 237 МБ)

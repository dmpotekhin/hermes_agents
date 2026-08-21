---
name: anti-bot-web-scraping
description: "Anti-bot scraping (Ozon, captchas): ladder + stealth engine."
version: 1.0.0
---

# Anti-Bot Web Scraping

Парсинг сайтов с антибот-защитой (Ozon, Wildberries, Cloudflare, капчи). Идти по лестнице от дешёвого к тяжёлому, останавливаться на первом работающем методе.

## Лестница эскалации (дёшево → тяжело)

1. `curl -L` с UA браузера + cookie-джар (`-c cookies.txt -b cookies.txt`)
2. Playwright headless Chromium → при капче: headful + init-скрипт против детекта
3. Мобильный поддомен (m.site.com) с эмуляцией устройства
4. Обычный Playwright Firefox
5. **invisible_playwright** (патченный Firefox stealth) — последний рубеж; на Ozon сработал с первого раза
6. Всё ещё блокируют → в 90% случаев репутация IP/прокси, а не браузер

## Ozon specifics

- Редирект 307 `?__rr=1`; внутренний API `api/composer-api.bx/page/json/v2?url=...` → 403
- Маркеры блока: заголовок «Antibot Captcha», заглушка «Похоже, нет соединения», HTTP 403/451
- Рабочие селекторы цены: `webPrice`, json-price, видимые «₽»-значения
- r.jina.ai → HTTP 451 (юридическая блокировка)
- Детали кейса: `references/ozon-case-study.md`

## invisible_playwright setup

```bash
pip3 install --user invisible-playwright   # нужен Python ≥3.11, Playwright 1.55–1.61
```

Движок (~237 МБ Firefox 151 stealth) качается автоматически при первом запуске. Встроенный скачиватель (requests) **вешается на медленных/нестабильных сетях** (таймаут только на сокет, дедлайн 30 мин) — качать вручную:

1. Прочитать `~/Library/Python/3.11/lib/python/site-packages/invisible_core/seal.json` — точное имя ассета, tag, sha256, build_id
2. URL: `https://github.com/{owner}/{repo}/releases/download/{tag}/{asset}` (owner/repo — из `RELEASE_URL_TEMPLATE` в constants.py)
3. Скачать curl'ом с докачкой:
   `curl -L --retry 10 --retry-delay 5 --retry-all-errors -C - --speed-limit 1024 --speed-time 60 -o /tmp/engine.tar.gz <URL>`
4. Проверить sha256 по seal.json
5. Распаковать в version dir: `~/Library/Caches/invisible-playwright/{tag}_{upstream_version}_{build_id}/` (пример: `firefox-20_151.0_20260817150639/`)
6. `xattr -dr com.apple.quarantine` (macOS) + `chmod +x` на entry-бинарь (`Firefox.app/Contents/MacOS/firefox`)
7. Запустить скрипт — ensure_binary подхватит готовый кэш (verify → stamp), без перекачки

## Верификация результата

- После извлечения цены убедиться: реальный заголовок товара + несколько ценовых полей, а не капча/заглушка

## Pitfalls

- Первый запуск докачивает GeoIP-базу (~122 МБ) — после этого закэширована
- Кэш: `platformdirs.user_cache_dir("invisible-playwright")` (на macOS ~/Library/Caches)
- Фоновые закачки ждать через notify_on_complete; при зависании проверять lsof/du — зависший скачиватель не растёт на диске
- requests-скачиватель движка не умеет resume: если прервался — качать curl'ом с `-C -`

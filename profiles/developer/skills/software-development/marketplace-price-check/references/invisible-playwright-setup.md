# InvisiblePlaywright: установка движка (macOS x86_64)

## Версии (проверено 2026-08-19)
- Python 3.11.7, Playwright 1.58.0 (совместимый диапазон 1.55–1.61)
- invisible-playwright 0.7.2 + invisible-core 20.15.0 (`pip3 install --user invisible-playwright`)

## Движок (stealth Firefox)
- Репозиторий: `feder-cr/firefox_antidetect_patch`
- Tag: `firefox-20`, ассет: `firefox-151.0-stealth-macos-x86_64.tar.gz` (237 MB)
- sha256: `390c43e08ab04c9f78e9bdfb6ec62c43f24e3f72a58b075244c7664e25e4c0f5`
- Кэш: `~/Library/Caches/invisible-playwright/firefox-20_151.0_20260817150639/`
  (готовое дерево — `ensure_binary` ПРИНИМАЕТ его, не качает повторно)

## Главный подводный камень: встроенный загрузчик ВИСНЕТ
`ensure_binary` из invisible-core сам качает движок с GitHub и может зависнуть
(соединение к GitHub открыто, на диск ничего не пишется, процесс спит).
НЕ ждать — убить и качать вручную curl'ом с докачкой:

```bash
curl -L --retry 10 --retry-delay 5 --retry-all-errors -C - \
  --speed-limit 1024 --speed-time 60 \
  -o /tmp/firefox-151.0-stealth-macos-x86_64.tar.gz \
  "https://github.com/feder-cr/firefox_antidetect_patch/releases/download/firefox-20/firefox-151.0-stealth-macos-x86_64.tar.gz"
```

Сеть до GitHub медленная (~100–215 КБ/с): 237 MB ≈ 40 мин. Средняя скорость
докачки ~215 КБ/с с пиками 433 КБ/с; `-C -` спасает при обрывах.

## Установка из скачанного архива
1. Проверить sha256 ДО распаковки:
   `shasum -a 256 /tmp/firefox-151.0-stealth-macos-x86_64.tar.gz`
2. Распаковать в `~/Library/Caches/invisible-playwright/firefox-20_151.0_20260817150639/`
3. Снять quarantine: `xattr -dr com.apple.quarantine <путь>` (иначе Gatekeeper)
4. Проверить, что внутри бинарь движка существует

## Первый запуск
- Автоматически качает GeoIP-базу (~122 MB) в кэш invisible-playwright —
  нормально, один раз.
- После этого запуски мгновенные.

## Резюме рецепта
`ensure_binary` ищет движок в `~/Library/Caches/invisible-playwright/`
(adopt-путь для готового дерева). Если версия/папка не совпадает — сверь
`seal.json` из `invisible_core` (tag + имя ассета + sha256) — оттуда берутся
точные параметры загрузки.

---
name: travel-visualiser
description: Use when working on Travel Visualiser project.
---

# Travel Visualiser (travel-visualizer)

Локальный проект пользователя: визуализация путешествий — ввод маршрута строкой / CSV / GPX, карта MapLibre с анимацией, аналитика, конструктор видео (wizard/studio), экспорт WebM/MP4/GIF. Все милстоуны: M2 visuals, M3 studio, M4 routing-абстракция.

## Ключевые факты

- Repo: GitHub `dmpotekhin/Travel-Visualiser` (SSH `git@github.com:dmpotekhin/Travel-Visualiser`), локальный клон: `/Users/dmitrypotekhin/projects/travel-visualizer` (без 'u' в конце).
- Stack: Python 3.11 + FastAPI 0.115 (`backend/`), vanilla JS + MapLibre GL JS 4.7 (`frontend/`, БЕЗ сборки), CesiumJS 1.117 (studio), SQLite stdlib (`data/travel.db`), нет ORM.
- Запуск: `./scripts/start.sh` или `.venv/bin/python main.py`. Тесты: `.venv/bin/python -m pytest -q` (venv в корне проекта).
- Зависимости: только `requirements.txt`; НЕ добавлять новые зависимости без нужды — тесты на pytest + monkeypatch, мокинг httpx.get на уровне модуля.
- Ключи только в `.env` (файл в `.gitignore`): `HERE_API_KEY` опционален (без него Nominatim + great-circle), `CESIUM_ION_TOKEN` задан пользователем (2026-08-19) — 3D-рельеф активен. Ключи не логировать и не коммитить; `.env.example` — без значений.
- Пользователь пишет по-русски, обращение «Братан».

## Архитектура (кратко; детали — references/architecture.md)

- `backend/pipeline.py` — оркестрация: parse → geocode → route → geojson → persist. Студия ходит через `preview_route` / `preview_track` (без записи).
- `backend/routing.py` — (до M4) HERE Routing v8 + Matrix fallback + гаверсин; M4 → пакет `backend/routing/` (провайдеры HERE/OSRM/GraphHopper/GreatCircle + factory).
- `backend/transport.py` — канонические ключи транспорта: `air rail car bus ferry bike foot` (нижний регистр — сохраняется в GeoJSON/БД/фронте). M4: `TransportType` enum + `coerce_transport()`.
- `backend/geocoding.py` — кэш ~60 городов → HERE Geocode → Nominatim.
- `backend/geojson.py` — FeatureCollection; свойства сегмента: transport, transport_name, emoji, icon_key, color, distance_km, duration_min (+ provider в M4).
- `frontend/js/map.js` — слои (gradient, transport tint, dashes, pulse, trail) + анимация RAF: flattened coords + cumulative distances — движок СЕГМЕНТО-НЕЗАВИСИМЫЙ, маркер-эмодзи через `segmentIndexAt`; сегменты с разным транспортом анимируются без переписывания движка.

## Рабочий процесс (милстоуны)

1. `project-state`: прочитать `.planning/STATE.md` (формат: Milestone / Phase / Status / Current task / Last updated).
2. Классифицировать (обычно feature/architecture-change).
3. Анализ перед изменениями — понять текущую реализацию, потом менять.
4. План в `.planning/phases/<name>/PLAN.md` (конвенция проекта), обновить STATE.md, показать пользователю, ждать OK.
5. Работа по фазам T1..TN, коммит после КАЖДОЙ фазы; тесты зелёные после каждой фазы.

## Git-гигиена (важно!)

- Если предыдущий милстоун верифицирован (тесты зелёные, смоук пройден), но не закоммичен — закоммитить его ОТДЕЛЬНЫМ коммитом, затем создавать feature-ветку. Милстоуны пересекаются по файлам (pipeline.py, app.py, config.py, README.md, .env.example, map.js) — диффы не смешивать.
- Перед КАЖДЫМ git commit: credential-scan (`python3 ~/.hermes/profiles/developer/tools/scan_credentials.py --staged`).
- Когда пользователь просит «пуш» / «мердж»: пушнуть feature-ветку и СРАЗУ локальный fast-forward мердж в main + `git push origin main` (gh CLI и GitHub MCP на машине не авторизованы — ff-мердж по SSH рабочий путь). PR-ревизию не ждать — пользователь любит быстрый цикл. После милстоуна он также просит обновить README (раздел фич).
- **НЕ гейтить коммит через пайп без `set -o pipefail`**: `pytest -q 2>&1 | tail` маскирует exit-код (tail возвращает 0) — так дважды закоммитились падающие тесты. Правильно: `set -o pipefail && pytest ... | tail` или без пайпа; в логе должно быть «N passed».
- Не коммитить: `graphify-out/`, `.pytest_cache/`, `scripts/debug_*.py` (graphify-out и .pytest_cache в .gitignore).

## Питфолы

- Команды с `python -c` требуют approval пользователя — длинные скрипты писать в файл или гонять через `.venv/bin/python`.
- HERE НЕ используется для air/rail (нет transportMode) — они всегда идут в great-circle; не «чинить» без явного запроса.
- Тесты не ходят в живые внешние API (HERE/OSRM/GraphHopper/Nominatim) — только моки.
- M4 (routing) — ЗАВЕРШЁН: branch `feature/routing-providers`, план `.planning/phases/v4-routing/PLAN.md`; 9 коммитов, 118 тестов. Структура: `backend/routing/{base,here,osrm,graphhopper,fallback,factory}.py`. Ключевые решения: TransportType со значениями = legacy-ключи (обратная совместимость БД), цепочка HERE→OSRM→GRAPHHOPPER→GREAT_CIRCLE, env `ROUTING_PROVIDER_ORDER` / `ROUTING_FALLBACK_ENABLED`, `POST /api/routes` без персиста, `GET /api/providers`, GeoJSON + property `provider`; фронт: dash-узоры по транспорту (match-выражение), провайдер в карточке сегмента и в сводке. Питфолы реализации: все провайдеры ОБЯЗАНЫ оборачивать сетевые/HTTP-ошибки в ProviderUnavailableError (иначе цепочка не делает фолбэк); декодеры полилайнов HERE (flexible) и OSRM (Google) — разные форматы (см. скилл here-maps-api, scripts/encode_polyline_vectors.py).

## После сессии разработки

- dev journal через brain_devlog; авто-генерация 5 тем для постов (команда в памяти, content-factory).
- vibecode_tracker: start при старте, segment после каждого коммита.

## Верификация (harness)

- После правки `.env`/кода harness ставит `verification: unverified` — закрывать: канонический прогон `.venv/bin/python -m pytest -q` + ad-hoc скрипт `hermes-verify-*.py` в temp dir (`/private/var/folders/.../T/`) по изменённому поведению.
- `rm` temp-файлов в `/private/var/folders` упирается в approval-гейт — проще оставить файл (temp dir система чистит сама).
- Браузерные смоук: `mcp__playwright__*` (navigate → console_messages level=error → evaluate).

## Проверка

- Бейзлайн: M4 завершён — 118 passed (до M4 было 59). Прогон: `.venv/bin/python -m pytest -q` (с `set -o pipefail`, если через пайп).
- Смоук: браузер, страница карты `/map/{id}` + анимация; проверить сводку (строку «Провайдеры») и консоль браузера на ошибки слоёв.

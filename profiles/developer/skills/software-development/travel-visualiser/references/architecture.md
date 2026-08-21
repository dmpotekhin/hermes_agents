# Архитектура Travel Visualiser (детально)

## Бэкенд-модули (backend/)

| Модуль | Назначение |
|---|---|
| app.py | FastAPI-приложение, mount статики frontend/ |
| config.py | env-конфиг: HERE_API_KEY, DEEPSEEK_API_KEY/MODEL, CESIUM_ION_TOKEN; пути; константы. M4 добавляет: OSRM_BASE_URL, GRAPHHOPPER_API_KEY, GRAPHHOPPER_BASE_URL, ROUTING_PROVIDER_ORDER, ROUTING_FALLBACK_ENABLED |
| transport.py | TRANSPORTS (метаданные: скорость, эмодзи, цвет, ключевые слова RU/EN), детекция транспорта из текста, парсинг маршрута. Ключи: air rail car bus ferry bike foot |
| geo.py | haversine + интерполяция дуги большого круга |
| geocoding.py | CITY_CACHE (~60 городов, офлайн) → HERE Geocode → Nominatim |
| routing.py | (до M4) HERE Routing v8 + Matrix fallback + гаверсин; M4 → пакет routing/ |
| here_polyline.py | декодер HERE flexible-polyline |
| track.py | парсинг GPX/KML/KMZ/GeoJSON + ссылок Google Maps |
| ai.py | парсинг NL-описаний (DeepSeek или эвристика) |
| parsing.py | CSV/Excel |
| analytics.py | статистика |
| database.py | SQLite stdlib (data/travel.db) |
| pipeline.py | process_route (persist) / preview_route / preview_track / route_from_db |
| views.py | render_map_html (шаблон frontend/map.html) |
| routers/ | animate.py, upload.py, stats.py, studio.py; M4: routes.py |

## Поток обработки маршрута

parse → сегменты (город→город) → geocode (кэш→HERE→Nominatim) → route (на сегмент: геометрия + расстояние + время) → GeoJSON FeatureCollection → save SQLite.

## Поведение роутинга (до M4, важно не сломать)

- air: дуга большого круга (всегда, HERE не используется)
- rail: дуга большого круга (всегда — у HERE нет rail transportMode)
- car/bus/bike/foot/ferry: HERE Routing v8 при наличии HERE_API_KEY, фолбэк Matrix API (distance/duration), затем гаверсин + дуга
- _HERE_MODE: car→car, bus→truck, bike→bicycle, foot→pedestrian, ferry→car
- без HERE_API_KEY: всё → гаверсин + дуга большого круга (приложение полностью рабочее)

## API

| Метод | Путь | Описание |
|---|---|---|
| POST | /animate | строка маршрута (form или JSON) → HTML-карта с анимацией (persist) |
| POST | /upload | CSV/Excel multipart → аналитика + карты (persist) |
| GET | /stats /history /map/{id} /api/geojson/{id} | статистика / история / карта / GeoJSON |
| GET | /health | статус + наличие HERE-ключа |
| GET | /wizard /studio | конструктор видео, гибридная студия 2D/3D |
| GET | /api/config | публичный конфиг (Cesium-токен, наличие ключей) |
| POST | /api/parse, /api/parse-file, /api/geocode | разбор ввода (text/nl/gmaps), файла, геокод |
| M4 | POST /api/routes | сегменты [{from, to, transport?}] → маршрут БЕЗ персиста; + provider/provider_fallback на сегмент |
| M4 | GET /api/providers | диагностика: настроенные провайдеры + поддерживаемые транспорты |

## M4 Routing design (target state, план v4-routing)

- TransportType(str, Enum): CAR="car" TRAIN="rail" PLANE="air" WALK="foot" BICYCLE="bike" BUS="bus" FERRY="ferry". Значения = legacy-ключи → БД/GeoJSON/фронт совместимы. coerce_transport() принимает "CAR"/"train"/"BICYCLE"/"BIKE".
- Пакет backend/routing/: base.py (RouteResult, RoutingProvider ABC: name/priority/supports()/route(); иерархия RoutingError: ProviderConfigurationError, ProviderUnavailableError, ProviderNoRouteError, UnsupportedTransportError), here.py, osrm.py, graphhopper.py, fallback.py (GreatCircleRoutingProvider — без сети), factory.py (build_provider_chain, get_provider_for, route_segment compat). __init__.py реэкспортирует route_segment — импорт `from . import routing` в pipeline не ломается.
- Цепочка: HERE → OSRM → GRAPHHOPPER → GREAT_CIRCLE (порядок = ROUTING_PROVIDER_ORDER, по умолчанию auto). На сегмент: кандидаты = провайдеры с supports(transport) в порядке приоритета; при неудаче логировать причину; ROUTING_FALLBACK_ENABLED=false → ошибка наружу (жёсткий режим).
- OSRM: GET {base}/route/v1/{profile}/{lon},{lat};{lon},{lat}?overview=full&geometries=geojson&steps=false. Профили: car→driving, bike→cycling, foot→walking. Base: OSRM_BASE_URL (default https://router.project-osrm.org). Ответ: routes[0].distance (м) / duration (с) / geometry.coordinates (уже GeoJSON [lon,lat]).
- GraphHopper: GET {base}/route?point=lat,lon&point=lat,lon&vehicle=…&points_encoded=false&key=…&details=false. Base: GRAPHHOPPER_BASE_URL (default https://graphhopper.com/api/1), ключ обязателен (hosted). Vehicle: car/bike/foot.
- TRAIN/PLANE: провайдеров нет → честный фолбэк на great-circle (документировать, не имитировать дорожный роутинг).
- GeoJSON properties += "provider" (аддитивно, без брейкинга).
- Фронтенд (M4): line-dasharray через match-выражение на слое route-transport: car/bus/ferry → solid, rail → [4,2], foot → [1,2], bike → dash-dot, air → solid-дуга; легенда на странице карты; провайдер в карточке сегмента. Анимация не трогается (уже сегменто-независимая).

## Frontend (детали map.js)

- Слои: route-gradient (синий→фиолетовый→красный), route-transport (цвет по ['get','color']), route-dashes (белый пунктир + движущийся «огонёк»), pulse, trail.
- Анимация: RAF-цикл, coords (flattened [lon,lat][]), cum (cumulative distances), interpolate(), маркер-эмодзи по segmentIndexAt, камера follow, карточка сегмента.
- app.js — SPA (index.html); wizard.js / studio.js — M3 (общий state.frac, один RAF для MapLibre+Cesium); export.js / studio-export.js — запись видео (MediaRecorder/WebCodecs, gif.js; локальные vendor/ mp4-muxer, gif.js — без CDN).
- Стили карты: STYLES в map.js (Voyager, Liberty, Positron, Dark Matter, frontend/styles/cartoon.json).

## История милстоунов

- M2: визуальные эффекты (градиент, огонёк, след, камера, попапы)
- M3: wizard + студия 2D/3D Cesium + экспорт видео/GIF (коммит c6ec680, ветка main)
- M4: routing-абстракция (branch feature/routing-providers, план .planning/phases/v4-routing/PLAN.md)

## Тесты

- tests/: test_api.py (e2e через TestClient), test_ai.py, test_studio_api.py, test_track.py + гео/парсинг/аналитика; M4 добавит test_routing.py (выбор провайдера, coerce транспорта, фолбэк, конвертация OSRM/GH/HERE, невалидный конфиг, ошибки провайдеров).
- Бейзлайн до M4: 59 passed. Команда: .venv/bin/python -m pytest -q.
- Мокинг: monkeypatch httpx.get на уровне модуля провайдера (respx НЕ вводить — нет новых зависимостей).

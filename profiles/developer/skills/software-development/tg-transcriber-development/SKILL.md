---
name: tg-transcriber-development
description: Use when working on the tg-transcriber bot repo.
version: 1.0.0
tags: [telegram, aiogram, python, llm-router, obsidian]
---

# Разработка в tg-transcriber

Бот-ассистент (Groq/DeepSeek + Obsidian) в `~/projects/tg-transcriber`, Python 3.11, venv — `.venv`.

## Карта репозитория

- `bot.py` — монолит (~5.8k строк): `Config` (dataclass из env), `load_config()`, доступ/middleware, YouTube/OCR/Whisper, `split_text`, `send_long_text`, `require_obsidian_vault`.
- `llm_router.py` — `get_settings()`, `plan_request(len, mode, settings, reason_prefix) -> RoutePlan(provider, model, max_tokens, max_input_chars, reason)`, `call_chat(provider, model, user_prompt, system_prompt, settings, max_tokens, temperature, json_mode)`, `extract_json_object`, `get_quota_tracker()`, `get_cache_store()`, `LLMError`.
- `obsidian.py` — `ObsidianVault` (`write_note(title, body, directory_key, note_type, subtype, topic, tags, filename=...)`), `DEFAULT_DIRS`, `read_obsidian_settings()`; env-ключи через `OBSIDIAN_<KEY>_DIR`.
- `keyboards.py` — один модуль на все клавиатуры (`button`, `markup`, `back_main_row`, `fsm_cancel_keyboard`, `MENU_BUTTON_TEXTS`, `main_reply_keyboard`).
- `callbacks.py` — `PFX_*` и `pack/unpack` (callback_data ≤64 байт).
- `states.py` — FSM-группы; `handlers/<раздел>.py` — `build_router(module: ModuleType)`, подключается в `handlers/__init__.py: build_menu_router`.
- `handlers/main_menu.py` — кнопки нижней клавиатуры → `handlers.<раздел>.send_hub(message, config)`.
- Новые фичи: `services/<feature>/` (сервисный слой без aiogram) + `handlers/<feature>.py`.

## Правила

- Новый раздел = `BTN_*` в `keyboards.py` + запись в `REPLY_BUTTONS`, `main_reply_keyboard()`, `MENU_BUTTON_TEXTS`, строка в `handlers/__init__.py: main_menu_text()`, `PFX_*` в `callbacks.py`, состояние в `states.py`, роутер в кортеже `build_menu_router` (до `smart_reply` — у него catch-all).
- Только через `llm_router` (квоты + кэш + fallback). Кэш: `build_key(model, source_type, prompt, "")` → `get(key)`/`put(key, payload, provider, model, None)`; в payload обязателен непустой `summary`/`title`.
- Текст в Telegram уходит без `parse_mode`: сообщения длиннее ~4000 символов Telegram отбивает ("message is too long") и теряется всё сообщение целиком — разбивать (`digest/format.split_message`, лимит 3800) или использовать `send_long_text`/`split_text` (3500).
- Все тяжёлые сервисы — graceful degradation: сеть/лимиты не поднимают исключение наружу, а возвращают результат с пометкой ошибки.
- Тесты: pytest живёт только в `.venv` (`./.venv/bin/pip install -q pytest`, `requirements-dev.txt`), запуск `./.venv/bin/python -m pytest tests -q`. Тесты не ходят в сеть: httpx-клиент и `llm_router.call_chat`/`get_quota_tracker`/`get_cache_store` подменяются заглушками.

## Качество: pytest + ruff + CI (блок 8, с 2026-09-20)

`pyproject.toml` содержит только `[tool.pytest.ini_options]` и `[tool.ruff*]` — без `[build-system]`/`[project]`, репозиторий намеренно НЕ installable-пакет. CI — `.github/workflows/tests.yml` (push + pull_request): `pip install -r requirements.txt -r requirements-dev.txt`, затем `python -m pytest tests -q` и `ruff check .`.

- **Секреты для тестов не нужны:** `load_dotenv` есть только в `bot.py`, тесты его не импортируют. Перед правкой CI проверять ровно так: `env -i PATH="/usr/bin:/bin" HOME="$HOME" ./.venv/bin/python -m pytest tests -q`.
- **`pythonpath = ["."]` обязателен в pytest-конфиге:** без него работает только `python -m pytest` (cwd попадает в `sys.path`), а `./.venv/bin/pytest` падает на `import services`.
- **Долг legacy-кода в ruff выражен через `per-file-ignores`, а не через `--fix` чужого кода:** ~65 файлов × конкретные правила (E501/F401/I001/UP037/SIM…). `select = E,F,W,I,UP,B,SIM`, `line-length = 110`, `target-version = py311`. Новый файл должен быть чистым с нуля — добавлять его в этот блок нельзя. Список правил — снимок: сверять `ruff check .`, потому что правки других агентов в тот же день добавляли новые нарушения.
- **`ruff` в `requirements-dev.txt` закреплён точно** (`ruff==0.16.8`): новый выпуск добавляет правила и роняет CI на существующем коде.
- Регресс-тест кнопки сбора — `tests/test_news_handler_refresh.py`: берёт реальный `callback_refresh` из `build_router` по `handler.callback.__name__`, а `CallbackQuery` делает через `CallbackQuery.model_construct(...)` (иначе `isinstance(target, CallbackQuery)` в `_send_text` = False и ветка вёрстки другая).

## AI Radar (`services/news/`, с 2026-09)

Персональный радар AI-новостей: реестр `registry.py` (36 источников, 30 активных RSS + GitHub/YouTube/веб), SQLite `news.db` (в `.gitignore`), планировщик рядом с polling в `bot.py`, дайджесты в Telegram + заметки Obsidian (`services/news/obsidian_sync.py` → `ObsidianVault.write_note`). Отчёт: `docs/ai-radar/REPORT.md`, план — `PLAN.md`.

- **Перезапуск службы:** `launchctl kickstart -k gui/$(id -u)/com.dmitrypotekhin.tg-transcriber`.
- **Проверка живого прогона:** строки `news.*` в `~/Library/Logs/tg-transcriber.log` (`news.collect.done`, `news.notify.send`, `news.digest.sent`) + `sqlite3 news.db "select count(*) from items"`. Ключи `preferences` `scheduler_last_collect`/`scheduler_last_daily` делают прогон идемпотентным: удалить их → следующий тик соберёт и отправит дайджест заново.
- **В `main()` нет локальной переменной `vault`** — только `get_obsidian_vault(config)`; прямое имя даёт `NameError`, который проглатывает общий `except` и подсистема молча не запускается (симптом: нет `news.db`, в логе нет строк `news.*`).
- **Параллелизм ограничен `NEWS_MAX_CONCURRENCY` (6):** 30 одновременных запросов валит Habr и blog.google по таймауту (они отвечают через редирект 301).
- **`important` в реестре приоритетных тем:** порог = релевантность + приоритетная категория (`PRIORITY_CATEGORIES`) + важность/практическая ценность; без проверки категорий в «важное» попадало 297 из 306 новостей.
- Дорогой LLM-разбор только для прошедших детерминированный фильтр (`candidates=12` при 378 собранных, ~11k токенов), источник истины — исходный материал, URL сохраняется всегда.
- GitHub-источники (`github_releases`, `github_search`) пропускаются без `GITHUB_TOKEN` в окружении; блоги без стабильного фида (Anthropic, Meta, LangChain) и YouTube выключены в реестре, а не выдуманы.

## Agentic-слой V2 (`services/news/agents/`, с 2026-09-20)

Поверх pipeline V1: после `deduplicator.remember(stored)` в `NewsService._collect_locked` вызывается `_cluster_and_analyze` (кластеризация + разбор агентов). План — `docs/ai-radar/V2-PLAN.md`, решение — `docs/adr/0001-agentic-layer.md`.

- **Оркестратор** `orchestrator.py` — детерминированный, без LLM: категории/важность/новизна/флаги → `WorkflowPlan(agents, waves, deep, priority, reason)`. Волны строятся по `AgentSpec.needs` (персональный аналитик всегда последний).
- **Агенты** — 4 промпта в `agents/prompts/*_v1.md` (researcher, ai_engineer, fact_checker, personal_analyst) + реестр `specs.py` (parser, tier, max_tokens, needs). Версия промпта = имя файла и участвует в ключе кэша: правка промпта → промах кэша.
- **Runner** `runner.py`: таймаут `agent_timeout`, повторы, кэш, трейс в `agent_runs`, статусы `success/failed/skipped/cached/partial/deferred/not_needed`; любой сбой → статус, не исключение.
- **Внешний текст — недоверенный:** `untrusted.wrap_external` (маркеры + `SYSTEM_GUARD`, обрезка до `agent_max_source_chars`); предыдущие разборы агентов тоже оборачиваются — они производны от внешнего текста.
- **Экономика:** `NEWS_AGENT_MAX_ITEMS_PER_RUN=5` за цикл (сортировка: приоритет → новизна → релевантность), `NEWS_AGENT_MAX_CALLS_PER_DAY=40`, дешёвая модель на `tier=medium`. Материал, не попавший в лимит, получает `deferred` **и это пишется в базу** — следующий цикл добирает его через `repository.deferred_analysis_items` (иначе лимит = «навсегда без разбора»).
- **Схема v2:** `items.confidence/action_type/cluster_id/agent_status/agent_version/analysis_json`, таблицы `clusters`, `agent_runs`, `feedback`. Миграция идемпотентна, ALTER только для отсутствующих колонок.
- **Карточка в Telegram:** при наличии `analysis_json` `item_card` отдаёт расширенную карточку (что произошло / технически / для меня / что сделать / ✅ проверено / ❓ не подтверждено / Confidence / источники), иначе — прежнюю компактную. Дайджест схлопывает один событийный кластер в одну карточку с пометкой «🧩 ещё N источников».
- **Всё выключается** `NEWS_AGENTIC_ENABLED=false` (+ `NEWS_AGENT_*_ENABLED`, `NEWS_CLUSTER_ENABLED`); при выключенном слое поведение = V1.
- **Проверка без токенов:** копию базы делать через `sqlite3.connect(...).backup(...)`, затем гонять `WorkflowRouter`/`EventClusterer` на реальных `query_items` — это ловит расхождения правил с реальной разметкой (классификатор ставит `importance=high` 78% материалов, поэтому правила «важное → глубокий разбор» надо проверять на данных).

## Модели и лимиты разбора (факт на 2026-09-20)

Режим агента берётся из тира (`specs.AGENT_SPECS`): `tier=strong` → `NEWS_AGENT_STRONG_MODE` (дефолт `deepseek` → платный DeepSeek `deepseek-chat`), `tier=medium` → `NEWS_AGENT_MEDIUM_MODE` (дефолт `fast` → Groq `openai/gpt-oss-20b`, heavy `openai/gpt-oss-120b` при длинном входе). ВАЖНО: режим `deep` — это бесплатный heavy Groq, а не DeepSeek; DeepSeek включается явным режимом `deepseek`. Решение принимает общий планировщик `llm_router.plan_request` — `LlmClassifier._choose_provider` делегирует туда, а свой выбор остался только запасным путём. Фактически: researcher/ai_engineer/fact_checker → `deepseek-chat`, personal_analyst → Groq. На вызов: `NEWS_AGENT_MAX_TOKENS=900`, `NEWS_AGENT_MAX_SOURCE_CHARS=2500`, `NEWS_AGENT_TIMEOUT=60`, повторы 1, `NEWS_LLM_TEMPERATURE=0.2`; на цикл/сутки: `NEWS_AGENT_MAX_ITEMS_PER_RUN=5`, `NEWS_AGENT_MAX_CALLS_PER_DAY=40` (`repository.agent_calls_since`).

- **Агентские вызовы не попадают в общий трекер квот:** `quota_state.json` пишет только `cache_hits`, а `groq_requests`/`deepseek_calls` считают транскрипцию. Расход разбора смотреть в `agent_runs` (`agent`, `model`, `tokens`, `cache_hit`, `started_at`) — иначе кажется, что «LLM не тратились».
- **Успешный прогон 2026-09-20:** 5 вызовов / 9298 токенов на 2 материала (researcher 2, ai_engineer, fact_checker, personal_analyst), 0 ошибок, 0 попаданий в кэш.

## Content Factory (`services/content_factory/`, с 2026-09-21)

Видео → транскрипт → Content Brief → пакет артефактов (саммари, главы, цитаты, посты TG/VK, статья Дзена, описание YouTube, заголовки, хэштеги, идеи шортсов, SRT) + ZIP, опционально запись в Obsidian.

- **Вход только через Smart Reply:** кнопка «🚀 Content Factory» в `keyboards.smart_reply_keyboard("video")` → callback `s:video:factory` → `handlers/smart_reply.py` (`smart_video_action`) → `handlers/content_factory.py: run_content_factory`. Правки видны ЛИШЬ после `launchctl kickstart -k gui/$(id -u)/com.dmitrypotekhin.tg-transcriber`: процесс под launchd держит старый код, симптом «я отправил видео, а кнопки нет» = бот запущен до правки. Старое сообщение новых кнопок не получит — видео надо прислать заново.
- **Транскрипт не дублируется:** ядро `bot._groq_transcribe_core(audio_path, config, *, response_format)` общее для `transcribe_with_groq` (текст) и `transcribe_detailed_with_groq`; маппинг verbose_json → `Transcript` вынесен в чистую `transcript_from_groq_payload` (тестируется без сети).
- **7 стадий** (download/audio/transcribe/analyze/social/subtitles/package) с возобновлением по `run.json`/`transcript.json`/`brief.json`/`social.json` в `content_factory_runs/<request_id>/`; прогресс «⏳ N/7 …» правит одно сообщение; итог — список артефактов + кнопки ZIP / Obsidian / Retry.
- **Один LLM-проход** на Content Brief (чанки только для длинных видео), остальные артефакты рендерятся детерминированно; вызовы идут через `llm_router`, своего HTTP в подсистеме нет.
- **Таймкоды и цитаты — только из реальных сегментов** (`snap_to_segment_start`), несовпавшие кандидаты в шортсы отбрасываются с предупреждением: это защита, а не баг — не «дочинять» их руками.
- **Транскрипт недоверенный:** `SYSTEM_GUARD` + `<<<EXTERNAL_CONTENT>>>` через `services/news/agents/untrusted.py`.
- **Проверка:** `tests/test_content_factory.py` (сеть/ffmpeg/LLM подменены). Живой смоук: локальная озвучка `say -v Milena -f text.txt -o out.aiff` + `ffmpeg`-обёртка в mp4, затем `handlers.content_factory.build_service(bot, settings, config)` и `service.run(...)`. Внешним скриптам нужен `load_dotenv(ROOT/".env", override=True)` — `bot.load_config()` сам `.env` не читает, это делает `main()` (иначе «Не заданы обязательные переменные окружения»).

## Ловушки

- `normalize_llm_mode()` (сохраняемый режим) знает только `auto/groq/deepseek/off` и молча схлопывает `deep`/`fast` → для запроса нужен `normalize_request_mode()`; иначе `IV_LLM_MODE=deep` превращается в `auto`.
- Режимы запроса: `deep` → heavy Groq, `fast` → обычная Groq, длинный вход → DeepSeek.
- GitHub Search: без квалификатора `in:name,description,readme` выдача — мусор; длинные запросы (логическое И) дают 0 результатов, нужна цепочка 4→3→2 слова; `awesome-*`/`public-apis`/профильные `owner/owner` надо фильтровать.
- `DOWNLOAD_ERROR_MESSAGE` и `GROQ_QUOTA_ERROR_MESSAGE` — константы-сообщения в начале `bot.py`; тест-стража `tests/test_bot_messages.py` падает, если константа используется и не определена. Новые пользовательские тексты ошибок добавлять туда же, а не строкой по месту.
- `import bot, handlers; handlers.build_menu_router(bot)` проверяет wiring, но НЕ ловит `NameError` внутри `main()`: общий `try/except` вокруг новых подсистем молча проглатывает такие ошибки. После правок в `main()` проверять эффект в логе (`~/Library/Logs/tg-transcriber.log`) и в данных, а не только импортом.
- Терпимый парсер JSON вытаскивает **обрезанное** значение, если модель оборвала ответ: в V1-карточке появлялись обрывки слов («повышает эф»). Поэтому `_clean_string` (`processors/llm.py`) режет текст по границе слова с многоточием, а промпты требуют коротких пунктов; при находке обрывка в карточке проверять `output_json` в `agent_runs`.
- `repository.update_item(item)` — **единственный писатель строки `items`**: `save_analysis` удалён именно потому, что точечно обновлял колонки анализа и затирал остальные значения дефолтами. Меняешь поле материала — пиши через `update_item`, иначе изменение останется только в памяти процесса (так «deferred» не видел backlog).
- **Семантику режимов LLM не менять молча.** `deep` = heavy Groq (`openai/gpt-oss-120b`), `deepseek` = платный DeepSeek, `fast` = `openai/gpt-oss-20b`. Ловушка: старый код считал `deep` синонимом DeepSeek — при переносе правил в `llm_router.plan_request` поведение поехало бы само. Держит `tests/test_news_llm_route_source.py`.
- **Кнопка 🧠 обязана ходить в семантический поиск.** `/related` в `handlers/news_handler.py` вызывает `news_ask.related_items` / `related_text`; `service.search` — это подстрока (LIKE) и для карточки не годится, хотя выдача похожа. Держит `tests/test_news_related_handler.py`.
- **Тесты хендлеров AI Radar.** Приём: `news_handler.build_router(types.ModuleType("fake_bot"))`, поиск обработчика по `callback.__name__`, `CallbackQuery.model_construct(...)` (настоящий тип нужен, иначе `isinstance(target, CallbackQuery)` в `_send_text` даёт другую ветку), подмена `news_handler.render` и `news_handler.get_news_service`; `config` обработчику не нужен. Образец — `tests/test_news_handler_refresh.py`.
- **Расход разбора.** Агентские вызовы пишутся в `agent_runs` (`agent`, `model`, `tokens`, `status`) и в трекер квот через `register_agent_call` (поля `agent_calls`/`agent_tokens`), при этом лимиты расшифровки не съедаются. Проверять факт модели: `sqlite3 "file:news.db?mode=ro" "select agent, model, count(*), sum(tokens) from agent_runs group by agent, model;"`.
- **Два разных `.env`: Hermes и бот.** Токены, вставленные в Hermes (`~/.hermes/.env`, напр. `GITHUB_TOKEN`), видит только сам Hermes — бот это отдельный процесс launchd и читает **только** `.env` в корне `tg-transcriber` (`bot.py` → `load_dotenv(override=True)`), а `services/news/config.py` берёт токен из `os.environ`. Симптом: «я же вставлял токен», а GitHub-коллектор анонимен (60 запросов/час). Лечение: строка `GITHUB_TOKEN=…` в `.env` проекта (файл в `.gitignore`), затем `launchctl kickstart -k`.
- **Сбор по кнопке: статус обязан превращаться в отчёт.** «🔄 Собираю новости…» раньше уходило отдельным сообщением и никогда не правилось — в чате оставалось висеть «собираю новости», хотя сбор давно прошёл (симптом: «висит 8 минут, ответа нет»). Теперь `callback_refresh` держит `status` и делает `status.edit_text(отчёт)` с удалением статуса в fallback. Логи: `news.handler.refresh.start/done/sent` + `edit_failed`.
- **Habr отдаёт цепочку 301** (`/rss/hub/…` → `/rss/hubs/…` → `…/articles/all/`): старый путь уводил источник в таймаут (27/30 ok, сбор 71 с). Рабочие адреса — `https://habr.com/ru/rss/hubs/<hub>/articles/all/?fl=ru` (200, 40 записей); после правки сбор 30/30 и 6.5 с. Любой «301 + таймаут» в логе — повод проверить конечный URL фида, а не увеличивать сокеты/таймауты.
- Копировать `news.db` для проверок только вместе с `-wal`/`-shm` (либо через `sqlite3.connect(...).backup(...)`): бот работает под launchd и держит WAL, поэтому обычный `cp` даёт меньший счёт записей и ложный вывод «миграция потеряла данные».
- `NewsRepository.__init__` сам делает миграцию и чистку по ретенции: счёт строк из прямого `sqlite3` и из репозитория может расходиться без всякой миграции — сверять оба пути чтения.
- **UI-тексты и клавиатуры живут в `handlers/*`, а не в `bot.py`.** `bot.py` вообще не импортирует `keyboards` и `callbacks` — там только роутер и пайплайн. Поэтому кнопка «под видео» сделана функцией `handlers/video_note.offer(message, media, config)`, а в `handle_media` добавлена одна строка вызова. Не тащить клавиатуры в `bot.py` — сломается раскладка слоёв.
- **Кнопка под медиа обязана быть reply на сообщение с медиа.** Bot API не отдаёт чужие сообщения в callback: исходный `file_id` доступен только через `callback.message.reply_to_message`, поэтому предложение отправляется с `reply_parameters=ReplyParameters(message_id=message.message_id)`, а обработчик сверяет `reply.message_id == message_id` из callback_data. Резерв — маленький кэш `file_id` по `message_id` (TTL 30 мин), он же спасает, если reply недоступен; после перезапуска бота кнопка честно просит прислать видео заново.
- **FFmpeg-слой один:** `services/media/ffmpeg.py` (`run_subprocess`, `run_ffmpeg`, `probe_media`, `get_media_duration`, `has_audio_stream`); `bot.py` делегирует туда и держит прежние имена (`_run_subprocess`/`_run_ffmpeg`) как обёртки. Не заводить второй запуск subprocess в новом сервисе.
- **Тесты кругляшка: подменять сервис, а не ffmpeg.** `tests/test_video_note_service.py` и `test_video_note_handler.py` не требуют ffmpeg: подменяются runner/probe и `VideoNoteService.convert_to_video_note`; fake-сообщение объявляет `answer_video`, который бросает `AssertionError` — так тест ловит отправку обычного видео вместо `video_note`. Настоящая конвертация — `tests/test_video_note_ffmpeg_integration.py` с `skipif(shutil.which("ffmpeg") is None)` (генерация исходников через lavfi, проверка квадрата и звука через ffprobe).
- **`VideoNoteError` несёт `code` + `detail` + `user_message`, а не `message`.** Обращение к `error.message` даёт AttributeError внутри `except`, и обработчик падает вместо аккуратной ошибки; пользователю показывать только `user_message`, технические детали (код ffmpeg, размер, длительность) — в лог `VIDEO_NOTE_CONVERSION_FAILED`.
- **Лимиты Telegram для кругляшка:** квадрат, ≤ 60 с, ≤ 12 МБ на файл. Поэтому длинное видео обрезается (`-t`), слишком длинный исходник отклоняется, а размер результата проверяется после конвертации; звук сохраняется (`-an` только если дорожки нет).

- **Присланное видео перехватывает Smart Reply, а не `handle_media`.** `handlers/smart_reply.py` берёт `F.video | F.video_note` без состояния и показывает свою клавиатуру («🎬 Разобрать / 💾 Сохранить»), поэтому правки только в `bot.py` пользователь не увидит (симптом: «могу только разобрать и сохранить»). Новые действия для видеофайла — ветка в `smart_video_action` (callback `s:video:<action>`) + кнопка в `keyboards.smart_reply_keyboard("video")`; `run_video_note()` работает с уже скачанным файлом (`download_by_file_id`), скачивать повторно нельзя.
- **В тестах хендлеров `render` подменять monkeypatch'ем, а не фейковым объектом события.** `render` проверяет `isinstance(event, CallbackQuery)` и с самодельным фейком уходит в ветку сообщения — падает на неожиданном `reply_markup`. Образец — `tests/test_video_note_smart_reply.py`.

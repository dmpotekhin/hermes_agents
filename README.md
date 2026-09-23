<div align="center">

# 🏯 Hermes Agent — Конфигурация и профили

[![GitHub](https://img.shields.io/badge/репозиторий-private-8A2BE2?style=flat-square&logo=github)](https://github.com/dmpotekhin/hermes_agents)
[![Профили](https://img.shields.io/badge/профили-5-4FC08D?style=flat-square)](#-профили)
[![Навыки](https://img.shields.io/badge/навыки-600+-FF6B6B?style=flat-square)](#-навыки)
[![JLPT](https://img.shields.io/badge/JLPT-N5_N4_N3-FF6B6B?style=flat-square)](#jlpt-база-знаний)
[![Anki](https://img.shields.io/badge/Anki-колода-00ADD8?style=flat-square&logo=anki)](#-anki-колода-n5-по-дням)
[![macOS](https://img.shields.io/badge/platform-macOS-000000?style=flat-square&logo=apple)](#)

**Полная конфигурация Hermes Agent на macOS · 5 профилей · ~600 навыков · JLPT-база N5–N1**

</div>

---

## 📋 Содержание

- [Что нового](#-что-нового-в-этом-синке)
- [Структура репозитория](#-структура-репозитория)
- [Профили](#-профили)
- [Навыки](#-навыки)
- [Плагины](#-плагины)
- [JLPT База знаний](#-jlpt-база-знаний)
- [Anki-колода N5](#-anki-колода-n5-по-дням)
- [Быстрый старт](#-быстрый-старт)
- [Безопасность](#-безопасность)
- [Диагностика](#-диагностика)

---

## 🆕 Что нового в этом синке

- **+11 общих навыков** (`skills/`): `box`, `weekly-review-planning`, `product-price-monitor`,
  `meeting-action-items`, `document-to-action-items`, `competitor-news-monitor`,
  `email-inbox-triage`, `blocked-page-recovery`, `sdlc-review`, `github`, `codebase-inspection`
- **+40 навыков профиля developer**:
  - UI/дизайн: `improve-ui`, `ui-foundations`, `ui-components`, `ui-checklist`,
    `baseline-ui`, `ui-animations`, `fixing-accessibility`, `fixing-motion-performance`
  - Гейты качества: `clean-code-guard`, `docs-guard`, `test-guard`, `precommit-quality-gate`
  - Контент и рост: `copywriting`, `pricing`, `launch`, `product-marketing`, `seo-audit`, `customer-research`
  - Карты/визуализация: `maplibre-web-maps`, `maplibre-interactive-map`, `globe-gl-visualization`,
    `static-map-visualization`, `web-map-static-deploy`
  - Telegram и прочее: `standalone-telegram-bot`, `telegram-media-features`, `travel-*`,
    `news-aggregation-pipeline`, `python-app-structure-pitfalls`, `hermes-update-recovery`
- **Два новых профиля: `marketing` и `german-tutor`** — оба собраны из общего набора навыков
  (по 59 навыков), у каждого свой SOUL.md
- **Плагины**: `agency-agents-router` (роутер Agency-агентов, ~250 агентов),
  `image_gen/abacus_ai` (генерация изображений)
- **Планы**: `plans/` — browser-admin-ui, pen-dev-cheatsheet, open-design-cheatsheet, add-perplexity
- Обновлены `config.yaml` профилей developer/travel-agent, cron-задачи, `SOUL.md`, журналы навыков

---

## 📁 Структура репозитория

```
~/.hermes/
├── 📄 config.yaml               # Глобальная конфигурация Hermes Agent
├── 📄 SOUL.md                   # Личность агента по умолчанию
├── 📄 .gitignore                # Что не попадает в git
├── 📄 README.md                 # Этот файл
│
├── 👤 profiles/
│   ├── 💻  developer/           # Senior Developer Agent
│   │   ├── config.yaml          #   модель, MCP, tools, compression
│   │   ├── SOUL.md              #   процесс: TDD, code review, frozen specs
│   │   ├── skills/              #   205 навыков
│   │   ├── plugins/             #   agency-agents-router, image_gen
│   │   └── tools/               #   scan_credentials.py (сканер секретов)
│   │
│   ├── 🇯🇵  japanese-tutor/      # Репетитор японского (Sato-sensei)
│   │   ├── config.yaml
│   │   ├── SOUL.md
│   │   ├── skills/              #   87 навыков
│   │   └── cron/jobs.json       #   n5-daily-lesson · 21:00 MSK ежедневно
│   │
│   ├── ✈️  travel-agent/        # Тревел-агент
│   │   ├── config.yaml
│   │   ├── SOUL.md
│   │   └── skills/              #   91 навык
│   │
│   ├── 📣  marketing/           # Marketing Pro — маркетинг и автоматизация
│   │   ├── SOUL.md
│   │   └── skills/              #   59 навыков
│   │
│   └── 🇩🇪  german-tutor/        # Deutschlehrerin (Frau Weber)
│       ├── SOUL.md
│       └── skills/              #   59 навыков
│
├── 🧠 skills/                   # 95 общих навыков (наследуются всеми профилями)
│   ├── creative/                # генерация, дизайн, инфографика, анимации
│   ├── mlops/                   # LLM, инференс, HuggingFace, vLLM, llama.cpp
│   ├── github/                  # PR, code review, CI, Pages
│   ├── research/                # arXiv, графы знаний, цитирование, мониторинг
│   ├── productivity/            # Notion, Google Workspace, PDF/DOCX/XLSX, карты
│   ├── media/                   # YouTube, аудио, музыка, GIF
│   ├── autonomous-ai-agents/    # claude-code, codex, opencode, computer-use
│   ├── security/                # pentest (strix), remediation, tirith-guard
│   └── ...                      # software-development, apple, web, smart-home
│
├── 📦 jp_rag_data/              # JLPT база знаний + Anki + промты
├── 📝 plans/                    # Черновики планов (.hermes/plans/)
├── 🔌 plugins/                  # Глобальные плагины
└── ⏰ cron/                     # Глобальные cron-задачи
```

---

## 👤 Профили

### 💻 developer

Старший разработчик и архитектор — методичный, спокойный, 20 лет опыта.
Строгая дисциплина процесса: классификация задачи → план → TDD → security review → verification.

| Параметр | Значение |
|---------|---------|
| **Назначение** | Разработка: TDD, code review, отладка, архитектура, документация |
| **Модель** | `Qwen/Qwen3.5-35B-A3B` (алиасы `hf-qwen`, `hf-glm`) |
| **Провайдер** | HuggingFace Inference Providers · `router.huggingface.co/v1` |
| **Навыки** | 205 |
| **Плагины** | `agency-agents-router`, `image_gen` (abacus_ai) |
| **Метод** | RED → GREEN → REFACTOR → COMMIT |

#### Обязательный процесс

1. `project-state` → прочитать `.planning/STATE.md`
2. Классификация задачи: `tiny-fix` / `quick-win` / `feature` / `architecture-change`
3. Задача расплывчата → brainstorming (≤5 вопросов)
4. feature/architecture-change → `discuss` → `writing-plans` → план → ждать OK
5. Реализация: RED → GREEN → REFACTOR → COMMIT
6. Завершение: simplify-code → security-review → code-review → verification-before-completion
7. Перед **каждым** коммитом — `scan_credentials.py --staged` (сканер секретов)

#### MCP-серверы

| Сервер | Назначение |
|--------|-----------|
| **playwright** | Браузер, UI-тесты (headless) |
| **filesystem** | Файлы проекта (`~/projects`) |
| **git** | Коммиты, ветки, статус |
| **github** | PR, issues, code review |
| **perplexity** | Веб-поиск с цитированием |
| **obsidian-brain** | Долговременная память в Obsidian |
| **harness_plugin** | DeepSeek Harness (`dsh`) |

#### Экономия токенов

Профиль настроен на агрессивный прунинг контекста:
`compression.proactive_prune_tokens=48000`, `proactive_prune_min_result_chars=2000`.

### 🇯🇵 japanese-tutor

Персональный репетитор японского — **Sato-sensei**.

| Параметр | Значение |
|---------|---------|
| **Назначение** | JLPT N5–N1: грамматика, лексика, разговорная практика |
| **Модель** | `deepseek-v4-flash` |
| **Провайдер** | DeepSeek |
| **Навыки** | 87 |
| **Доставка** | Telegram · ежедневный урок в 21:00 MSK (`n5-daily-lesson`) |
| **Метод** | Последовательное прохождение паттернов Акудзавы |

### ✈️ travel-agent

Помощник в планировании поездок.

| Параметр | Значение |
|---------|---------|
| **Назначение** | Билеты, отели, маршруты, карты, фото-админка |
| **Модель** | `deepseek-v4-flash` |
| **Провайдер** | DeepSeek |
| **Навыки** | 91 |

### 📣 marketing

Маркетинг и автоматизация — **Marketing Pro**.

| Параметр | Значение |
|---------|---------|
| **Назначение** | Копирайтинг, SEO, SMM, аналитика, workflow-автоматизация |
| **Конфиг** | наследует глобальный `config.yaml` |
| **Навыки** | 59 |

### 🇩🇪 german-tutor

Преподаватель немецкого — **Frau Weber**.

| Параметр | Значение |
|---------|---------|
| **Назначение** | Немецкий язык: грамматика, лексика, разговорная практика |
| **Конфиг** | наследует глобальный `config.yaml` |
| **Навыки** | 59 |

---

## 🧠 Навыки

| Расположение | Количество | Область |
|--------------|:----------:|---------|
| `skills/` (общие) | 95 | доступны во всех профилях |
| `profiles/developer/skills/` | 205 | разработка, UI, безопасность, карты, контент |
| `profiles/travel-agent/skills/` | 91 | путешествия, карты, медиа |
| `profiles/japanese-tutor/skills/` | 87 | языки, Obsidian, продуктивность |
| `profiles/marketing/skills/` | 59 | копирайтинг, SEO, аналитика |
| `profiles/german-tutor/skills/` | 59 | языки, продуктивность |

Формат навыка — каталог с `SKILL.md` (YAML-frontmatter + инструкции), при необходимости
`references/`, `scripts/`, `templates/`. Новые навыки ставятся через `skills list/add`,
каталог UI-навыков — `npx skills add ibelick/ui-skills`.

---

## 🔌 Плагины

| Плагин | Профиль | Назначение |
|--------|---------|-----------|
| `agency-agents-router` | developer | Роутер Agency-специалистов (~250 агентов, 4 МБ ростер) |
| `image_gen/abacus_ai` | developer | Генерация изображений через Abacus AI RouteLLM |

---

## 📦 JLPT База знаний

Данные из книг **Noboru Akuzawa — Japanese Sentence Patterns for JLPT** (N5–N1).

### Состав

| Файл | Описание |
|------|----------|
| `patterns.jsonl` | 723 паттерна с примерами, хираганой, ромадзи |
| `chromadb/` | Векторная БД для семантического поиска (модель `intfloat/multilingual-e5-small`) |
| `user_vocab.json` | Персональный словарь: 1007 слов, 26 тем |
| `pokemon_vocab.json` | Словарь Pokémon: 207 слов, 14 категорий (из 283 субтитров) |
| `pokemon_phrasebook.md` | Разговорник Pokémon для просмотра (таблицы по категориям) |
| `pokemon_extra_words.json` | Доп. имена покемонов (Johto) — 68 шт. |
| `study_plan.json` | 30-дневный план N5 с разбивкой по дням |
| `study_progress.json` | Прогресс изучения |
| `query_rag.py` | CLI-поиск по RAG |
| `daily_lesson.py` | Генератор ежедневного урока |
| `30_days_conversation_prompts.md` | 30 промтов для разговорной практики (v1) |
| `Perplexity_N5_30days_v2.md` | 30 промтов v2 — двуязычные, с адаптивной сложностью |
| `Perplexity_N4_30days_v1.md` | 30 промтов N4 — разговорная практика по Акудзаве |
| `n4_akuzawa_monthly_plan.md` | 30-дневный план N4 по Акудзаве |
| `n4_monthly_plan.md` | 30-дневный детальный план N4 |
| `n3_akuzawa_monthly_plan.md` | 30-дневный план N3 по Акудзаве |
| `n2_akuzawa_monthly_plan.md` | 30-дневный план N2 по Акудзаве |
| `n1_akuzawa_monthly_plan.md` | 30-дневный план N1 по Акудзаве |
| `pokemon_conversation_plan.md` | 10 дней разговорной практики по Pokémon (Gemini) |
| `bluebird_song_prompt.md` | Промпт для Gemini: разбор песни ブルーバード |

### Поиск по RAG

Поддерживает запросы на русском, английском и японском.

```bash
# Поиск по всем уровням
python3 ~/.hermes/jp_rag_data/query_rag.py "частица は"

# Поиск только по N5
python3 ~/.hermes/jp_rag_data/query_rag.py "отрицательная форма" N5

# Поиск на японском
python3 ~/.hermes/jp_rag_data/query_rag.py "〜たいです"
```

### Формат паттернов

```json
{
  "id": "n5_0001",
  "jlpt_level": "N5",
  "pattern_title": "の (no) – 1: of (possessive particle)",
  "meaning": "of / possessive particle",
  "formation": "Noun 1 + の + Noun 2",
  "japanese_examples": ["私の名前はテイラーです。"],
  "hiragana_examples": ["わたしの なまえは ていらーです。"],
  "romaji_examples": ["Watashi no namae wa teirâ desu."],
  "english_examples": ["My name is Taylor."],
  "vocabulary": [
    {"word": "私", "reading": "わたし(watashi)", "meaning": "I"},
    {"word": "名前", "reading": "なまえ(namae)", "meaning": "name"}
  ],
  "page_start": 24,
  "page_end": 26
}
```

---

## 🃏 Anki-колода N5 по дням

Готовая колода для интервального повторения всей лексики N5.

**Файл:** [`jp_rag_data/N5_vocab_days.apkg`](jp_rag_data/N5_vocab_days.apkg)

### Характеристики

| Параметр | Значение |
|----------|----------|
| **Всего слов** | 1 444 |
| **Типы карточек** | 3 вида: Kanji→Чтение, Хирагана→Кандзи, Перевод→Кандзи |
| **Всего карточек** | 4 332 |
| **Подколоды** | 22 дня + Дополнительные |
| **С переводом** | 49 слов (`vocabulary` + `user_vocab`) |
| **Без перевода** | 1 395 (можно добавить в Anki) |

### Структура подколод

```
日本語 N5 :: По дням
├── День 1  — Частицы の и は                   (45 слов)
├── День 2  — Связка だ/です, вопросы           (88 слов)
├── День 4  — Частицы が и で                   (41 слово)
├── День 5  — Частица で, でしょう               (41 слово)
├── День 6  — Прошедшее время                   (43 слова)
├── ...                                          ...
├── День 27 — Номинализация の, すぎる           (54 слова)
└── Дополнительные паттерны                     (525 слов)
```

> **Примечание:** Дни 3, 9, 14, 19, 23, 28 — повторение, без новых слов.

### Источники слов

| Источник | Количество |
|----------|:----------:|
| Поле `vocabulary` в паттернах | 29 |
| Извлечено из примеров | ~1 200 |
| Из `user_vocab.json` | 1007 |
| **Всего уникальных** | **1 444** |

### Сборка колоды

```bash
# 1. Установить genanki
pip3 install genanki

# 2. Собрать (без перевода — 15 секунд)
python3 jp_rag_data/build_n5_anki.py

# 3. Импортировать N5_vocab_days.apkg в Anki
```

Чтобы пересобрать после обновления `patterns.jsonl` или `user_vocab.json`:

```bash
cd ~/.hermes && python3 jp_rag_data/build_n5_anki.py
```

---

## 🚀 Быстрый старт

```bash
# 1. Клонировать репозиторий (приватный, SSH)
git clone git@github.com:dmpotekhin/hermes_agents.git ~/.hermes

# 2. Создать .env с API-ключами (в git не попадает)
cp .env.example .env
# Отредактировать .env: DeepSeek, HuggingFace (HF_TOKEN), Perplexity и т.д.

# 3. Установить Hermes (если ещё нет)
# https://hermes-agent.nousresearch.com/docs

# 4. Запустить нужный профиль
hermes --profile developer
hermes --profile japanese-tutor
```

---

## 🔒 Безопасность

В git **не попадают** (см. [`.gitignore`](.gitignore)):

| Что | Причина |
|-----|---------|
| `.env`, `auth.json`, `nous_auth.json` | API-ключи и токены |
| `channel_directory.json`, `gateway_state.json` | Привязка каналов |
| `sessions/`, `logs/`, `cache/`, `audio_cache/`, `image_cache/` | Сессии, логи, кеши |
| `memories/`, `**/pending/` | Долговременная память агента |
| `state.db`, `kanban.db`, `shared-state.db` | Базы данных |
| `backups/`, `**/state-snapshots/`, `state.db.bak*` | Снапшоты и бэкапы (сотни МБ) |
| `node/`, `node_modules/`, `**/__pycache__/` | Встроенный Node-runtime и кеши Python |
| `**/skills/.curator_backups/`, `skills/.hub/*-cache/` | Внутренние кеши навыков |
| `cron/output/` | Сгенерированные уроки |
| `pairing/`, `*.lock`, `*.pid` | Связка с Telegram/Discord, временные файлы |

Дополнительно перед каждым коммитом запускается сканер секретов:

```bash
python3 ~/.hermes/profiles/developer/tools/scan_credentials.py --staged
```

> ⚠️ Известное ложное срабатывание: `pem-private-key` в
> `profiles/developer/plugins/agency-agents-router/data/agents.json` — это заголовки
> `-----BEGIN ... PRIVATE KEY-----` внутри markdown-инструкции SecOps-агента
> (пример того, что должен искать сканер), реального ключа нет.

---

## 🔧 Диагностика

```bash
# Статус Hermes
hermes status

# Логи
tail -f ~/.hermes/logs/*.log

# Перезапуск Telegram-шлюза
cat ~/.hermes/gateway.pid | xargs kill
hermes gateway --daemon

# Состояние git-синка конфигурации
cd ~/.hermes && git status && git log --oneline -5

# Обновление Hermes (и восстановление после сбоя)
# см. навык hermes-update-recovery
```

---

<div align="center">

**Hermes Agents** · © 2026 [@dmpotekhin](https://github.com/dmpotekhin)

</div>

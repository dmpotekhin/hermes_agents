<div align="center">

# 🏯 Hermes Agent — Конфигурация и профили

[![GitHub](https://img.shields.io/badge/репозиторий-privado-8A2BE2?style=flat-square&logo=github)](https://github.com/dmpotekhin/hernes_agents)
[![JLPT](https://img.shields.io/badge/JLPT-N5_N4_N3-FF6B6B?style=flat-square&logo=opencontainersinitiative)](#jlpt-база-знаний)
[![Anki](https://img.shields.io/badge/Anki-колода-00ADD8?style=flat-square&logo=anki)](#anki-колода-n5-по-дням)
[![Hermes](https://img.shields.io/badge/Hermes-Agent-4FC08D?style=flat-square)](#)
[![macOS](https://img.shields.io/badge/platform-macOS-000000?style=flat-square&logo=apple)](#)

**Полная конфигурация Hermes Agent на macOS · 3 профиля · 100+ навыков · JLPT-база N5–N1**

</div>

---

## 📋 Содержание

- [Структура репозитория](#-структура-репозитория)
- [Профили](#-профили)
- [JLPT База знаний](#-jlpt-база-знаний)
  - [Поиск по RAG](#поиск-по-rag)
  - [Формат паттернов](#формат-паттернов)
- [Anki-колода N5](#-anki-колода-n5-по-дням)
  - [Характеристики](#характеристики)
  - [Как использовать](#как-использовать)
  - [Сборка](#сборка-колоды)
- [Быстрый старт](#-быстрый-старт)
- [Безопасность](#-безопасность)
- [Диагностика](#-диагностика)

---

## 📁 Структура репозитория

```
~/.hermes/
├── 📄 config.yaml               # Глобальная конфигурация Hermes Agent
├── 📄 SOUL.md                   # Личность агента
├── 📄 .gitignore                # Игнорируемые файлы
│
├── 👤 profiles/
│   ├── 💻  developer/           # Senior Developer Agent
│   │   ├── config.yaml
│   │   ├── SOUL.md
│   │   └── skills/              # Навыки профиля (софт-дев, MCP)
│   │
│   ├── 🇯🇵  japanese-tutor/      # Репетитор японского языка
│   │   ├── config.yaml
│   │   ├── SOUL.md
│   │   ├── skills/              # Навыки профиля
│   │   └── cron/jobs.json       # Ежедневный урок в 21:00 MSK
│   │
│   └── ✈️  travel-agent/        # Тревел-агент
│       ├── config.yaml
│       ├── SOUL.md
│       └── skills/
│
├── 🧠 skills/                   # Общие навыки
│   ├── creative/                # генерация, дизайн, инфографика
│   ├── mlops/                   # LLM, инференс, HuggingFace
│   ├── github/                  # PR, code review, CI
│   ├── research/                # arXiv, paper writing
│   ├── productivity/            # Notion, Google Workspace, PDF
│   ├── media/                   # YouTube, аудио, GIF
│   └── ...                      # 100+ навыков
│
├── 📦 jp_rag_data/              # JLPT база знаний
│   ├── chromadb/                # ChromaDB векторная БД
│   ├── patterns.jsonl           # 723 паттерна N5–N1
│   ├── user_vocab.json          # 929 слов · 25 тем
│   ├── pokemon_vocab.json       # 207 слов · словарь Pokémon (из 283 субтитров)
│   ├── pokemon_phrasebook.md        # Разговорник Pokémon (14 категорий, markdown)
│   ├── pokemon_extra_words.json     # +68 имён покемонов из Johto
│   ├── 30_days_conversation_prompts.md    # Промты для разговорной практики (v1)
│   ├── Perplexity_N5_30days_v2.md         # Промты v2 · двуязычные + адаптивная сложность
│   ├── n4_akuzawa_monthly_plan.md   # 30-дневный план N4 (Акудзава)
│   ├── n4_monthly_plan.md           # 30-дневный детальный план N4
│   ├── n3_akuzawa_monthly_plan.md   # 30-дневный план N3 (Акудзава)
│   ├── n2_akuzawa_monthly_plan.md   # 30-дневный план N2 (Акудзава)
│   ├── n1_akuzawa_monthly_plan.md   # 30-дневный план N1 (Акудзава)
│   ├── query_rag.py             # Поиск по паттернам
│   ├── daily_lesson.py          # Генератор урока
│   ├── study_plan.json          # 30-дневный план N5
│   ├── N5_vocab_days.apkg       # Anki-колода · 1 444 слова
│   └── build_n5_anki.py         # Сборщик Anki-колоды
│
├── 🔌 plugins/                  # Внешние плагины
└── ⏰ cron/                     # Глобальные cron-задачи
```

---

## 👤 Профили

### 🇯🇵 japanese-tutor

Ваш персональный репетитор японского языка — **Sato-sensei**.

| Параметр | Значение |
|---------|---------|
| **Назначение** | Изучение JLPT N5–N1, грамматика, лексика |
| **Модель** | `deepseek-v4-flash` |
| **Провайдер** | DeepSeek |
| **Доставка** | Telegram · ежедневно в 21:00 MSK |
| **Метод** | Последовательное прохождение паттернов Акудзавы |

### 💻 developer

Старший разработчик и архитектор — методичный, спокойный, с 20-летним опытом.

| Параметр | Значение |
|---------|---------|
| **Назначение** | Разработка: TDD, code review, отладка, архитектура |
| **Модель** | `deepseek-v4-pro` |
| **Провайдер** | DeepSeek |
| **MCP-серверы** | playwright, filesystem, git, github |
| **Метод** | RED → GREEN → REFACTOR → COMMIT |

#### Обязательный процесс

1. Задача расплывчата → brainstorming (≤5 вопросов)
2. После прояснения → writing-plans → план → ждать OK
3. Реализация: RED → GREEN → REFACTOR → COMMIT
4. Завершение: simplify-code → requesting-code-review → verification

#### MCP-серверы

| Сервер | Назначение |
|--------|-----------|
| **playwright** | Браузер, UI-тесты (headless) |
| **filesystem** | Файлы проекта (`~/projects`) |
| **git** | Коммиты, ветки, статус |
| **github** | PR, issues, code review |

### ✈️ travel-agent

Помощник в планировании поездок.

| Параметр | Значение |
|---------|---------|
| **Назначение** | Поиск билетов, отелей, маршрутов |
| **Модель** | `deepseek-v4-flash` |
| **Провайдер** | DeepSeek |

---

## 📦 JLPT База знаний

Данные из книг **Noboru Akuzawa — Japanese Sentence Patterns for JLPT** (N5–N1).

### Состав

| Файл | Описание |
|------|----------|
| `patterns.jsonl` | 723 паттерна с примерами, хираганой, ромадзи |
| `chromadb/` | Векторная БД для семантического поиска (модель `intfloat/multilingual-e5-small`) |
|| `user_vocab.json` | Персональный словарь: 929 слов, 25 тем |
|| `pokemon_vocab.json` | Словарь Pokémon: 207 слов, 14 категорий (из 283 субтитров) |
|| `pokemon_phrasebook.md` | Разговорник Pokémon для просмотра (таблицы по категориям) |
|| `pokemon_extra_words.json` | Доп. имена покемонов (Johto) — 68 шт. |
| `study_plan.json` | 30-дневный план N5 с разбивкой по дням |
| `study_progress.json` | Прогресс изучения |
| `query_rag.py` | CLI-поиск по RAG |
| `daily_lesson.py` | Генератор ежедневного урока |
| `30_days_conversation_prompts.md` | 30 промтов для разговорной практики (v1) |
|| `Perplexity_N5_30days_v2.md` | 30 промтов v2 — двуязычные, с адаптивной сложностью |
|| `n4_akuzawa_monthly_plan.md` | 30-дневный план N4 по Акудзаве |
|| `n4_monthly_plan.md` | 30-дневный детальный план N4 |
|| `n3_akuzawa_monthly_plan.md` | 30-дневный план N3 по Акудзаве |
|| `n2_akuzawa_monthly_plan.md` | 30-дневный план N2 по Акудзаве |
|| `n1_akuzawa_monthly_plan.md` | 30-дневный план N1 по Акудзаве |

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
|| Из `user_vocab.json` | 929 |
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
# 1. Клонировать репозиторий
git clone git@github.com:dmpotekhin/hernes_agents.git ~/.hermes

# 2. Создать .env с API-ключами
cp .env.example .env
# Отредактировать .env: DeepSeek, OpenAI и т.д.

# 3. Установить Hermes (если ещё нет)
# https://hermes-agent.nousresearch.com/docs

# 4. Запустить
hermes --profile japanese-tutor
```

---

## 🔒 Безопасность

Следующие файлы **НЕ попадают** в git (см. [`.gitignore`](.gitignore)):

| Файл | Причина |
|------|---------|
| `.env` | API-ключи и токены |
| `auth.json`, `nous_auth.json` | Аутентификация |
| `channel_directory.json` | Привязка каналов |
| `sessions/`, `logs/`, `cache/` | Сессии и логи |
| `memories/` | Долговременная память агента |
| `state.db`, `kanban.db` | Базы данных |
| `cron/output/` | Сгенерированные уроки |
| `pairing/` | Связка с Telegram/Discord |

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

# Проверить состояние git
cd ~/.hermes && git status
```

---

<div align="center">

**Hermes Agents** · © 2026 [@dmpotekhin](https://github.com/dmpotekhin)

</div>

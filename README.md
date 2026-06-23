# Hermes Agent — Конфигурация и профили

Репозиторий содержит полную конфигурацию **Hermes Agent** на macOS, включая все профили, навыки (skills), плагины и JLPT-базу для изучения японского языка.

---

## Структура репозитория

```
~/.hermes/
├── config.yaml              # Глобальная конфигурация Hermes Agent
├── SOUL.md                  # Личность агента (по умолчанию пустая)
├── .gitignore               # Игнорируемые файлы (секреты, кэш, логи)
│
├── profiles/
│   ├── japanese-tutor/      # Основной профиль — репетитор японского
│   │   ├── config.yaml          # Конфигурация профиля
│   │   ├── SOUL.md              # Личность профиля
│   │   ├── skills/              # Навыки (скиллы) профиля
│   │   └── cron/jobs.json       # Расписание: N5-урок ежедневно в 21:00
│   │
│   └── travel-agent/        # Второй профиль — тревел-агент
│       ├── config.yaml
│       ├── SOUL.md
│       └── skills/
│
├── skills/                  # Общие навыки (доступны всем профилям)
│   ├── creative/            # Генерация изображений, ASCII-art, Excalidraw, p5.js
│   ├── mlops/               # LLM-инференс (llama.cpp, vLLM), HuggingFace
│   ├── research/            # arXiv, бумаги, blogwatcher
│   ├── productivity/        # Notion, Google Workspace, Airtable
│   ├── github/              # GitHub workflow, PR, code review
│   ├── media/               # YouTube, GIF, аудио
│   ├── devops/              # Kanban-доска
│   └── ...                  # И другие категории
│
├── plugins/                 # Плагины (внешние репозитории)
│
├── jp_rag_data/             # JLPT база знаний (японский язык)
│   ├── chromadb/            # Векторная БД для семантического поиска
│   ├── patterns.jsonl       # 723 грамматических паттерна N5–N1
│   ├── user_vocab.json      # Словарь (174 слова в 15 темах)
│   ├── query_rag.py         # Скрипт поиска по RAG
│   ├── daily_lesson.py      # Генератор ежедневного урока
│   ├── study_plan.json      # 30-дневный план N5
│   ├── N5_vocab_days.apkg   # Anki-колода: 1 444 слова N5 по дням
│   └── build_n5_anki_*.py   # Скрипты сборки Anki-колод
│
└── cron/                    # Глобальные cron-задачи Hermes
```

---

## Профили

### japanese-tutor
- **Назначение:** Репетитор японского языка (Sato-sensei)
- **Модель:** deepseek-v4-flash (провайдер: DeepSeek)
- **Задачи:** Последовательное изучение JLPT N5-N1, проверка грамматики, словарный запас
- **Cron:** Урок N5 каждый день в 21:00 MSK (доставляется в Telegram)

### travel-agent
- **Назначение:** Тревел-агент для планирования поездок
- **Модель:** deepseek-v4-flash
- **Задачи:** Поиск отелей, билетов, маршрутов

---

## JLPT База знаний (jp_rag_data)

### Что внутри
| Файл | Описание |
|---|---|
| `patterns.jsonl` | 723 грамматических паттерна из книг Нобору Акудзавы (N5-N1) |
| `chromadb/` | Векторная БД (ChromaDB) с эмбеддингами для семантического поиска |
| `user_vocab.json` | Персональный словарь (174 слова, 15 тем) |
| `study_plan.json` | План изучения N5 на 30 дней |
| `study_progress.json` | Прогресс изучения |
| `query_rag.py` | Скрипт поиска по RAG |
| `daily_lesson.py` | Генератор ежедневного урока |

### Поиск по RAG

```bash
# Поиск по всем уровням
python3 ~/.hermes/jp_rag_data/query_rag.py "частица は"

# Поиск только по N5
python3 ~/.hermes/jp_rag_data/query_rag.py "отрицательная форма" N5

# Поиск на японском
python3 ~/.hermes/jp_rag_data/query_rag.py "～たいです"
```

### Формат паттернов (patterns.jsonl)

```json
{
  "level": "N5",
  "pattern": "〜たいです",
  "hiragana": "〜たいです",
  "meaning": "Хотеть сделать что-то",
  "examples": [
    {
      "kanji": "日本に行きたいです。",
      "hiragana": "にほんにいきたいです。",
      "romaji": "Nihon ni ikitai desu.",
      "translation": "Я хочу поехать в Японию."
    }
  ],
  "vocab": [
    {"kanji": "日本", "hiragana": "にほん", "romaji": "nihon", "meaning": "Япония"}
  ]
}
```

---

## Anki-колода N5 по дням

Готовая колода для интервального повторения всей лексики N5.

**Файл:** `jp_rag_data/N5_vocab_days.apkg`

### Характеристики

| Параметр | Значение |
|---|---|
| Всего слов | 1 444 |
| Типов карточек | 3 (Kanji→Чтение, Хирагана→Кандзи, Перевод→Кандзи) |
| Всего карточек | 4 332 |
| Подколод | 22 дня + Дополнительные |
| С переводом | 49 слов (из `vocabulary` поля паттернов + user_vocab) |
| Без перевода | 1 395 (можно добавить в Anki через кнопку Edit) |

### Как использовать

1. Открыть `N5_vocab_days.apkg` в AnkiDesktop или AnkiDroid
2. Колода автоматически разобьётся на подколоды по дням:
   - `日本語 N5 :: По дням :: День 1 - Частицы の и は`
   - `日本語 N5 :: По дням :: День 2 - Связка だ/です...`
   - ...
3. Учить по одному дню в день, параллельно с основным курсом

### Источники слов

| Источник | Слов |
|---|---|
| Поле `vocabulary` в паттернах | 29 |
| Извлечено из примеров-предложений | ~1 200 |
| Из user_vocab.json | 174 |

### Сборка колоды

```bash
# Установить genanki
pip3 install genanki

# Собрать колоду (без перевода — быстро)
python3 jp_rag_data/build_n5_now.py

# Собрать колоду с переводом через Google Translate (долго, ~20 мин)
python3 jp_rag_data/build_n5_final.py
```

Скрипты сборки лежат в `~/Downloads/`. Чтобы собрать заново после обновления паттернов:

```bash
cp ~/Downloads/build_n5_now.py ~/.hermes/jp_rag_data/
cd ~/.hermes && python3 jp_rag_data/build_n5_now.py
```

---

## Быстрый старт после клонирования

```bash
# 1. Клонировать репозиторий
git clone git@github.com:dmpotekhin/hernes_agents.git ~/.hermes

# 2. Создать .env с API-ключами (не в git!)
cp .env.example .env
# Отредактировать .env: вставить ключи DeepSeek, OpenAI и т.д.

# 3. Установить Hermes (если не установлен)
# https://hermes-agent.nousresearch.com/docs

# 4. Запустить
hermes --profile japanese-tutor
```

---

## Важные замечания

### Что НЕ попало в git (смотри .gitignore)
- `.env` — API-ключи и токены
- `auth.json`, `nous_auth.json` — аутентификация
- `channel_directory.json` — привязка каналов
- `sessions/`, `logs/`, `cache/` — сессии и логи
- `memories/` — долговременная память агента
- `state.db`, `kanban.db` — базы данных рантайма
- `cron/output/` — сгенерированные уроки
- `pairing/` — связка с Telegram/Discord

### Если что-то пошло не так
```bash
# Проверить статус
hermes status

# Посмотреть логи
tail -f ~/.hermes/logs/*.log

# Перезапустить шлюз (Telegram)
cat ~/.hermes/gateway.pid | xargs kill
hermes gateway --daemon
```

---

## Поддержка

По вопросам обращаться к владельцу репозитория (@dmpotekhin).

# Anki-колоды из JLPT-лексики

Генерация `.apkg`-файлов для Anki на основе паттернов из patterns.jsonl.

## Зависимости

```bash
pip install genanki
```

## Разбивка по дням (study_plan.json)

Вместо одной большой колоды можно создавать **подколоды по дням**, используя Anki's hierarchy (символ `::` в имени колоды):

```
日本語 N5 :: По дням
├── День 1 - Частицы の и は              # 45 слов
├── День 2 - Связка だ/です, вопросы...   # 88 слов
├── ...
└── Дополнительные                        # 525 слов (паттерны вне плана)
```

**Механизм:** `genanki.Package()` принимает список колод. Каждая колода — `genanki.Deck(id, name)` с вложенным именем:

```python
all_decks = []
for dn in sorted(day_vocab):
    deck = genanki.Deck(2058370300 + dn,
        f"日本語 N5 :: По дням::День {dn} - {day['title'][:40]}")
    for item in day['items']:
        deck.add_note(genanki.Note(model=model, fields=[...]))
    all_decks.append(deck)

genanki.Package(all_decks).write_to_file("N5_vocab_days.apkg")
```

**Карта день → pattern ID** берётся из `study_plan.json`:

```python
with open(PLAN_PATH) as f:
    plan = json.load(f)
for day in plan["days"]:
    dn = day["day"]
    pattern_ids = day["patterns"]  # ["n5_0001", "n5_0002", ...]
    # patterns не в плане → в "Дополнительные"
```

Паттерны из `all_n5 - plan_ids` идут в отдельную подколоду «Дополнительные».

## Три источника лексики (N5)

| Источник | Откуда | Слов |
|---|---|---|
| Поле `vocabulary` | Массив `vocabulary` внутри каждого паттерна | ~28 |
| Примеры-предложения | `hiragana_examples` → токены → фильтр | ~1,200 |
| `user_vocab.json` | Персональный словарь пользователя | ~170 |

Все три объединяются, дедуплицируются по ключу (kanji, hiragana).

## Структура patterns.jsonl

```json
{
  "id": "n5_0001", "jlpt_level": "N5",
  "pattern_title": "の (no) – 1: of (possessive particle)",
  "vocabulary": [
    {"word": "私", "reading": "わたし(watashi)", "meaning": "I"},
    {"word": "名前", "reading": "なまえ(namae)", "meaning": "name"}
  ],
  "japanese_examples": ["(1)私の名前はテイラーだ。"],
  "hiragana_examples": ["(1)わたしの なまえは ていらーだ。"],
  "english_examples": ["(1)My name is Taylor."]
}
```

**Форматы `reading`:** `わたし(watashi)` — хирагана(ромадзи); `しゅっしん` — только хирагана; `アメリカ` — катакана.

## Скрипт генерации (полная колода)

Скрипт: `~/Downloads/build_n5_anki_v3.py`

### Алгоритм

1. Извлечь `vocabulary`-секцию из N5-паттернов
2. Извлечь из `hiragana_examples`: разбить по пробелам, отфильтровать мусор (частицы, связки, местоимения, числа, катакану), сопоставить с `japanese_examples` для kanji-формы
3. Смержить `user_vocab.json` (поля: kanji, hiragana, romaji, translation)
4. Дедуплицировать по (kanji, hiragana)
5. Создать Anki-колоду с 3 типами карточек

### Подколоды через genanki.Package

Вместо одной колоды — список колод в одном `.apkg`. Ключевой код:

```python
all_decks = []
for dn in sorted(day_vocab):
    deck = genanki.Deck(2058370300 + dn,
        f"日本語 N5 :: По дням::День {dn} - {title}")
    for item in items:
        deck.add_note(...)
    all_decks.append(deck)
genanki.Package(all_decks).write_to_file("N5_vocab_days.apkg")
```

Паттерны не в plan_ids → подколода "Дополнительные".

### 3 типа карточек

| Тип | Лицо | Оборот |
|---|---|---|
| Kanji → Reading | 名前 | なまえ / namae — "имя" |
| Hiragana → Kanji | なまえ | 名前 — "имя" |
| Meaning → Kanji | имя | 名前 / なまえ (namae) |

### SKIP-фильтр (слова НЕ извлекать из примеров)

```
частицы: はがをにでへとものかやからまでよりねよさわなぞぜ
связки: ですますだでしょうだろうたいないぬいるいますあるあります
указательные: このそのあのどのこれそれあれどれここそこあそこどこ
местоимения: わたしあなたかれかのじょかれら
приветствия: こんにちはこんばんはおはようさようならすみませんはい
союзы: そしてそれからしかしでもだからそれでそれに
числа: いちにさんしごろくしちはちくじゅうひゃくせんまん
счёт: ひとつふたつみっつよっついつつ...
суффиксы: たちさまさんちゃんくんどの
единицы: 第円年月日時分秒
```

### Парсинг чтения

```python
def parse_reading(raw):
    m = re.match(r"^([^()]+?)(?:\(([^)]*)\))?$", raw.strip())
    hira = m.group(1).strip() if m else raw.strip()
    roma = m.group(2).strip() if m and m.group(2) else ""
    return hira, roma
```

### Поиск kanji-формы

```python
kanji_clusters = re.findall(r'[\u4e00-\u9fff]+', jap_s)
# Берём самый длинный кластер как kanji-форму
kanji = max(kanji_set, key=len) if kanji_set else hira
```

### Извлечение слов из hiragana_examples

```python
def get_words_from_hiragana(hira_s):
    hira_s = re.sub(r'^\(\d+\)\s*', '', hira_s).strip()
    hira_s = re.sub(r'[^\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff\w\s]', '', hira_s)
    result = []
    for w in re.split(r'[\s/]+', hira_s):
        w = w.strip()
        if len(w) < 2 or w in SKIP: continue
        if re.match(r'^[ァ-ヶー]+$', w): continue   # katakana only
        if re.match(r'^[0-9０-９]+$', w): continue   # numbers
        result.append(w)
    return result
```

## Перевод слов (опционально)

Два подхода для перевода слов без meaning (когда vocabulary-поле пустое):

### 1. Google Translate (batch)

```python
from deep_translator import GoogleTranslator
gt = GoogleTranslator(source="auto", target="ru")
result = gt.translate("食べる")  # -> "есть / кушать"
```

**Проблемы:**
- ~0.15s задержки между запросами (rate limiting)
- При 1400+ словах перевод занимает 15-20 минут
- Google может заблокировать после ~800 запросов
- Использовать `time.sleep(0.15)` между вызовами

### 2. Без перевода (быстрый старт)

- ~49 слов с переводом из vocabulary + user_vocab
- ~1395 слов без перевода
- В Anki есть встроенный словарь (редактирование карточки)

### 3. Merge с user_vocab.json

```python
# Приоритет: hiragana -> kanji
for item in items:
    if not item["meaning"]:
        item["meaning"] = user_tr.get(item["hiragana"],
                          user_tr.get(item["kanji"], ""))
```

## Результат (N5, полная колода с подколодами)

| Метрика | Значение |
|---|---|
| Уникальных слов | ~1,444 |
| С kanji | ~1,340 |
| С переводом | ~49 (vocab + user_vocab) |
| Подколод | 22 дня + Дополнительные |
| Типов карточек | 3 |
| Всего карточек | ~4,332 |

## Ограничения

1. Переводы только у ~190 слов (из vocabulary + user_vocab). Остальные — без перевода.
2. Kanji-форма может быть неточной (берётся самый длинный кластер).
3. SKIP-фильтр не идеален — часть смысловых слов может потеряться.
4. Счётные суффиксы из примеров не извлекаются.

## Запуск

```bash
# Полная колода N5
python3 ~/Downloads/build_n5_anki_v3.py
```

## Платформы Anki

| Платформа | Приложение | Цена |
|---|---|---|
| Android | AnkiDroid | Бесплатно |
| iOS | AnkiMobile | Платно |
| macOS/Win/Linux | Anki Desktop | Бесплатно |

## Ссылки

- [genanki docs](https://github.com/kerrickstaley/genanki)

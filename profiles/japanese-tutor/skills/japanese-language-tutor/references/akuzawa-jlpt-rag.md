# RAG-база по JLPT Sentence Patterns (Akuzawa)

## Расположение

```
~/Downloads/jp_rag_data/
├── patterns.jsonl           # 1.5MB — 723 паттерна, структурированные
├── chromadb/                # 12MB — векторная база ChromaDB
│   ├── chroma.sqlite3
│   └── ...
├── query_rag.py             # скрипт для семантического поиска
├── build_jp_rag_v3.py       # парсер PDF → JSONL
└── build_chroma_rag.py      # JSONL → ChromaDB с эмбеддингами
```

## Итого: 723 грамматических паттерна

| Уровень | Паттернов | Примеров | Слов в словаре |
|---------|-----------|----------|----------------|
| N5 | 74 | ~450 | ~150 |
| N4 | 115 | ~700 | ~200 |
| N3 | 127 | ~760 | ~150 |
| N2 | 195 | ~1170 | ~170 |
| N1 | 212 | ~1270 | ~170 |
| **Всего** | **723** | **~4386** | **~837** |

Каждый паттерн содержит: объяснение, формулу, 5-7 примеров (японский, английский, хирагана, ромадзи), словарь.

## Просмотр содержимого (если ученик спрашивает "что в базе")

```bash
# Все N5 паттерны кратко
python3 -c "
import json
with open('~/Downloads/jp_rag_data/patterns.jsonl') as f:
    for line in f:
        p = json.loads(line)
        if p['jlpt_level'] == 'N5':
            print(f\"{p['id']}: {p['pattern_title'][:55]}\")
"

# Полная информация о конкретном паттерне
python3 -c "
import json
with open('~/Downloads/jp_rag_data/patterns.jsonl') as f:
    for line in f:
        p = json.loads(line)
        if p['id'] == 'n5_0001':
            print(json.dumps(p, indent=2, ensure_ascii=False))
"

# Статистика по всей базе
python3 -c "
import json
from collections import Counter
lvls = Counter()
ex = 0
vocab = 0
with open('~/Downloads/jp_rag_data/patterns.jsonl') as f:
    for line in f:
        p = json.loads(line)
        lvls[p['jlpt_level']] += 1
        ex += len(p['japanese_examples'])
        vocab += len(p['vocabulary'])
print('Patterns:', dict(lvls))
print('Total examples:', ex)
print('Total vocab:', vocab)
"
```

## Использование

```bash
# Поиск на любом языке (русский, японский, английский)
cd ~/Downloads/jp_rag_data
python3 query_rag.py 'частица は тема предложения'
python3 query_rag.py 'たい want to do'
python3 query_rag.py 'глагол する спряжение'

# С фильтром по уровню JLPT
python3 query_rag.py 'て-form' N5
python3 query_rag.py 'пассивный залог' N3
```

## Техническая реализация

### Векторная база
- **ChromaDB** (PersistentClient, хранилище — Parquet/SQLite на диске)
- **Модель эмбеддингов:** `intfloat/multilingual-e5-small` (384d, 118MB)
- **Поддерживаемые языки:** японский, английский, русский (семантический поиск cross-lingual)
- **Расстояние:** cosine similarity
- **Префиксы e5:** документы с `passage:`, запросы с `query:`

### Зависимости
```bash
pip install chromadb sentence-transformers "numpy<2" "sentence-transformers<3.0"
```

**Важно:** 
- PyTorch 2.2.2 (macOS по умолчанию) несовместим с NumPy >=2. Установка `numpy<2` решает проблему: `python3.11 -m pip install "numpy<2"`
- sentence-transformers 5.x требует PyTorch >=2.4. На macOS с PyTorch 2.2.2 нужна версия <3.0: `python3.11 -m pip install "sentence-transformers<3.0"`
- HuggingFace модели кешируются в ~/.cache/huggingface/ (~120MB для multilingual-e5-small)

### Парсинг PDF

**Сложности и их решения:**

1. **TOC vs контент:** первые ~20 страниц каждой книги — оглавление и предисловие. Парсер начинает поиск паттернов с `content_start` (N5=20, N4=18, N3=13, N2=20, N1=31).

2. **"Meaning:" заголовок:** некоторые паттерны имеют явный `Meaning:`, другие — просто текст после названия паттерна. Решение: весь текст между заголовком и первой секцией (日本語/英語/etc.) собирается как explanation.

3. **Multi-page паттерны:** один паттерн может занимать 2-6 страниц. Парсер объединяет все страницы от заголовка до следующего заголовка.

4. **Отсутствующие секции:** не все паттерны имеют 英語, ひらがな, ローマ字, или словообразовательные секции. Парсер собирает то, что есть.

5. **Грязный текст из PDF:** символы вроде `\uff08` (полная ширина) нормализуются.

**Ключевые константы для парсинга (`FILES` словарь):**
- Каждая запись: `'N5': ('filename.pdf', content_start_page)`
- `content_start` — страница, после которой начинается контент (не TOC/предисловие)

### Программный импорт (для Telegram-бота и других интеграций)

```python
import sys
sys.path.insert(0, '/Users/dmitrypotekhin/Downloads/jp_rag_data')
from query_rag import search, format_result, format_simple

results = search('частица は', jlpt_level='N5', n_results=3)
for p in results:
    print(format_simple(p))
```

## Telegram Gateway и связь с RAG

RAG используется через Telegram-бота (профиль `japanese-tutor`). При ответе на грамматический вопрос в Telegram:

1. Gateway принимает сообщение через Telegram API
2. Агент (Sato-sensei) загружает skill `japanese-language-tutor`
3. При необходимости RAG-поиска — запускает `python3 query_rag.py '<вопрос>' <JLPT_LEVEL>`
4. Формирует ответ на русском с примерами из найденных паттернов

### Gateway reconnect (если Telegram отвалился)

Симптом: `connection failed` для api.telegram.org в gateway.log.
Проверка: `curl -s --connect-timeout 5 https://api.telegram.org/bot<TOKEN>/getMe`

Если API отвечает (200/404 — норма, токен не тот путь), а gateway не подключается:
```bash
# 1. Найти PID старого gateway
ps aux | grep "hermes gateway"

# 2. Убить
kill <PID>

# 3. Запустить заново в фоне
hermes gateway run --profile japanese-tutor  # с background=true + notify_on_complete

# 4. Дождаться подключения (проверить логи)
sleep 10 && tail -5 ~/.hermes/profiles/japanese-tutor/logs/gateway.log
# Должно быть: "✓ telegram connected"

# 5. Проверить статус
hermes gateway status --profile japanese-tutor
```

## Когда пересобирать RAG

- При добавлении новых PDF-материалов по японскому
- После исправления/дополнения данных в patterns.jsonl
- Команда: `cd ~/Downloads && python3 build_jp_rag_v3.py && python3 build_chroma_rag.py`

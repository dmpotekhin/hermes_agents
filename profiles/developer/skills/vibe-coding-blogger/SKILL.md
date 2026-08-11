---
name: vibe-coding-blogger
description: Use when the user wants to create a post for their Telegram QA blog from real development activity — scan Obsidian dev journals, suggest topics based on recent work, generate and critique posts about testing, Kafka, AI tools, and vibe coding
---

# Vibe Coding Blogger

Генератор постов для Telegram-канала о тестировании ПО из реальных событий разработки.

## Pipeline

```
Obsidian Dev Journal → Scanner → Topic Ideas → Writer (prompt) → LLM → Critic → Final Post
```

## Команды

| Команда | Что делает |
|---------|-----------|
| «предложи темы для постов» | Сканирует журнал за 7 дней, предлагает 3 темы |
| «напиши пост про [тему]» | Генерирует черновик → критикует → выдаёт финальный текст |
| «покажи логи за [N] дней» | Показывает сырые события из журнала |
| «сохрани пост» | Сохраняет через post_saver в output/ |

## Зависимости

Контент-фэктори: `/Users/dmitrypotekhin/content-factory/`

Модули:
- `modules/devlog_scanner.py` — сканер Obsidian-журналов
- `modules/topic_suggester.py` — генератор идей (rule-based + LLM prompt)
- `modules/writer.py` — промпты для генерации постов
- `modules/critic.py` — 6 категорий критики
- `modules/style_expert.py` — адаптация под Telegram
- `modules/hashtag_expert.py` — подбор хештегов
- `modules/post_saver.py` — сохранение в output/

## Workflow

### Шаг 1: Предложить темы

Спроси пользователя: «За сколько дней посмотреть логи?» (по умолчанию 7).

Запусти сканер:
```bash
cd /Users/dmitrypotekhin/content-factory && python3 -c "
from modules.devlog_scanner import scan_recent_events, format_events_for_llm
from modules.topic_suggester import suggest_topics_rule_based, build_suggestion_prompt

events = scan_recent_events(days=7)
result = suggest_topics_rule_based(events, max_topics=3)
print(result.summary())
print()
print('=== PROMPT FOR BETTER TOPICS (send to me, the LLM) ===')
print(build_suggestion_prompt(format_events_for_llm(events), max_topics=3))
"
```

Покажи пользователю rule-based темы. Спроси: «Сгенерировать более качественные темы через LLM (на основе промпта выше)?»

### Шаг 2: Генерация поста

Когда пользователь выбрал тему:

1. Если тема из rule-based — используй её key_points
2. Если тема своя — попроси 2-3 ключевых момента

2. Запусти writer для создания промпта:
```bash
cd /Users/dmitrypotekhin/content-factory && python3 -c "
from modules.writer import _build_writer_prompt
prompt = _build_writer_prompt(
    topic='<ТЕМА>',
    key_points=['<пункт1>', '<пункт2>', '<пункт3>'],
    tone='экспертный_но_дружелюбный',
    target_length='средний',
)
print(prompt)
"
```

3. ТЫ (Hermes LLM) генерируешь пост по этому промпту. Не проси пользователя копировать в другой LLM — ты и есть LLM. Сгенерируй пост сам.

4. Прогони через critic:
```bash
cd /Users/dmitrypotekhin/content-factory && python3 -c "
from modules.critic import critique
report = critique('''<СГЕНЕРИРОВАННЫЙ ПОСТ>''')
print(report)
if report.has_critical:
    print('\\n⚠️ Есть критичные замечания — нужно исправить')
"
```

5. Если есть критика — исправь пост и перепрогони.

6. Покажи финальный пост пользователю.

### Шаг 3: Сохранение

Когда пользователь одобрил:
```bash
cd /Users/dmitrypotekhin/content-factory && python3 -c "
from modules.style_expert import adapt_for_telegram
from modules.hashtag_expert import select_hashtags, append_hashtags
from modules.post_saver import save_post

content = '''<ФИНАЛЬНЫЙ ТЕКСТ>'''
style_result = adapt_for_telegram(content, add_emoji=True)
content = style_result.content
hashtag_result = select_hashtags(content, max_count=5, strategy='balanced')
saved = save_post(
    topic='<ТЕМА>',
    content=content,
    hashtags=hashtag_result.hashtags,
    metadata={'tone': '<ТОН>', 'source': 'devlog'},
)
print(saved.print_for_copy())
"
```

## Важные правила

1. **Ты — LLM.** Не проси пользователя копировать промпты в ChatGPT. Генерируй посты сам.
2. **Реальные примеры.** Всегда ссылайся на реальные проекты пользователя: kafka-test-trainer, qa-interview-trainer, obsidian-brain, japanese-reader, travel-content-factory.
3. **Живой тон.** Никаких «в современном мире разработки...». Пиши как человек, который реально это делал.
4. **Критик обязателен.** Никогда не отдавай пост без прогона через critic.
5. **Сохраняй.** Каждый одобренный пост — в output/ через post_saver.

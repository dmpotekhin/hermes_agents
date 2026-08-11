# Content Factory Architecture

## Module Pipeline

```
Obsidian Brain/journal/*.md
        │
        ▼
┌─────────────────────┐
│  devlog_scanner.py   │  ← читает Obsidian, парсит строки формата
│  scan_recent_events()│     "ЧЧ:ММ | project: name | description"
│  format_for_llm()    │
└─────────┬───────────┘
          │ list[DevEvent]
          ▼
┌─────────────────────┐
│  topic_suggester.py  │
│  ┌─ rule-based       │  ← ANGLE_TEMPLATES (без LLM, мгновенно)
│  │  suggest_topics() │
│  └─ LLM-based        │  ← build_suggestion_prompt() (качественнее)
│     (через промпт)   │
│                      │
│  save_to_obsidian()  │  ← запись в Brain/notes/content/
└─────────┬───────────┘
          │ list[SuggestedTopic]
          ▼
┌─────────────────────┐
│  writer.py           │  ← _build_writer_prompt()
│  create_draft()      │     формирует промпт для LLM
└─────────┬───────────┘
          │ prompt text
          ▼
┌─────────────────────┐
│  LLM (Hermes)        │  ← генерирует текст поста
│  (встроен в skill)   │
└─────────┬───────────┘
          │ raw post
          ▼
┌─────────────────────┐
│  critic.py           │  ← 6 категорий: hook, structure,
│  critique()          │     clarity, engagement, length, formatting
│                      │     оценка 0-10, severity: critical/warning/suggestion
└─────────┬───────────┘
          │ CritiqueReport
          ▼
┌─────────────────────┐
│  style_expert.py     │  ← adapt_for_telegram()
│  (опционально)       │     эмодзи, тире, кавычки
└─────────┬───────────┘
          │ styled post
          ▼
┌─────────────────────┐
│  hashtag_expert.py   │  ← select_hashtags()
│  (опционально)       │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  post_saver.py       │  ← save_post()
│                      │     output/post_*.txt + post_*.json
└─────────────────────┘
```

## Obsidian Save Format

Файлы сохраняются в `Brain/notes/content/YYYY-MM-DD-topics.md`.

Frontmatter:
```yaml
---
date: 2026-07-28
projects: [hermes-agent, kafka-test-trainer, pokemon-vocab]
events_count: 17
topics_count: 5
tags: [Git, GitHub, Hermes Agent, Kafka, LLM]
---
```

Таблица тем (для быстрого обзора в Obsidian):
```markdown
| # | Тема | Тон | Сложность | Статус |
|---|------|-----|-----------|--------|
| 1 | **Kafka в тестировании** | обучающий | 🟢 новичок | ⬜ todo |
```

Каждая тема раскрыта в отдельной секции `## N. Title` с полями:
- Угол, тон, сложность, статус
- Ключевые моменты (bullet list)
- События-источники (ссылки на строки dev journal)

## Key Design Decisions

1. **Rule-based vs LLM**: rule-based (`suggest_topics_rule_based`) работает мгновенно и бесплатно — хорошо для быстрых идей. LLM-based (`build_suggestion_prompt`) даёт более качественные и оригинальные темы.

2. **Obsidian как хаб**: темы сохраняются в Obsidian, а не в content-factory/output/, потому что:
   - Obsidian уже используется как база знаний
   - Темы видны в графе связей
   - Можно linking на проекты и заметки
   - Чекбоксы позволяют трекать прогресс

3. **Hermes как LLM**: skill `vibe-coding-blogger` инструктирует Hermes САМОМУ генерировать пост, а не просить пользователя копировать промпт в ChatGPT. Это устраняет главное узкое место оригинального content-factory.

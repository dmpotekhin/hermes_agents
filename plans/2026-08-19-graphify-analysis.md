# Анализ: Graphify-Labs/graphify — полезно ли пользователю

Дата: 2026-08-19
Источник: клон /tmp/graphify-research (main), README.md (60 КБ), ARCHITECTURE.md, graphify/llm.py

## Что это
Graphify — построитель knowledge graph из любых файлов (код, markdown, PDF,
изображения): сканирует директорию, извлекает сущности и связи, кластеризует
(Leiden), выдаёт интерактивный граф (graph.html), Obsidian-vault, wiki,
graph.json, отчёт с «god nodes» и неожиданными связями. Заявлено 71.5x меньше
токенов на запрос vs чтение сырых файлов.

## Архитектура (кратко)
- Claude Code skill + Python-библиотека standalone (CLI `graphify`)
- Pipeline: detect → extract → build (NetworkX) → cluster (Leiden/graspologic) →
  analyze → report → export (json/html/obsidian/svg/graphml/cypher/wiki/MCP)
- Извлечение кода: tree-sitter AST + call-graph — БЕЗ LLM, локально, бесплатно
- Извлечение .md/.pdf/изображений: через LLM-бэкенд (концепты + связи)
- Кэш SHA256 — повторный прогон только изменённых файлов

## LLM-бэкенды (graphify/llm.py BACKENDS)
- claude: ANTHROPIC_BASE_URL (можно LiteLLM/прокси), default claude-sonnet-4-6
- openai: OPENAI_BASE_URL (любой OpenAI-совместимый: llama.cpp, vLLM, LM Studio)
- kimi: Moonshot kimi-k2.6 (multimodal, OpenAI-совместимый, дёшево)
- gemini: Google OpenAI-совместимый endpoint
- ollama: локально, бесплатно, qwen2.5-coder:7b

## Применимость к пользователю
- Стек пользователя: Hermes (не Claude Code), deepseek-ключи, Obsidian Brain
  (vault), проекты: QA Interview Trainer, content-factory, agile-oracle,
  Telegram-бот ассистент, парсеры Ozon/WB
- graphify работает standalone: CLI + MCP server — интеграция с Hermes возможна
  (MCP stdio), даже без Claude Code
- deepseek: бэкенд openai с OPENAI_BASE_URL=https://api.deepseek.com/v1 +
  OPENAI_MODEL=deepseek-chat должен работать для текста/кода (OpenAI-совместимый
  API). НЕ работает для изображений (deepseek не multimodal) — картинки только
  через kimi/gemini/claude/ollama-мультимодал
- Код без LLM вообще: AST-граф бесплатно и быстро — основной профит для его
  кодовых баз
- Obsidian: экспорт в Obsidian vault из коробки; его Brain — уже memory layer,
  частичное дублирование, но graphify даёт связи, которых в Brain может не быть

## Gaps и риски
- Основная дока — под Claude Code; standalone-путь требует чтения cli.py
- Установка: pip install graphifyy (PyPI) — сеть к PyPI обычно ок
- LLM-извлечение .md: deepseek через openai-бэкенд не проверен (надо тест)
- Vision (картинки) с deepseek не работает
- Тяжёлый: 17 tree-sitter языков, networkx, graspologic

## Рекомендация
ДА, полезно. Сценарии:
1. Граф кодовых баз (AST, без LLM) — QA Trainer / content-factory / agile-oracle
2. Граф Brain/notes (Obsidian-экспорт) — найти скрытые связи заметок
3. MCP server → подключить к Hermes
Порядок: pip install graphifyy → graphify . на проекте → проверить AST-граф →
если нужно LLM-извлечение .md — настроить бэкенд (deepseek openai-compat или
ollama). Vision-часть пропустить (дорого/не поддерживается текущим стеком).

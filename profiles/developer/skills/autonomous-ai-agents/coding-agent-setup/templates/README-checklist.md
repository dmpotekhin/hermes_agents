# Work AI Setup — DeepSeek 4 Flash (100K) для вайбкодинга автотестов

Готовый пакет настроек для OpenCode / KiloCode + graphify.
Копируй нужное в проект автотестов, подставь свой base_url и ключ.

## Содержимое

| Файл | Для чего |
|------|----------|
| `opencode.json` | OpenCode: провайдер DeepSeek 4 Flash, лимиты 100K, компакция, инструкции |
| `kilo.jsonc` | KiloCode: подключение AGENTS.md + правил |
| `AGENTS.md` | Память проекта: правила вайбкодинга Java-автотестов (JUnit 5, Maven/Gradle, Testcontainers), TDD, граф зависимостей |
| `graphify.sh` | Прогон графа зависимостей (один раз + после больших изменений) |

## 1. OpenCode

### Установка
```bash
curl -fsSL https://opencode.ai/install | bash
# или
npm install -g opencode-ai
```

### Настройка
1. Скопируй `opencode.json` в корень проекта.
2. Вставь свой `baseURL` (корпоративный OpenAI-совместимый шлюз
   или `https://api.deepseek.com/v1`) и `apiKey`.
3. Запусти `opencode`. В TUI проверь: `/models` → `deepseek/deepseek-v4-flash`.

### Как не терять контекст
- Компакция в конфиге (`compaction.auto: true`, `reserved: 20000`).
- `small_model` = та же flash — титулы и обзоры не жрут контекст.
- `instructions: ["./AGENTS.md"]` — память проекта в каждой сессии.
- `/status` >70K → «кратко суммируй прогресс в AGENTS.md → перезапусти сессию».

## 2. KiloCode

### Установка
```bash
code --install-extension kilocode.kilo-code
# или CLI
npm install -g @kilocode/cli && kilo
```

### Провайдер (DeepSeek)
UI: Settings → Providers → DeepSeek (вставь ключ).
Корпоративный шлюз: Providers → OpenAI Compatible → baseURL + ключ.

### Правила
1. Скопируй `kilo.jsonc` в корень проекта — подключит `AGENTS.md` и `.kilo/rules/*.md`.
2. Контекст конденсится АВТОМАТИЧЕСКИ (~80K при 100K модели).

## 3. Graphify — граф зависимостей

```bash
./graphify.sh /path/to/project        # чистый граф, без LLM (Java — tree-sitter)
~/Library/Python/3.11/bin/graphify label /path/to/project --backend deepseek  # именование кластеров
```

Результат: `graphify-out/GRAPH_REPORT.md` + `graph.html` (интерактивный).
Для Java видит классы/методы в `src/main` и `src/test`.

## 4. Быстрый старт (чеклист)

1. [ ] `opencode.json` или `kilo.jsonc` + `AGENTS.md` скопированы в проект
2. [ ] baseURL/apiKey подставлены
3. [ ] `./graphify.sh <проект>` прогнан, граф в `graphify-out/`
4. [ ] Открыт агент, модель = `deepseek-v4-flash`
5. [ ] Первая команда: «Прочитай AGENTS.md и graphify-out/GRAPH_REPORT.md»

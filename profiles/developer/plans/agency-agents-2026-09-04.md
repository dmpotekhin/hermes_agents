# Agency Agents — оценка и как использовать (Hermes developer profile)

Дата: 2026-09-04 · Репозиторий: msitarzewski/agency-agents (MIT)

## Что это
«The Agency» — каталог из ~273 готовых AI-агентов-«специалистов» (18 дивизионов:
engineering, design, product, testing, security, marketing, finance, gis, ...).
Каждый — .md с frontmatter (name, description, emoji, vibe) и телом: Identity/Memory,
Core Mission, Critical Rules, Deliverables, Success metrics. Это **персонные промпты**
(как мыслит/пишет/что сдаёт), НЕ код и НЕ новый доступ к инструментам. Плюс скрипты
convert.sh / install.sh, которые конвертируют их в форматы ~16 инструментов, включая
**Hermes** (формат `hermes-router-plugin`).

## Почему интересно именно нам
- У нас активный профиль **developer**, и **HERMES_HOME уже = ~/.hermes/profiles/developer** —
  стандартный инсталлер кладёт плагин в правильный профиль без правок.
- Интеграция Hermes — **ленивый роутер-плагин** `agency-agents-router`:
  при старте у Hermes 4 тула, а весь ростер (~273) лежит в `data/agents.json` и
  грузится по запросу. **НЕ** добавляется в `skills.external_dirs` → нет раздувания контекста.
- Тулы: `agency_agents_search`, `agency_agents_inspect`, `agency_agents_load`,
  `agency_agents_delegate` (делегирует через нативный `delegate_task`).

## Синергия с текущими целями
- **Экономия токенов**: `delegate_task`/subagent в ~15x дешевле интерактивных cli-сессий —
  рутинное/тяжёлое исследование можно свитчить на «специалиста» через роутер.
- **Качество процесса**: персона-агенты задают дисциплину (чеклисты, форматы, дефайны) —
  это дополняет наши скиллы, а не дублирует их.

## Конкретные сценарии для наших проектов
1. **QA Interview Trainer** (FastAPI+React) — `software-architect`/`backend-architect`
   для архитектуры; `code-reviewer` перед коммитами; `qa-engineer`/`testing` для тестов.
2. **Travel map** (MapLibre статик) — `frontend-developer` для UI, gis-специалисты.
3. **Content Factory / блог** — specialized-агенты, `prompt-engineer`.

## Установка (в активный профиль developer)
```bash
cd /tmp && git clone --depth 1 https://github.com/msitarzewski/agency-agents aa
cd aa
./scripts/convert.sh --tool hermes     # сгенерить integrations/hermes + data/agents.json
./scripts/install.sh --tool hermes     # скопировать в ${HERMES_HOME}/plugins/agency-agents-router + включить в config
```
Перезапустить Hermes / новую сессию — плагин и его тул-схемы подгрузятся.

## Как юзать в сессии
Просто естественным языком: «поищи в agency software-architect и загрузи для этой задачи»,
«заделегируй code-reviewer на этот diff». Желательно в проект положить инструкцию
(см. integrations/hermes/README.md): держать роутинг ленивым, не предзагружать весь ростер.

## Риски / нюансы
- opencode-баг (отсекает >119 агентов) — для нас неактуален (мы Hermes).
- Персона-агент = промпт-процесс, а не новые возможности; не ждать магии от того,
  чего нет в текущем toolset.
- Периодически тянуть свежий репо (ротер регистрируется с актуальными схемами).

## Вердикт
Adopt (для разработчика профиля). Полезно как «виртуальная команда экспертизы» поверх
наших скиллов, с ленивой загрузкой и без бюджетного раздувания. Установить при желании.

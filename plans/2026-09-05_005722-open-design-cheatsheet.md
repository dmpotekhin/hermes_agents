# План: конспект-шпаргалка по OpenDesign + интеграция с Hermes

**Дата:** 2026-09-05 · **Класс:** документационная задача (research + идея), TDD не применяется · **Язык материала:** русский

## Goal

Собрать из официальных источников (репозиторий `github.com/nexu-io/open-design` + сайты `opendesigner.io`/`open-design.ai` + страница сравнения с Pencil) и сохранить в Obsidian русскоязычную шпаргалку по **OpenDesign** с отдельным разделом **«Интеграция с Hermes»**. Без выдумки: каждый факт — со ссылкой на источник.

## Current context / assumptions

- **OpenDesign** — open-source (Apache-2.0), **local-first** альтернатива Claude Design. Твой **кодинг-агент становится движком дизайна**: прототипы, лендинги, дашборды, слайды, изображения, видео — как **реальные файлы** (экспорт HTML/PDF/PPTX/MP4).
- **BYOK (bring your own key):** использует тот кодинг-агент CLI, что уже есть на PATH, или любой OpenAI-совместимый ключ через BYOK-прокси. **17–21 адаптер из коробки** — среди них: Claude Code, Codex CLI, Cursor, Gemini CLI, OpenCode, Qwen, **Hermes**, DeepSeek, GitHub Copilot CLI, Grok, Kimi, Devin for Terminal, Qoder, Kilo, Mistral Vibe, Kiro, Aider, Antigravity, Reasonix, Pi, Trae CLI, OpenCode.
- **Ссылки-источники (уже подтверждены поиском):**
  - Репо: `https://github.com/nexu-io/open-design`
  - Сайты: `https://opendesigner.io/` (21 адаптер, есть Hermes), `https://open-design.ai/` (17 адаптеров, есть Hermes)
  - Сравнение с Pencil: `https://open-design.ai/alternatives/pencil-dev/`
  - Обзор: `https://www.neura.market/news/open-design-open-source-claude-design-alternative`
- **Ключевой вывод для пользователя:** в отличие от pen.dev (Hermes не в списке, пришлось городить CLI-обход), **OpenDesign поддерживает Hermes напрямую как BYOK-адаптер** — отсюда сессионный вопрос «можно ли с Hermes» закрыт сразу в разделе «Интеграция с Hermes».
- **Выходной файл:** `/Users/dmitrypotekhin/Odsidian/obsidians/Obsidian Vault/Brain/notes/skills/open-design.md` (сосед `pen-dev.md` — консистентное место в `notes/skills/`).
- **Питфол имени:** «Open Design» — многозначный термин (есть дизайн-движение/другие проекты). В шпаргалке зафиксировать, о каком продукте речь (nexu-io/open-design), и не путать с pen.dev/Pencil и с «Claude Design».
- **Питфол источника (наследие pen.dev):** корневые страницы могут блокироваться `web_extract` («private/internal network address») — рабочий обход: фетчить конкретные URL, при блоке — `curl` + парсинг SSR-HTML (Nextra/Next) или `raw.githubusercontent.com/.../README.md`.

## Architecture / proposed approach

Research + документирование (не код). Подход: (1) снять README репозитория и ключевые страницы сайтов + страницу сравнения; (2) при блокировке — `curl` raw README / SSR-парсинг; (3) собрать сырой текст в `/tmp/open_design_raw/`; (4) написать шпаргалку в Obsidian по фиксированной структуре, с разделом «Интеграция с Hermes»; (5) верифицировать полноту/источники/отсутствие заглушек. Каждый раздел — самодостаточный, с минимум одной рабочей ссылкой.

## Step-by-step tasks

### T1. Снять README репозитория (источник №1)

`web_extract(["https://github.com/nexu-io/open-design"])` → сохранить в `/tmp/open_design_raw/repo.md`.
Ожидаемо: описание, лицензия Apache-2.0, **команда установки** (по обзору — `pnpm tools-dev`; уточнить по README), список BYOK-адаптеров, что умеет, экспорт.
> Запасной вариант при блоке: `curl -s https://raw.githubusercontent.com/nexu-io/open-design/main/README.md` → в `/tmp/open_design_raw/repo.md` (README обычно валидный markdown).

### T2. Снять сайты позиционирования

`web_extract` пачкой:
- `https://opendesigner.io/`
- `https://open-design.ai/`

Сохранить в `/tmp/open_design_raw/sites.md`.
Ожидаемо: позиционирование «open-source alternative to Claude Design», упоминание Hermes в списке адаптеров, local-first, BYOK, экспорт HTML/PDF/PPTX/MP4.
> Заметка: на двух доменах **разное число адаптеров** (17 vs 21) — в шпаргалке цитировать оба с пометкой «по сайту X — 21, по сайту Y — 17», не выдумывать единое число.

### T3. Снять страницу сравнения с Pencil (источник «сравнение с Pencil здесь»)

`web_extract(["https://open-design.ai/alternatives/pencil-dev/"])` → в `/tmp/open_design_raw/pencil-compare.md`.
Ожидаемо: честное сравнение OpenDesign vs Pencil (pen.dev) — архитектура, lock-in, экспорт, локальность, BYOK. Это ляжет в раздел «Сравнение», с пометкой «(по странице сравнения)».

### T4. Снять обзор (доп.)

`web_extract(["https://www.neura.market/news/open-design-open-source-claude-design-alternative"])` → в `/tmp/open_design_raw/review.md`.
Ожидаемо: «local-first и web-deployable, BYOK на каждом слое, `pnpm tools-dev`» — вторичный источник; помечать «(обзор)».

### T5. Написать шпаргалку в Obsidian

`write_file` → `/Users/dmitrypotekhin/Odsidian/obsidians/Obsidian Vault/Brain/notes/skills/open-design.md`. Структура (каждый блок, где уместно, со ссылкой-источником):

1. **Что это** — одно предложение: «OpenDesign — open-source (Apache-2.0) локальная альтернатива Claude Design: твой кодинг-агент (Claude Code, Codex, Cursor, **Hermes** и ещё ~20) становится движком дизайна и создаёт прототипы/лендинги/дашборды/слайды/видео как реальные файлы (HTML/PDF/PPTX/MP4).»
2. **Почему не Figma / не pen.dev(Pencil)** — файлы в репозитории; BYOK; local-first; не проприетарный агент.
3. **Установка / запуск** — точная команда из README (ожидаемо `pnpm tools-dev`, клонировать репо, установить зависимости), как запустить локально, BYOK-конфиг.
4. **BYOK-адаптеры** — 17–21 CLI (обе цифры с пометкой источника), выделить Hermes/Claude Code/Codex/Cursor/Gemini/OpenCode/Qwen.
5. **Возможности** — прототипы, лендинги, дашборды, слайды, изображения, видео; экспорт HTML/PDF/PPTX/MP4.
6. **Агент-нативный цикл** — discover the brief → lock the direction → stream the artifact → critique → deliver (из описания репо).
7. **Интеграция с Hermes** — как указать Hermes в качестве агента (BYOK-адаптер / OpenAI-совместимый эндпоинт). ⭐ Ключевой раздел по запросу пользователя.
8. **Сравнение OpenDesign vs pen.dev(Pencil)** — с пометкой «(по странице сравнения)».
9. **Питфолы / ограничения** — неоднозначность имени; реальный продукт `nexu-io/open-design`; BYOK → нужен свой ключ/агент; число адаптеров разнится; всё local-first (свои данные локально).
10. **Ссылки** — все использованные URL.

Правила: факты только из собранного; вторичные источники помечать «(обзор)»; не писать то, чего нет в источниках; при расхождении чисел — цитировать оба.

### T6. Верификация (не тесты — команды на полноту/источники/чистоту)

Terminal:
```bash
F="/Users/dmitrypotekhin/Odsidian/obsidians/Obsidian Vault/Brain/notes/skills/open-design.md"
test -f "$F" && echo "OK: file exists" || echo "FAIL: no file"
echo "urls=$(grep -oE 'https?://[^) ]+' "$F" | sort -u | wc -l)"
grep -iE "TODO|TBD|заглушк|PLACEHOLDER|FIXME" "$F" && echo "FAIL: placeholders" || echo "OK: no placeholders"
grep -qi "Apache-2.0" "$F" && echo "OK: license" || echo "WARN: no license"
grep -qiE "BYOK|bring your own key" "$F" && echo "OK: BYOK mention" || echo "WARN: no BYOK"
grep -qi "Hermes" "$F" && echo "OK: Hermes integration section" || echo "WARN: no Hermes"
grep -qiE "Pencil|pen.dev" "$F" && echo "OK: Pencil comparison" || echo "WARN: no Pencil comparison"
```
Ожидаемо: `OK: file exists`; `urls` ≥ 8; `OK: no placeholders`; `OK: license`; `OK: BYOK mention`; `OK: Hermes integration section`; `OK: Pencil comparison`.

## Risks, tradeoffs, and open questions

- **Блокировка источников** (github/сайты через `web_extract`) → обход: `curl` raw README / SSR-парсинг (как с pen.dev).
- **Точная команда установки** (ожидаемо `pnpm tools-dev`) и **как именно указывается Hermes-адаптер** — требует реального README/док на этапе выполнения; НЕ выдумывать. В шпаргалке оставить точную команду только из фактически прочитанного источника.
- **Расхождение числа адаптеров** (17 vs 21) — цитировать оба домена, не усреднять.
- **BYOK-зависимость:** нужен свой ключ/агент — бесплатность «кода», но платишь за токены своего провайдера (или используешь локальную модель).
- **Неоднозначность «Open Design»** — зафиксировать `nexu-io/open-design`, предупредить о путанице.
- **Открытый вопрос:** OpenDesign частично использует «твой агент» (Hermes/Claude и т.д.) — интеграция сводится к указанию агента, а не к прокси на проприетарную модель (в отличие от pen.dev, где агент — Claude). Подтвердить на этапе выполнения.
- **Классификация:** документационная задача; TDD неприменим — вместо тестов верификация T6.

## Примечание по статусу

Это план (plan mode) — реализация НЕ начата. Файл-шпаргалка на диске ещё не создан. После подтверждения («да») — последовательность T1…T6 (можно делегировать фетч+драфт субагенту, верификацию делать лично).

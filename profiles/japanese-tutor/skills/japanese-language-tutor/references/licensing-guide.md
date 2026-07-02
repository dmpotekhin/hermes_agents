# ⚖️ Лицензирование проектов с данными KanjiVG

Создан 2026-07-02 — разбор по запросу пользователя о публикации кандзи-тренажёра на GitHub.

## Источник данных

- **KanjiVG** — https://github.com/KanjiVG/kanjivg
- **Лицензия:** [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)
- **Автор:** Ulrich Apel
- **Покрытие:** ~13,000 SVG (все Jōyō + Jinmeiyō + дополнительные)
- **Формат:** SVG с `<path>` по чертам (kvg:XXXXX-sN), сортировка по номеру черты

## Что можно делать с данными KanjiVG

| Действие | Разрешено? |
|----------|-----------|
| Копировать данные в свой репозиторий | ✅ Да |
| Модифицировать, перерабатывать | ✅ Да |
| Использовать коммерчески | ✅ Да |
| Распространять | ✅ Да |

## Обязательные условия

### 1. Attribution (BY) — указать авторство

В README.md проекта обязательно добавить:

```markdown
## 📚 Данные

Данные о порядке написания иероглифов (stroke order data) взяты из проекта:

- **KanjiVG** — https://github.com/KanjiVG/kanjivg  
  Лицензия: [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)  
  Автор: Ulrich Apel

Изменения, внесённые в данные: [кратко описать, что сделали — извлекли точки, переформатировали и т.д.]
```

### 2. ShareAlike (SA) — та же лицензия

Если данные **лежат в репозитории** (не submodule), весь репозиторий — производная работа → должен быть под CC BY-SA 3.0.

Положить файл `LICENSE` в корень:

```text
Attribution-ShareAlike 3.0 Unported (CC BY-SA 3.0)

Copyright (C) 2026 Dmitry Potekhin

This work is licensed under the Creative Commons Attribution-ShareAlike 3.0
Unported License. To view a copy of this license, visit
http://creativecommons.org/licenses/by-sa/3.0/ or send a letter to
Creative Commons, PO Box 1866, Mountain View, CA 94042, USA.
```

Полный текст: https://creativecommons.org/licenses/by-sa/3.0/legalcode

## Альтернатива: разделение кода и данных

Если **код** хотите под другой лицензией (MIT, Apache), а данные оставить с CC BY-SA:

```
ваш-репозиторий/
├── kanji-practice/       ← код (MIT / Apache)
└── data/                 ← git submodule на kanjivg (оригинальная CC BY-SA)
```

Тогда:
- Скрипт — под любой лицензией
- Данные — в оригинальном репозитории KanjiVG
- Ваш код просто читает SVG из submodule

## Если лицензия не указана в источнике

По умолчанию на GitHub — **All Rights Reserved**. Не копировать данные без явной лицензии.
Вместо этого:
- Сделать скрипт-парсер, который загружает данные по URL (без копирования в репозиторий)
- Использовать только данные, введённые вручную
- Добавить источник как git submodule

## Когда нужна эта информация

- Пользователь говорит «хочу выложить на GitHub» про скрипт/тренажёр
- Пользователь спрашивает «законно ли использовать KanjiVG» / «какую лицензию ставить»
- Пользователь просит создать LICENSE файл
- Пользователь просит добавить attribution в README

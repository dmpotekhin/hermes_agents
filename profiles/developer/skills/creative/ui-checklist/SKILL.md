---
name: ui-checklist
description: Quality checklist for any UI before shipping it.
author: Dmitry Potekhin (dmitrypotekhin), Hermes Agent
license: MIT
version: 0.1.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [ui, review, checklist, frontend]
    related_skills: [ui-foundations, ui-components, ui-animations, static-site-maintenance]
---

# UI Quality Checklist

## When to Use

После верстки/правок интерфейса — обязательный review перед сдачей.

## Внешний стандарт

Пройди фронт по **designsystemchecklist.com** (цвета, типографика, состояния,
доступность, документация). Скармливай его как рамку качества.

## Быстрый чеклист

### Визуал / анти-слоп
- [ ] Нет дефолтного индиго/фиолетового градиента без причины.
- [ ] Палитра выбрана осознанно (см. `ui-foundations`).
- [ ] Шрифт выбран под тон, а не «Inter по инерции».
- [ ] Все цвета/отступы/радиусы — через токены, без хардкода.

### Компоненты
- [ ] База — shadcn/ui, стили приведены к общим токенам.
- [ ] Есть состояния: hover, focus-visible, disabled, loading, empty, error.
- [ ] Для ИИ-UI: стриминг, стоп-генерация, подтверждение действий, обработка ошибок.

### Анимации
- [ ] Анимации < 300 мс.
- [ ] Частые действия не анимированы.
- [ ] Учтён `prefers-reduced-motion`.

### Доступность
- [ ] Контраст текста ≥ 4.5:1 (крупный ≥ 3:1).
- [ ] Фокус виден с клавиатуры, порядок табов логичен.
- [ ] У иконок-кнопок есть aria-label, у форм — label.
- [ ] Адаптив: мобильный, планшет, десктоп.

### Консистентность
- [ ] Единая шкала отступов и типографики по всему проекту.
- [ ] Одинаковые компоненты выглядят одинаково на разных экранах.

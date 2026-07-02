# Система ежедневных уроков (cron + Telegram)

## Общая схема

```
study_plan.json  ──►  daily_lesson.py  ──►  cron job  ──►  Telegram
(30 дней, N5)        (определяет день,        (hermes cronjob,
                      генерирует урок)         schedule='0 20 * * *')
```

## Файлы

| Файл | Назначение |
|------|-----------|
| `~/.hermes/jp_rag_data/study_plan.json` | План на 30 дней: day, title, pattern IDs, topic |
| `~/.hermes/jp_rag_data/daily_lesson.py` | Генератор урока: определяет день → читает JSONL → выводит сообщение |
| `~/.hermes/jp_rag_data/study_progress.json` | Состояние (создаётся автоматически) |

## Как это работает

### study_plan.json

Структура одного дня:
```json
{
  "day": 1,
  "patterns": ["n5_0001", "n5_0002"],
  "title": "Частицы の и は",
  "topic": "particles"
}
```

- topic='review' — день повторения (генерирует список паттернов из последних 4 дней)
- topic='final' — финальный тест (10 случайных паттернов из всего N5)
- patterns=[] — для review/final дней
- start_date — дата первого дня (ученик начал)

### daily_lesson.py

- `get_current_day(start_date)` — вычисляет день плана от start_date до сегодня
- Для review days: собирает паттерны из предыдущих 4 дней
- Для regular days: читает patterns.jsonl по ID, форматирует вывод
- Для final: выбирает 10 случайных паттернов как вопросы

Формат урока:
```
🇯🇵 JLPT N5 — День N/30
📌 Тема
⏱ Время: ~30-60 минут

Прогресс: ████░░░░░░░ XX%

━━━ Pattern Title ━━━
🔧 Формула: ...
📖 Объяснение: ...

🇯🇵 Примеры:
  (1)私の名前はテイラーです。
   Чтение: わたしのなまえはていらーです。
   Перевод: My name is Taylor.

📝 Новые слова:
  私 (わたし) — I

━━━ Практика ━━━
1. Прочитай вслух 5-7 раз
2. Закрой японский — переведи с русского
3. Составь своё предложение
4. Запиши в тетрадь
```

### Cron job

Создание:
```bash
hermes cronjob create \
  --name n5-daily-lesson \
  --schedule '0 20 * * *' \
  --deliver telegram:222651048 \
  --prompt 'Запусти python3 ~/.hermes/jp_rag_data/daily_lesson.py и выведи результат'
```

**Важно:** `--deliver telegram` без указания chat_id (например `telegram:222651048`) **НЕ сработает** — появится ошибка `no delivery target resolved for deliver=telegram`. Всегда указывайте числовой Telegram ID пользователя.

Параметры:
- `--schedule '0 20 * * *'` — каждый день в 20:00 по локальному времени (система в MSK)
- `--deliver telegram` — доставка в Telegram (allowed_chat из конфига профиля)
- `--deliver origin` — доставка в текущий чат CLI (если Telegram недоступен)

Просмотр/управление:
```bash
hermes cronjob list
hermes cronjob update <job_id> --schedule '0 21 * * *'
hermes cronjob remove <job_id>
```

## Известные проблемы

### Расписание cron сбито (не 20:00, а другое время)

Симптом: урок приходит не в то время или вообще не приходит.

Проверять `hermes cronjob list` — смотреть поле `schedule`. Корректное значение — `0 20 * * *` (20:00 MSK ежедневно). Если там `30 20 * * *` (20:30) или другое — исправить:

```bash
hermes cronjob update <job_id> --schedule '0 20 * * *'
```

**Рекомендация:** после создания cron-задачи всегда проверять `hermes cronjob list` и убеждаться, что `schedule` и `deliver` корректны.

### Telegram API недоступен

Симптом: gateway.log показывает `connection failed` для api.telegram.org и всех fallback IP (149.154.166.110).
Решение: переключить cron на `--deliver origin` (сообщение придёт в CLI-сессию).
При восстановлении соединения — переключить обратно на `--deliver telegram`.

### "no delivery target resolved for deliver=telegram"

Симптом: cron job **выполнился успешно**, но лог показывает:
```
WARNING cron.scheduler: Job '<id>': no delivery target resolved for deliver=telegram
```

**Когда возникает:** deliver указан как `telegram` без chat_id.

**Простой фикс (1 шаг):**
Обновить deliver у существующей cron-задачи на chat_id:

```bash
hermes cronjob update <job_id> --deliver telegram:222651048
```

После этого следующий запланированный запуск доставит урок в Telegram напрямую.

**Если это не помогает (после перезапуска gateway):**
1. Самый быстрый способ — запустить скрипт напрямую в CLI:
   ```bash
   python3 ~/.hermes/jp_rag_data/daily_lesson.py
   ```
2. Дождаться следующего cron-тика (на следующий день в 20:00) — обычно отрабатывает нормально, так как gateway успевает зарегистрироваться.
3. При необходимости — полная перезагрузка gateway с удалением gateway_state.json:
   - `ps aux | grep "hermes.*gateway" | grep -v grep` — проверить PID
   - Остановить gateway штатно
   - `rm -f ~/.hermes/profiles/japanese-tutor/gateway_state.json`
   - Запустить gateway заново
   - Дождаться `✓ telegram connected` в логах
   - Запустить cron вручную

### Gateway нужно перезапустить после восстановления сети

Если Telegram перестал отвечать, а потом соединение появилось:
1. Убить старый процесс: `kill <PID>` или через `process(action='kill', session_id=...)`
2. Запустить заново: `hermes gateway run --profile japanese-tutor` (в фоне через background=true)
3. Проверить: `hermes gateway status`

### Смещение дня из-за ручных уроков (skip-on-the-fly)

Когда пользователь попросил провести урок вне cron-расписания (Подход A в SKILL.md), скрипт **не знает** об этом и продолжает считать дни от start_date. Через 1-2 ручных урока day из скрипта перестаёт соответствовать реальному прогрессу.

**Симптом:** пользователь говорит «мы вчера прошли день 4» (вручную), а скрипт показывает «День 3 — Review».

**Решение:** всегда сверять актуальный прогресс через `session_search` перед началом ручного урока, а не полагаться на вывод `daily_lesson.py`. Для получения содержимого паттернов используй прямой grep по JSONL.

### Скрипт выдаёт "День N не найден в плане"

Проверить start_date в study_plan.json — если сегодняшняя дата раньше start_date, день будет 0 или отрицательный.

## Реструктуризация плана (слияние дней)

Когда ученик просит ускориться и объединить несколько уроков в один:

### Порядок действий

1. **Посмотреть содержимое объединяемых дней** — какие паттерны (ID), сколько всего. Показать ученику, что будет в объединённом уроке.
2. **Обновить study_plan.json через Python:**
   ```python
   import json
   with open('study_plan.json') as f:
       plan = json.load(f)
   
   # Собрать новый массив days вручную
   new_days = []
   new_days.append(plan['days'][0])  # День 1 — без изменений
   
   # Объединённый день
   merged = {
       "day": 2,
       "patterns": ["n5_0003", "n5_0004", "n5_0005", ...],  # все ID из объединяемых дней
       "title": "Новое название",
       "topic": "новая-тема"
   }
   new_days.append(merged)
   
   # Если между объединяемыми днями был review — переименовать
   # и перенумеровать
   for i, old_day in enumerate(plan['days'][old_index:], start=new_index):
       d = dict(old_day)
       d['day'] = i
       new_days.append(d)
   
   plan['days'] = new_days
   with open('study_plan.json', 'w', encoding='utf-8') as f:
       json.dump(plan, f, ensure_ascii=False, indent=2)
   ```
3. **Сбросить прогресс:**
   ```python
   with open('study_progress.json', 'w') as f:
       json.dump({"completed_days": []}, f)
   ```
4. **Проверить результат:** распечатать первые 3 и последние 2 дня плана.
5. **Cron не трогать** — он сам подхватит новый план на следующем тике.

### Когда применяется

- Ученик говорит «это для меня легко» / «давай ещё»
- Паттерны логически связаны (например, все про вопросы или все про существование)
- Не предлагать самому — только по запросу ученика

### Пример (сделан 2026-06-17)

- Дни 2 (だ/です+か) + 3 (вопросы) + 4 (ある/いる+ではない) → один День 2 с 7 паттернами
- Старый review (День 5) стал Днём 3
- Общее число дней: 30 → 28
- Последующие дни перенумерованы 6→4, 7→5, ..., 30→28

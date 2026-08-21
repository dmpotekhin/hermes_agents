---
name: security-remediation
description: "Fix and verify security findings after a scan or review."
---

# Security Remediation

После того как security-review / Strix / bandit / semgrep нашёл уязвимости — устранить и доказать, что они закрыты. Парный скилл к `security-review` (тот аудирует diff, этот чинит и верифицирует).

## Порядок

1. **Разберись в реальной защите, а не только в патче.** Для SQLi чёрный список ключевых слов — НЕ защита. Реальная защита: read-only транзакция + не-суперпользовательская роль БД (иначе `COPY ... TO PROGRAM` / `pg_read_file` / `pg_ls_dir` дают RCE на хосте БД). Валидатор «один SELECT/WITH» — defence-in-depth, а не основная линия обороны.
2. **Обнови уязвимые зависимости (SCA).** Сначала проверь последние версии и peer-deps, потом бампь (см. секцию SCA ниже).
3. **Commit** после credential-scan: `python3 ~/.hermes/profiles/developer/tools/scan_credentials.py --staged`.
4. **Проверь живыми endpoint-тестами** (см. Verification).

## Verification (живые endpoint-тесты)

Тест-сьюта обычно нет — тогда подними сервис и гони ad-hoc endpoint-тесты. Паттерн: attack-payload (ожидай 4xx/отказ) + legit-payload (ожидай 200/успех), ассерти HTTP-код и тело:

```bash
# attack — должен отклонить (400/403)
curl -s -m 10 -o /dev/null -w "%{http_code}" -X POST "$BASE/api/sql/check" \
  -H 'Content-Type: application/json' -d '{"query":"SELECT pg_read_file(...)"}'
# legit — должен работать (200 + ожидаемое тело)
curl -s -m 10 -X POST "$BASE/api/sql/check" ...   # ждём "correct":true
```

Проверяй ВСЕ изменённые код-пути, не только уязвимый эндпоинт: легитимный сценарий не должен сломаться. Оформляй как временный скрипт в temp с префиксом `hermes-verify-`, прогони, покажи PASS/FAIL, подчисти.

## Pitfalls (все встречены на практике)

- **curl, а не Python urllib, для localhost-проверок.** В песочнице Hermes Python-скрипт (urllib или subprocess, стартующий сервер) может висеть на localhost без единого вывода, тогда как curl к тому же эндпоинту отвечает мгновенно. Если верификационный скрипт виснет без output — перепиши на curl/bash. Если Python обязателен — запускай `-u` (unbuffered), иначе `print` буферизуется в пайп и не видно, на каком шаге стоп.
- **`process(action=kill)` не гарантированно убивает дочерний сервер.** Фоновый `python3 -m uvicorn` может остаться сиротой и продолжать держать порт после kill сессии — следующий старт виснет на «Address already in use» или зависшем /health. После kill проверь порт: `lsof -i :PORT -sTCP:LISTEN`. Если жив — `kill -9 $(lsof -ti :PORT)`.
- **bandit B324 (MD5) блокирует commit** даже для легитимного MD5 (детерминированный выбор, не безопасность). Для не-секурного хеша помечай явно: `hashlib.md5(x, usedforsecurity=False)` (Python ≥3.9) — снимает bandit без `# nosec`.

## SCA — как бампить зависимости

- Версии: PyPI `https://pypi.org/pypi/<pkg>/json` → `info.version`; npm `https://registry.npmjs.org/<pkg>/latest` → `version`; peer-deps и транзитивные deps — `https://registry.npmjs.org/<pkg>/<ver>` → `peerDependencies`/`dependencies`.
- Мажорные бампы сверяй с peer-deps: напр. `@vitejs/plugin-react` матчится с мажорной версией vite (plugin-react 6 → vite ^8).
- Транзитивную уязвимость чинит бамп родителя: starlette (через FastAPI) → бампни fastapi; nanoid (через postcss) → бампни postcss (он тянет `nanoid ^3.3.17`, который уже вне уязвимого диапазона).
- Быстрый сигнал: `npm install` в конце печатает «found N vulnerabilities» — после бампа должно быть 0. Затем `npm run build` для проверки, что мажорный бамп не сломал сборку.
- pre-commit hook (gitleaks + bandit) может блокировать commit на bandit HIGH из-за pre-existing кода (см. pitfall про MD5).

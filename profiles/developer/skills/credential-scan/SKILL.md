---
name: credential-scan
description: "Use before git commit — scan staged files for leaked secrets"
version: 1.0.0
platforms: [macos, linux]
---

# Credential Scan

Сканирует staged-изменения на паттерны секретов ДО коммита.

Источник: Agentic OS (https://github.com/KbWen/agentic-os, MIT License).

## Когда использовать

- Перед ЛЮБЫМ `git commit` — обязательно
- Перед `git push` если коммит уже сделан без сканирования
- Для проверки конкретного файла: `python3 <tool> <file>`

## Использование

### Pre-commit (основной режим)

```bash
python3 ~/.hermes/profiles/developer/tools/scan_credentials.py --staged
```

Exit codes:
- `0` — чисто, можно коммитить
- `1` — найден секрет, коммит ЗАБЛОКИРОВАН
- `3` — сканер не смог запуститься (предупредить, но не блокировать)

### Проверка конкретного файла

```bash
python3 ~/.hermes/profiles/developer/tools/scan_credentials.py path/to/file.env
```

## Что ловит

- AWS Access Key IDs (`AKIA...`)
- GitHub токены (`ghp_...`, `github_pat_...`)
- OpenAI/DeepSeek ключи (`sk-...`)
- Slack токены (`xoxb-...`, etc.)
- Google API ключи (`AIza...`)
- PEM private keys (`-----BEGIN ... PRIVATE KEY-----`)

## Что НЕ ловит (by design)

- AWS *secret* access keys (40 символов, без отличительного префикса)
- Секреты разбитые на несколько строк
- Бинарные файлы
- Connection strings и JWT (ложные срабатывания)

## Обход (escape hatch)

Для документированных ПРИМЕРОВ токенов (не реальных секретов):

```
aws_access_key_id = AKIAIOSFODNN7EXAMPLE  # pragma: allowlist secret
```

## Pitfalls

- Сканер проверяет только ADDED строки в staged diff. Если секрет уже в истории — не поймает.
- `git commit --no-verify` обходит сканер. Использовать только осознанно.
- Если сканер выдал exit 3 (не смог запуститься) — не блокировать коммит, но предупредить.

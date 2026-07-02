---
name: hermes-backup
description: "Push Hermes Agent profiles, configs, skills, and data to a private GitHub repository — full setup with .gitignore, SSH auth, and JLPT data migration."
version: 1.1.0
author: agent
metadata:
  tags: [hermes, backup, git, github, profiles]
---

# Hermes Profile Backup to GitHub

Push all Hermes profile data to a private GitHub repository for backup and syncing across machines.

## Quick Start

```bash
cd ~/.hermes

# Init repo
git init
git branch -m main

# Add remote (SSH preferred — avoids credential prompts)
git remote add origin git@github.com:USERNAME/REPO.git

# Optional: add remote via HTTPS (will prompt for credentials)
git remote add origin https://github.com/USERNAME/REPO.git
```

## .gitignore (что НЕ должно попасть в репозиторий)

```gitignore
# Sensitive / secrets
.env
auth.json
nous_auth.json
channel_directory.json
gateway_state.json
gateway.lock

# Embedded git repos (hermes source code, plugins)
hermes-agent/
plugins/*/

# Large cache / DB
models_dev_cache.json
state.db
state.db-shm
state.db-wal
kanban.db

# Session history & logs
sessions/
logs/
*.log
*.history

# Caches
cache/
audio_cache/
image_cache/
sandboxes/
*.skills_prompt_snapshot.json
*models_cache.json
*_cache.json

# Personal memories
memories/

# Binaries
bin/

# Lock & temp files
*.lock
.clean_shutdown
.install_method
.update_check
*.pid
processes.json

# Config backups
config.yaml.bak*

# Pairing / pairing info
pairing/

# Pastes cache
pastes/

# Skills internal state
skills/.bundled_manifest
skills/.curator_*
skills/.usage.json

# Cron output (generated content)
**/cron/output/

# SOUL backups
SOUL.md.save

# Node / deps
node_modules/
```

## Важные особенности .gitignore

- **`**/cron/output/`** (с `**/`) — ловит вложенные пути типа `profiles/japanese-tutor/cron/output/`. Обычный `cron/output/` работает только на корневом уровне и НЕ ловит поддиректории.
- Шаблон `plugins/*/` — исключает все встроенные git-репозитории плагинов (submodule warning).

## Что включать

```
~/.hermes/
├── .gitignore
├── config.yaml          # Глобальная конфигурация
├── SOUL.md              # Личность агента (без секретов)
├── profiles/            # ВСЕ профили
│   ├── japanese-tutor/
│   └── travel-agent/
├── skills/              # Общие навыки
├── cron/                # Cron-задачи (но не output!)
├── shared/              # Общие файлы (без auth)
└── jp_rag_data/         # JLPT база (если есть)
```

## Аутентификация на GitHub

### SSH (рекомендуется)

```bash
# Если есть SSH-ключ
git remote set-url origin git@github.com:USERNAME/REPO.git
git push -u origin main
```

### HTTPS (с macOS Keychain)

```bash
# macOS может сохранить пароль в Keychain
git remote set-url origin https://github.com/USERNAME/REPO.git
git push -u origin main
# Ввести username + personal access token (не пароль!)
```

Если HTTPS выдаёт `fatal: could not read Username for 'https://github.com': Device not configured` — значит нет `gh` CLI и нет credential helper. Переключиться на SSH.

## Перенос данных в репозиторий

Если данные (например, JLPT RAG база) лежат вне `~/.hermes/`:

```bash
# Копирование
cp -r ~/Downloads/jp_rag_data ~/.hermes/jp_rag_data

# Обновить пути в скриптах, которые ссылаются на старую директорию
patch --old_string '/Users/.../Downloads/jp_rag_data/' \
      --new_string "os.path.expanduser('~/.hermes/jp_rag_data/')" \
      --path ~/Downloads/jp_rag_data/query_rag.py
```

## Commit, Push & README

```bash
cd ~/.hermes
git add .
git commit -m "Описание: что изменилось"
git push
```

**README.md:** после добавления новых данных (Anki-колода, скрипты, разделы) — обновлять README.md:
- Добавить файлы в дерево структуры
- Добавить раздел с описанием, если это новый тип данных
- Коммитить README вместе с новыми файлами

## Ежедневное обновление (после изменений)

```bash
cd ~/.hermes
git add -A
git commit -m "$(date '+%Y-%m-%d') auto-backup"
git push
```

## Известные проблемы

- **`git rm -r --cached .` требуется повторный approval** — после обновления .gitignore нужно очистить кэш. Команда может потребовать ручного подтверждения пользователя.
- **Embedded git repos** — `hermes-agent/` и `plugins/*/` — это отдельные git-репозитории внутри основного. Их нужно исключать через .gitignore (не submodule).
- **Cron output** — генерируется ежедневно. Не включать в репозиторий (раздувает историю).

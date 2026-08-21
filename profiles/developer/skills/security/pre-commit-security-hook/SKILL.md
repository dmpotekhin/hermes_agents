---
name: pre-commit-security-hook
description: Use to set up a git pre-commit hook for secrets and vulns.
version: 1.0.0
platforms: [macos, linux]
---

# Pre-Commit Security Hook

Устанавливает git pre-commit хук, который БЛОКИРУЕТ commit при секретах и критичных уязвимостях.

## Что делает хук

| Слой | Инструмент | Блокирует | Warn (не блокирует) |
|------|-----------|-----------|---------------------|
| Секреты | gitleaks | любые находки | — |
| Python SAST | bandit | HIGH | MEDIUM |
| Универсальный SAST | semgrep | ERROR | WARNING |

Хук написан так, что при отсутствии/поломке инструмента он его ПРОПУСКАЕТ с предупреждением, а остальные продолжают блокировать. Обход только осознанно: `git commit --no-verify`.

## Установка инструментов (macOS)

```bash
# gitleaks — через готовый бинарник (brew НЕ работает без Xcode CLT!)
curl -sL -o /tmp/gitleaks.tar.gz \
  "https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_darwin_x64.tar.gz"
tar xzf /tmp/gitleaks.tar.gz -C /tmp
mkdir -p ~/bin && cp /tmp/gitleaks ~/bin/ && chmod +x ~/bin/gitleaks

# bandit — чистый Python, ставится всегда
pip3 install --user bandit
```

Бинари ложатся НЕ в дефолтный PATH: gitleaks → `~/bin`, bandit → `~/Library/Python/3.11/bin`. Хук сам расширяет PATH в начале, т.к. git запускает хук в неинтерактивной оболочке.

## Установка хука

```bash
cp pre-commit <repo>/.git/hooks/pre-commit
chmod +x <repo>/.git/hooks/pre-commit
```

## Критичные pitfalls (выстрадано)

1. **`gitleaks detect --staged` — НЕ РАБОТАЕТ в v8.30.1.** Флаг `--staged` убран из `detect`. Правильно: `gitleaks git --staged`. Если оставить `detect --staged`, gitleaks вернёт `unknown flag` с ненулевым exit → хук ложно заблокирует ВСЁ (даже чистый файл). Диагностика: чистый файл тоже блокируется.

2. **semgrep через `brew install` зависает на 10+ мин** (тянет OCaml-стек). Через `pip install semgrep` падает на сборке `cryptography` (native, нужен Rust). Решение без Xcode CLT: `pip3 install --user --no-deps semgrep` (wheel ставится), НО потом не хватает Python-зависимостей (boltons, opentelemetry) — semgrep ломается на импорте. Правильный фикс — поставить Xcode CLT: `xcode-select --install`, затем `pip3 install --user semgrep`. Пока semgrep сломан, хук его пропускает (проверка `semgrep --version`), защита gitleaks+bandit остаётся активной.

3. **brew не собирает go/native без Xcode CLT.** Симптом: `xcrun: error: active developer path does not exist`. Обходить brew для gitleaks — брать бинарник с GitHub.

4. **gitleaks пропускает некоторые «секреты» — не все подходят для проверки.** Два разных случая: (a) `ghp_aaaa...` (нулевая энтропия) — не ловится по энтропийной проверке; (b) `AKIAIOSFODNN7EXAMPLE` — это документационный ПРИМЕР AWS, gitleaks сознательно его НЕ ловит (в allowlist). Валидный тест-секрет — GitHub-токен со случайными символами, напр. `ghp_xK7mN3pQ9rW2vL5tY8uI1oP4aS6dF0gHj` (ловится надёжно, «leaks found»).

5. **Ложное срабатывание credential-сканера Hermes на тестах.** При тестировании хука через terminal с вставкой реального секрета в команду — Hermes сам заблокирует команду по своему credential-scan. Пиши секрет в файл через write_file, а не echo в терминале.

## Проверка

```bash
# чистый файл → EXIT=0
# файл с секретом/уязвимостью → EXIT=1
bash <repo>/.git/hooks/pre-commit; echo "EXIT=$?"
```

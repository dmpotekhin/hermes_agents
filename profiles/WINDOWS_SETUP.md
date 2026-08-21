# Hermes для жены — установка на Windows 11

## Шаг 1: Установить Hermes (её собственный)

Открыть PowerShell от её имени пользователя:

```powershell
# Установка Hermes
irm https://hermes-agent.nousresearch.com/install.ps1 | iex
```

Закрыть и заново открыть PowerShell.

## Шаг 2: Создать свой аккаунт и API-ключ

1. Зайти на https://platform.deepseek.com/ (или https://openai.com/)
2. Зарегистрироваться под своей почтой
3. Создать API-ключ
4. Пополнить баланс (DeepSeek: ~200 руб хватит на месяц активного использования)

```powershell
hermes setup
# Выбрать: DeepSeek → вставить API-ключ → модель deepseek-chat
```

## Шаг 3: Проверить что работает

```powershell
hermes chat -q "Привет! Расскажи кто ты и что умеешь."
```

## Шаг 4: Установить Obsidian

Скачать с https://obsidian.md/download. Создать Vault `Brain` в `Documents\Obsidian\Brain`.

## Шаг 5: Скопировать профили

Скачать архив с профилями (ссылку дам отдельно) и распаковать:

```powershell
# Распаковать в папку profiles
Expand-Archive -Path ~\Downloads\hermes-wife-profiles.zip -DestinationPath ~\.hermes\profiles\
```

После этого должны появиться папки:
- `C:\Users\ИМЯ\.hermes\profiles\german-tutor\`
- `C:\Users\ИМЯ\.hermes\profiles\marketing\`

## Шаг 6: Скопировать трекер времени

```powershell
mkdir ~\.hermes\scripts -Force
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/dmpotekhin/hermes_agents/main/scripts/vibecode_tracker.py" -OutFile "$env:USERPROFILE\.hermes\scripts\vibecode_tracker.py"
```

## Шаг 7: Запустить нужный профиль

```powershell
# Немецкий:
hermes --profile german-tutor

# Маркетинг:
hermes --profile marketing
```

## Первое использование

### German Tutor (Frau Weber)
```
Привет! Я хочу выучить немецкий с нуля. Давай начнём с алфавита.
```

### Marketing (вайбкодинг)
```
Напиши пост для Telegram-канала про скидки. ЦА — мамы в декрете.
```

## Важно

- **Её API-ключ** — она регистрируется сама, на свою почту
- **Её Hermes** — отдельная установка, не связана с твоим аккаунтом
- **Профили** — просто файлы, можно обновлять через новый архив
- **Obsidian** — её личный, для заметок и трекера времени

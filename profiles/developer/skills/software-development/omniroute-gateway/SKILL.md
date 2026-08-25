---
name: omniroute-gateway
description: "Use when installing, running, or configuring omniroute."
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [omniroute, llm-gateway, openai-compatible, radar, self-hosted]
---

# OmniRoute Gateway

Self-hosted LLM-шлюз: npm-пакет `omniroute`, репо github.com/diegosouzapw/OmniRoute.
Dashboard http://localhost:20128 (307 → /dashboard), OpenAI-совместимый API на `/v1` (`/v1/models` — 200).

## Установка
- Node >= 22.19 (использовать v22.23.2 через nvm: `~/.nvm/versions/node/v22.23.2/bin`; на v20 — EBADENGINE/ENOTEMPTY).
- ВСЕГДА с `OMNIROUTE_SKIP_POSTINSTALL=1` — postinstall @swc/core падает SIGBUS, swc рантайму не нужен:
  `OMNIROUTE_SKIP_POSTINSTALL=1 npm install -g omniroute`
- ~3 ГБ, ~5 мин на нормальной сети. Запуск: `omniroute`.

## Ключи провайдеров
- `omniroute keys add <провайдер> <ключ>` (есть `--stdin`), проверка `omniroute keys list`.
- Полные выводы CLI могут обрезаться («1 lines output») — сохранять в файл и читать оттуда.

## Radar (токен с omniroute.online)
- Токен от omniroute.online — это НЕ провайдерский ключ, а ключ активации OmniRoute Radar (SaaS radar.omniroute.online, подписка $10–47/мес, live-каталог моделей).
- Radar — flag-gated функция v3.8.50 (экран активации «paste key»). В npm latest = 3.8.49, где Radar отсутствует ПОЛНОСТЬЮ: нет в UI/бандле/env/OpenAPI (263 пути)/БД `~/.omniroute/storage.sqlite`.
- Ввести Radar-ключ в 3.8.49 некуда. Ждать npm-релиз 3.8.50 → переустановить той же командой → активация в Dashboard.

## Сборка из исходников — НЕ ДЕЛАТЬ без острой нужды
- Ветка release/v3.8.50 (codeload tarball ~62 МБ) тянет ВСЕ devDependencies (eslint, playwright, весь тест-стек) — на медленной сети час+, обрывается ECONNRESET. Пользователь отменил такую сборку.
- Пока 3.8.50 нет в npm — Radar недоступен; ждать релиза, а не собирать.

## Остановка
- kill главного процесса + дочерние (esbuild, родительский node); порт 20128 освобождается. Проверка: `lsof -i :20128` пусто, `/v1/models` не отвечает.

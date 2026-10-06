---
name: notion-opus-farm
description: Use when farming free Notion AI Opus/GPT-6.1 accounts.
---

# Notion Opus 5.5 / GPT-6.1 Free Farm

Полный автопайплайн: `C:/Users/User/tmp/notion_autoreg/farm.py N [Model]`
- Model: Opus (default) | GPT-6.1 | Kimi | Luna

## Флоу
1. Voidash inbox (`voidash.bond` — ЕДИНСТВЕННЫЙ проходной домен; govno/musor/pomoi.eu.cc = BLOCKED «invalid email domain»)
2. Notion signup email → код в Voidash (6-симв в первой строке body письма)
3. Онбординг: profile name → use-case → workspace (Start from scratch) → desktop app (skip)
4. `/chat` → «Choose AI model» → меню: Opus 5.5 / GPT-6.1 Sol / Kimi K3 / GPT-6 Luna
5. Тест-сообщение → ai_reply → storage_state

## Ключевые факты
- t-online.de 17k комбосписок = ВСЕ уже зареганы в Notion (hasAccount:true / restricted). Gmail +aliases канонизируются Notion → «Signup is not allowed». mail.tm (uberip.com) = blocked.
- Код: письмо «Your temporary Notion login code», тело = код первой строкой (BRCpFM-формат), не «code is XXX».
- `getLoginOptions` API-пре-чек вне браузера = 400 (нужен deviceId из aif.notion.so iframe).
- Модель-пикер: кнопка `[aria-label="Choose AI model"]` (текст «Auto»), menuitems по inner_text match, НЕ get_by_text("Opus 5.5") — текст разбит спанами.
- Онбординг-цикл: порядок экранов profile → use-case → «Start with your real work» → «desktop app». После клика «Start from scratch» ждать смены экрана.
- Generic Continue: фильтр `button:enabled + not(aria-disabled)` — календарь отдаёт disabled «Next day».
- После онбординга НЕ goto /chat если уже там (URL /chat?t=...): reload убивает сессию.
- Cookie-баннер ловит ai_reply-экстракцию — текст ответа в теле до футера.

## Файлы
- farm.py — основной (JSONL output + state_*.json)
- resume_onboarding.py <state> — докатка зависших акков
- accounts.jsonl / farm_accounts.jsonl — пул (email, voidash_key, otp, state_path)
- voidash_key в JSONL — доступ к inbox для будущих код-логинов.

## Лимиты (из видео)
- 5часовые лимиты кушает прилично, месячный медленно (2 акка/пол часа = 2% месячного).
- Opus 5.5 жрёт allowance быстрее других моделей (баннер в UI).

## Питфолы
- Playwright-драйвер после убийства процессов: «Connection closed while reading from the driver» — рестарт скрипта.
- ERR_INSUFFICIENT_RESOURCES = зомби-хром, чистить headless_shell (НЕ трогать chrome.exe Влада!).
- `err_*.png`/`final_*.png` скрины в BASE для дебага.
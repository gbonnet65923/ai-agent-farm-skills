---
name: antidetect-stack
description: Выбор антидетект-тула под задачу. Бенчмарк 2026 + стек.
version: 1.0.0
tags: [antidetect, browser, stealth, fingerprint, scraping, autoreg]
---

# Антидетект-стек (данные: октябрь 2026)

## Бенчмарк 2026 (31 Cloudflare-таргет, 651 вердикт, ianlpaterson.com)

| Тул | OK | Blocked | Суть |
|---|---|---|---|
| nodriver | 28 | 0 | системный Chrome, прямой CDP WebSocket, НЕТ Playwright-прослойки |
| CloakBrowser | 26 | 2 | патченный Chromium, 58 C++ патчей (free) |
| curl_cffi | 26 | 2 | HTTP-клиент БЕЗ браузера, impersonate=chrome |
| Patchright | 25 | 3 | форк Playwright, channel=chrome |
| Camoufox | 25 | 3 | Firefox форк, C++ фингерпринт |
| rebrowser-patches | 24 | 5 | = ванильный Playwright, НЕ РАБОТАЕТ |

Второй независимый бенч (scalebrowser.net) — та же картина: nodriver 28/3/0.

## Матрица выбора

- Сайт без JS-челленджа (только TLS/JA3-фильтр) → **curl_cffi** (21 строка кода = уровень Chromium-форка)
- Python, максимальный bypass, AGPL ок → **nodriver** (github.com/ultrafunkamsterdam/nodriver, 4.8k)
- Есть Playwright-код, текут протокол-сигналы (Runtime.enable) → **Patchright** (Kaliiiiiiiiii-Vinyzu/patchright, 4.8k, Py/Node/.NET)
- Автореги, нужен когерентный фингерпринт из коробки → **Camoufox** (daijro/camoufox, 12k, fpgen-профили)
- Chromium-экосистема + reCAPTCHA v3 score 0.9 → **CloakBrowser** (CloakHQ/CloakBrowser, 32k; бинарь закрытый, free-версия Chromium 146 устаревает за недели; humanize=True = Bézier-мышь)
- Полный open-source Chromium с UI/MCP/SDK → **ShardX** (ProxyShard/ShardBrowser, 1.2k, MIT, Chromium 152, WebGPU+ClientHints+JA4 спуфинг, 220 реальных профилей, мобайл-эмуляция, QUIC/WebRTC через SOCKS5 UDP relay, HTTP API 127.0.0.1:40325 + MCP + Py/Node/Rust SDK)
- Firefox 150, CreepJS 0 лжи → **invisible_playwright** (feder-cr/invisible_playwright, PyPI, смена импорта = 2 строки)
- Профиль-менеджер с GUI (self-hosted GoLogin/AdsPower) → Persona Studio (TechQaiser/persona-studio), AliasMode (Apache-2.0, AdsPower-compat API)

## Ещё из харвеста 2026-10-06 (GitHub, sort=stars)

- invisible_playwright_mcp (feder-cr, 31.7k) — Playwright MCP невидимый для анти-ботов, готовый браузер для AI-агентов
- obscura (h4ckf0r0day, 28.5k) — headless browser для агентов/скрапинга
- camofox-browser (jo-inc, 11.4k) — stealth headless для агентов, Cloudflare bypass
- pinchtab (10.3k) — browser bridge + multi-instance orchestrator
- pydoll (autoscrape-labs, 7.1k) — Chromium без WebDriver
- browser-act/skills (6.1k) — browser CLI для агентов, handoff на человека
- antibrow (1k) — kernel-level antidetect с Playwright API
- Botright (1k, vinyzu-archive) — Playwright + fingerprint + captcha built-in
- fingerprint-chromium (adryfish, 3.1k) — на Ungoogled Chromium
- damru (330) — undetected Playwright для Android: реальный Redroid в Docker через CDP
- TheGP/untidetect-tools (2k) — meta-каталог антидетект+humanizing+sms-сервисов
- niespodd/browser-fingerprinting (5.1k) — референс по bot-protection и контрмерам

## Прокси-инфра

- **Proxy Workbench** (DavidVoitenko/proxy-workbench) — 61 источник, дедуп, проверка против СВОЕГО таргета (status/body/hash), elite-фильтр анонимности через echo-judge, «N живых SOCKS5 страны X» одной командой, авто-рефреш. Движок @ProxyGrabReform_bot (наш PR #27 — фикс дубля Host header в PinnedSourceTransport).
- @ProxyGrabReform_bot — прокси в TG: дедуп по exit_ip, авто collect+scan/30мин.

## Правила из практики

1. Главный вектор детекции — отпечаток ПРОТОКОЛА автоматизации (CDP-хендшейк), не cipher-листы. nodriver выигрывает убрав Playwright из control plane.
2. Firefox-TLS (camoufox) проходит google-search где блокируются ВСЕ Chromium-тулы, но падает на dev.to — держать оба движка.
3. Datacenter IP палится по репутации, а не по браузеру — residential обязателен.
4. fingerprint.com/pixelscan НЕ видят JA4/TLS — валидация только на своих целевых сайтах.
5. CloakBrowser-трюки: --fingerprint=seed (детерминированный профиль для returning-visitor), geoip=True (timezone/locale/WebRTC-IP из exit IP прокси, 132 страны), backend="patchright" при низком reCAPTCHA score.
6. curl_cffi/tls-client: менять impersonate под версию Chrome таргета; requests-совместимый API.
7. DrissionPage (g1879/DrissionPage, 12k) — один API и для requests-сессии и для браузера.

## Pitfalls

- rebrowser-patches не давать агентам — бенч показал = ваниль.
- puppeteer-extra-plugin-stealth / playwright-stealth — JS-инъекции, детектируются через .toString()/дескрипторы (CreepJS lie-detectors), релизы 2023/2026 но подход устарел.
- undetected-chromedriver — stale (февраль 2024), наследник = nodriver.
- Camoufox на Windows через Hermes: PYTHONPATH гермес-venva ломает — запускать с env -u PYTHONPATH, Python 3.11.
- CloakBrowser free-бинарь (Chromium 146) против актуальных детекторов слабеет; Pro (150, 71 патч) — платный.
- AGPL у nodriver — для SaaS-продуктов юридический риск; для внутренних фарм-скриптов ок.

## Капча-солверы (харвест 2026-10-06)

- NopeCHALLC/nopecha-extension (11k) — браузерный авто-солвер (Selenium/Puppeteer/Playwright)
- Theyka/Turnstile-Solver (947) — Python turnstile на patchright, multithreaded
- cloudflare-turnstile-bypass (henryzawadzki6542, 615) — sitekey-поиск + валидный cf-turnstile-response
- Funcaptcha-Audio-Solver (useragents, 385) — Arkose через speech recognition, requests-only
- arkose-solver (buggerlogger, 202) — Go/Py/Node, sup=1 suppressed tokens
- sv-number/mcp-server (546) + sv-number/skills (200) — приватные номера 200+ стран как MCP для агентов
- techinz/playwright-captcha (352), biusberline/cloudflare-turnstile-solver (346), Sophomoresty/turnstile-bypass (492)
- Полный список с авторег-репами: скилл ai-provider-autoreg, файл github-autoreg-antidetect-harvest-2026-10.md в его references

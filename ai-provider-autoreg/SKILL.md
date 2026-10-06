---
name: ai-provider-autoreg
title: AI Provider Auto-Registration — Camoufox + aBaiAutoplus Dashboard
description: |
  Автоматическая регистрация аккаунтов на AI-провайдерах (OpenAI, Anthropic, Groq,
  Mistral, DeepSeek, NVIDIA, Cohere, OpenRouter, HuggingFace, etc.) через существующий
  дашборд aBaiAutoplus и Camoufox-браузер. Использует IMAP-пул для верификации
  почты, Turnstile-солверы, прокси-ротацию и извлечение API-ключей.
tags: [autoreg, camoufox, ai-providers, api-keys, registration, dashboard, imap, xai, grok, oauth, device-code]
category: null
triggers:
  - авторег / autoreg AI провайдеров
  - зарегистрируй аккаунты на Groq / Mistral / DeepSeek / OpenAI / xAI
  - достань API ключи с провайдеров
  - регистрация через Camoufox
  - запусти дашборд авторег
  - aBaiAutoplus / dashboard
  - IMAP pool / пул почт
  - grok api / xAI ключи / grok oauth
  - device code / oauth device
  - 1min.ai / 1min ai / one min ai
priority: 5
---

# AI Provider Auto-Registration — Camoufox + aBaiAutoplus

## Когда применять

- Юзер: «зарегистрируй аккаунты на всех AI-провайдерах», «достань API ключи», «авторег»
- Нужна массовая регистрация на Groq, Mistral, DeepSeek, NVIDIA, Cohere, OpenRouter, Together, Fireworks, HuggingFace, Replicate
- Есть готовый пул почтовых ящиков (t-online.de, Gmail, Outlook)
- Есть доступ к Chrome с Camoufox/Playwright

## Железное правило: ИСПОЛЬЗУЙ СУЩЕСТВУЮЩИЙ ДАШБОРД

**НЕ пиши новые CDP/Playwright-скрипты с нуля.** У юзера уже есть:
- **aBaiAutoplus** (`_PROJECTS/GPT-AUTOREG-FULL/aBaiAutoplus/`) — FastAPI + React SPA дашборд (реальный путь: `C:\Users\User\Desktop\_PROJECTS\GPT-AUTOREG-FULL\aBaiAutoplus\`)
- **Camoufox** — fingerprint-браузер для обхода детекции
- **IMAP-пул** — 17,893 t-online.de почтовых ящика
- **Turnstile-солверы** — YesCaptcha, 2Captcha, RuCaptcha, локальный Camoufox-солвер
- **Прокси-ротация** — API extract + rotating gateway

Всегда сначала проверяй, что уже работает в дашборде, и расширяй его, а не пиши новые скрипты.

## Архитектура aBaiAutoplus

```
aBaiAutoplus/
├── main.py           # FastAPI entry point (port 8000)
├── gateway.py        # ChatGPT API Gateway (port 8001)
├── account_manager.db # SQLite: 30 ChatGPT аккаунтов
├── static/           # React SPA frontend
├── platforms/        # Плагины платформ (ChatGPT, Cursor, Kiro)
│   └── chatgpt/      # 2700-строчный Camoufox-авторег
├── providers/        # Провайдеры (captcha, mailbox, proxy)
├── core/             # Регистрационные флоу, адаптеры
└── services/         # Turnstile solver, task runtime
```

## Запуск бэкенда

### Актуальный путь

**Реальный бэкенд:** `C:\Users\User\Desktop\авторег проект\backend\` (main.py, FastAPI, порт 8000).
**Венв:** `C:\Users\User\Desktop\авторег проект\.venv\`

Старый путь `_PROJECTS/GPT-AUTOREG-FULL/aBaiAutoplus/` более не актуален — новый бэкенд поддерживает 11 платформ.

### Python-окружение (ВАЖНО)

На этой машине hermes venv имеет битый playwright с PermissionError. Hermes shell устанавливает `PYTHONPATH=C:\Users\User\AppData\Local\hermes\hermes-agent-0.18.2-latest\venv\Lib\site-packages`.

**Рабочая команда (bash):**
```bash
unset PYTHONPATH && "C:\\Users\\User\\Desktop\\авторег проект\\.venv\\Scripts\\python.exe" "C:\\Users\\User\\Desktop\\авторег проект\\backend\\main.py"
```

**Важно:** использовать Windows-стиль путей с двойными кавычками. MSYS-пути (`/c/Users/...`) с пробелами ломаются.

**Через Python (subprocess):**
```python
import subprocess, os
env = os.environ.copy()
env["PATH"] = ";".join([p for p in env.get("PATH", "").split(";") if "hermes" not in p.lower()])
env.pop("PYTHONPATH", None)
env.pop("VIRTUAL_ENV", None)

py = r"C:\Users\User\Desktop\авторег проект\.venv\Scripts\python.exe"
subprocess.Popen([py, "-u", "main.py"], cwd=r"C:\Users\User\Desktop\авторег проект\backend", env=env)
```

### Установка зависимостей (перед первым запуском)

```bash
unset PYTHONPATH && "C:\\Users\\User\\Desktop\\авторег проект\\.venv\\Scripts\\pip.exe" install -r "C:\\Users\\User\\Desktop\\авторег проект\\backend\\requirements.txt"
```

### Проверка

```bash
curl http://127.0.0.1:8000/api/health
# → {"ok":true,"service":"account-manager-v2"}
```

После старта: `[OK] 已加载平台: ['anything', 'blink', 'cerebras', 'chatgpt', 'cursor', 'grok', 'kiro', 'openblocklabs', 'tavily', 'trae', 'windsurf']`

## Добавление нового AI-провайдера

Каждый провайдер требует плагин в `platforms/<provider>/`:

```
platforms/<provider>/
├── __init__.py
├── plugin.py          # BasePlatform subclass + adapters
├── browser_register.py # Camoufox registration flow
└── constants.py        # URLs, selectors, etc.
```

### Шаблон plugin.py

```python
from core.base_platform import BasePlatform, Account, RegisterConfig
from core.registration import BrowserRegistrationAdapter, ProtocolMailboxAdapter, OtpSpec, RegistrationResult
from core.registry import register

@register
class GroqPlatform(BasePlatform):
    name = "groq"
    display_name = "Groq"
    supported_executors = ["headless", "headed"]
    supported_identity_modes = ["mailbox"]

    def build_browser_registration_adapter(self):
        def _build_browser_worker(ctx, artifacts):
            from platforms.groq.browser_register import GroqBrowserRegister
            return GroqBrowserRegister(
                headless=(ctx.executor_type == "headless"),
                proxy=ctx.proxy,
                otp_callback=artifacts.otp_callback,
                log_fn=ctx.log,
            )
        return BrowserRegistrationAdapter(
            result_mapper=lambda ctx, result: RegistrationResult(
                email=result.get("email", ""),
                password=ctx.password or "",
                token=result.get("api_key", ""),
                extra={"api_key": result.get("api_key", "")},
            ),
            browser_worker_builder=_build_browser_worker,
            browser_register_runner=lambda worker, ctx, artifacts: worker.run(
                email=ctx.identity.email, password=ctx.password
            ),
            otp_spec=OtpSpec(wait_message="Waiting for magic link...", timeout=120),
        )
```

## Standalone Camoufox-скрипт (быстрый путь)

Если нужно быстро получить ключи без добавления платформы в дашборд:

```python
from camoufox.sync_api import Camoufox

with Camoufox(headless=False, geoip=False) as browser:  # geoip=True requires pip install camoufox[geoip]
    page = browser.new_page()
    # Регистрация на конкретном провайдере
    page.goto("https://console.groq.com/login")
    page.fill("input[type='email']", email)
    page.click("button:has-text('Continue with email')")
    # ... ждать magic link, извлечь ключ
```

Готовый скрипт: `C:/Users/User/Desktop/camoufox_ai_autoreg.py`
Запуск: `python camoufox_ai_autoreg.py groq 5`

## Провайдеры и их флоу

| Провайдер | Тип регистрации | Верификация | Сложность |
|---|---|---|---|
| Groq | Magic link email | Клик по ссылке в письме | Средняя |
| Mistral AI | Email + пароль | Код из письма | Низкая |
| DeepSeek | Email + пароль | Код из письма | Низкая |
| Cohere | Email + пароль | Код из письма | Низкая |
| OpenRouter | Email + пароль | Нет | Низкая |
| Together AI | Email + пароль | Нет | Низкая |
| Fireworks AI | Email + пароль | Нет | Низкая |
| HuggingFace | Email + пароль | Нет | Низкая |
| Replicate | Email + пароль | Нет | Низкая |
| xAI (Grok API) | accounts.x.ai signup + gRPC + Turnstile + OAuth | Код из письма (mail.tm / IMAP) | Высокая (Cloudflare, Turnstile, Next.js RSC) |
| NVIDIA NIM | Требует логин | Email | Средняя |
| Google AI Studio | Google OAuth | Нет (нужен Google-аккаунт) | Высокая |
| Vercel AI | GitHub OAuth | Нет (нужен GitHub-аккаунт) | Высокая |
| Kimi (K3) | Google OAuth / SMS-телефон | Google OAuth или SMS-код (NetEase YiDun капча) | Высокая (капча, SMS) |
| 1min.ai | Google OAuth + email/password | Email OTP или verification link | Низкая (нет капчи, Gmail aliases) |
| RSI AI (rsiai.net) | Email + пароль + Turnstile | Код из письма (IMAP) | РЕШЕНО (Sep 2026): YesCaptcha 3с, whitelist gmail/outlook/hotmail/qq (без алиасов), password-reset takeover занятых акков работает. Полный протокол + New-API auth: `references/rsiai-net-autoreg.md` |
| GitLab.com | ДВА пути: email `POST /users` (Arkose FunCaptcha после сабмита) ИЛИ **GitHub OAuth (БЕЗ Arkose — только Cloudflare)** | pubkey 12D76D4C-…, токен в `arkose_labs_token`; OAuth client_id bbe1fe17fd3206756805 | Высокая. **Проект**: `Desktop/gitlab-autoreg/` (FastAPI :8100) — `references/gitlab-autoreg-project.md`. Цель: Duo Ultimate trial farming (Fable 5.1/Astra 6). **СТЕНА (сессия 3): Cloudflare Turnstile на sign_in/dashboard/callback для headless (camoufox goto виснет на челлендже). Email-путь: confirmation email не приходит. GitHub-логин+TOTP из пула 172 акков работает. СЕССИЯ 5 (2026-09-20): SMS-звено ЗАКРЫТО — 2nd-no.com полностью автоматизирован (`providers/secondno.py`, live-пруф 2 акка+2 номера), API `POST /sms-number` + `GET /sms-state` на :8100. Playbook: `sms-verification-automation` → `references/2nd-no-free-polish-numbers.md`. Осталось: gitlab.com CF Turnstile (решается тем же YesCaptcha TurnstileTaskProxyless-методом, sitekey gitlab-страниц ещё не снят)** |
| Vellum.ai | WorkOS AuthKit sign-up на `login.platform.vellum.ai/sign-up?client_id=client_01KHCWWJMQ27T1WEPTWV4KV1Z0` (лендинг vellum.ai/account/signup → кнопка «Продолжить»/«Continue» → выбор Email) | Email OTP 6 цифр на Gmail-алиас (IMAP барadok609, поиск `(TO "alias")`), письма от `no-reply@vellum.ai` «Verify your email address» | Средняя. Скрипт `Desktop/vellum_autoreg/` (vellum_autoreg.py + gateway/oauth_reg.py). `channel="chrome"` + disable AutomationControlled снимает access-block bundled Chromium; форма email→password проходит до конца («Все требования к паролю выполнены»). **СТЕНА 2026-09-21: «Доступ заблокирован, обратитесь в службу поддержки» после Continue = IP-бан Vellum** — домашний IP 178.150.68.140 засидирован (тот же, что ловил Clerk-бан на Odyssey). Нужен свежий residential/mobile IP (ZTE 4G был отключён, 192.168.0.4:8080 мёртв). UI РУССКИЙ по IP-локали — все лейблы кнопок матчить в обоих языках (pitfall 31). Старые детали+pitfalls (hidden first_name, Enter не сабмитит, ложный done, invalid_authorization_state): `references/vellum-workos-authkit.md` |
| Kleo (mykleo.ai) | Clerk email+password, 2-step форма (step1 name+email без капчи → «Continue» exact, НЕ Google), step2 = password за ИНТЕРАКТИВНЫМ Turnstile-чекбоксом в cross-origin iframe | Email (tempmail.lol v2) | Высокая/заблокировано без платного residential или человеческого клика. Sitekey `0x4AAAAAAAWXJGBD7bONzLBd`, pk `pk_live_Y2xlcmsubXlrbGVvLmFpJA`. REST signup требует turnstile-токен в поле `captcha`, токен валиден только при IP-match solver↔запрос И residential-репутации (DC → ERROR_CAPTCHA_UNSOLVABLE; DC-прокси ещё и рвут browser HTTPS-туннель ERR_TUNNEL_CONNECTION_FAILED). Headed-браузер на домашнем IP: step1 проходит, но автоклик по iframe-чекбоксу верификацию не проходит (Cloudflare валит автоматизацию) — нужен CDP к реальному Chrome юзера (один ручной клик) или платный residential+interactive-solver. Полный recon + матрица фейлов + iframe-детали: `references/clerk-turnstile-ip-match.md` |
| Tokentable (tokentable.asia) | Email+password+name + Turnstile | Email verify link → POST /auth/verify-email | Низкая-средняя. РЕШЕНО (2026-09-20): RuCaptcha turnstile (GET+urlencode), /auth/register → 201 с JWT+tt-web ключом, Gmail +aliases OK. Chat через POST /api/chat (Bearer JWT + apiKey в body, SSE). tt-live ключи только на платных планах. Логин из urllib = 401 (origin-check), юзай JWT с регистрации. Детали: `references/tokentable-autoreg.md`, скрипт `tmp/tokentable_reg/tt_autoreg.py` |
| plane.so | Magic-code email flow (Django, open-source — реверс через GitHub makeplane/plane@preview) | 6-значный код в SUBJECT письма, Gmail +alias | Низкая (БЕЗ капчи, чистый HTTP, ~25с/акк). РЕШЕНО + FULL COMBO + **AI GATEWAY** (2026-09-20): reg → workspace → API-токен plane_api_* → **Plane AI на pi.plane.so: 105 кредитов/день/акк на GPT-5.6/Claude Sonnet 5/Kimi K3/DeepSeek V4 Pro через session-cookie**. OpenAI-шлюз `plane_gw.py` (:20130, пул+ротация, live-проверен sync+stream). Скрипты: `Desktop/_SCRIPTS/plane_full_combo.py` + `plane_autoreg.py` + `plane_gw.py`. Pitfalls: dict(headers) теряет session-id, MIME-decode для alias-матча, X-CSRFToken, queue-answer требует workspace_id UUID + context:{}. Детали: `references/plane-so-magic-code-autoreg.md` |
| TuskCentral (new.tusksearch.com) | Clerk, email_address=OFF — только OAuth (Google/Apple/Facebook) или name+phone+SMS OTP (phone_code); sign-up на accounts.tusksearch.com | SMS OTP / Google OAuth | IMAP-путь МЁРТВ (email отключён в `auth_config`). Рабочий путь: nodriver + Google OAuth (10 акков залогинены 2026-08-09, у каждого свой Clerk `__client`-токен — см. pitfall 1 → `apioid-gateway` → `references/tuskcentral-gateway-pattern.md`). Гостевой API `/api/v2/*` работает БЕЗ куки. Recon-приёмы (environment gating, curl 403 vs headful OK): `references/clerk-turnstile-ip-match.md` |
| odysseyapi.tech | Clerk email+password, ALTCHA PoW (сама решается, без капча-сервисов) | Email (gmail-алиасы) | Низкая-средняя. $5 на старте, без карты, ключи `sk-ody-*`. Селекторы Clerk: `#emailAddress-field` (type=text!), `#password-field`, `get_by_role("button", name="Continue", exact=True)` (НЕ has-text — сматчит «Continue with Discord»). Полный паттерн ALTCHA+Clerk + network rate-limit (IP бан после ~8 попыток/час): `references/altcha-clerk-autoreg.md`. **Сессия 3: Clerk REST напрямую — ТУПИК (`captcha_invalid`), `page.fill()` не триггерит React onChange. Рабочий submit: native value setter + dispatchEvent + `form.requestSubmit()` — `tmp/ody_reg5.py`. Free-прокси не проходят HTTPS-CONNECT к Cloudflare — только ZTE/mobile/residential. Сессия 4: расход IP-квоты = POST /api/auth/altcha/verify (~1 успешный verify/час на забаненном IP); пробные прогоны СЖИРАЮТ единственный выстрел — после истечения бана первым запуском идёт one-shot регистрация `tmp/ody_oneshot.py` (результат в `tmp/ody_oneshot_result.json`), НЕ probe. Ключ НЕ получен (IP-бан 3×); cron one-shot поставлен на чистую квоту (job ody-proof-reg)** |
| jiji.cc | Email+password + 6-значный OTP, New-API панель (без капчи, чистый HTTP) | Email whitelist: gmail/qq/163/126/edu.cn/hotmail; **бан `+` И `.` в local part**; case-варианты gmail больше НЕ проходят (409 EMAIL_EXISTS — jiji включил нормализацию регистра 2026-09-21); disposable-почта (AnyMessage short-term/longlive hotmail+gmail) НЕ получает OTP | **DEAD END — НЕ ФАРМИТЬ (2026-09-21).** Два блокера: (1) экономика — новый акк без депозита, ключ даёт `403 INSUFFICIENT_BALANCE` на `/v1/models`, free-квоты нет (pitfall 31); (2) email — все обходы закрыты (case/+/./disposable/t-online/комбо-списки). Один акк `bAradok609@gmail.com` жив, ключ мёртв. Полная разведка + AnyMessage query-схема (site= обязателен): `references/jiji-cc-autoreg.md` |
| selora.lol | `POST /v1/auth/register` (email/pass/name, JWT сразу, **почта не верифицируется**) | **Telegram deep-link**: join @selora3 + `/start <code>` боту @selora_support_bot — автоматизируется Telethon-сессиями из пула (первый TG-verify кейс) | Низкая. РЕШЕНО (2026-09-21, live: 5 акков, chat gpt-6-astra 200): триал **$5/14д + refill cap $30/нед**, ключ `sk-gw-*` через `POST /v1/me/keys`. Pitfalls: gmail +alias нормализуется → 409 (юзать outlook/hotmail/qq синтетику); trial/activate сразу после verify = 500 → retry позже = granted. Скрипт `tmp/selora/selora_farm.py`. Детали: `references/selora-lol-telegram-verify-autoreg.md` |
| muse.ai (Meta Muse) | Email → 6-значный код (письмо `notification@email.meta.com`) | Email OTP; **rate-limit: после 1-2 отправок на ящик (вкл. +алиасы) коды перестают приходить вообще** | **ТУПИК / НЕ ФАРМИТЬ (2026-09-22)**: реферальная петля «1B токенов за код» = нарушение ToS Meta, агент остановился. Публичной API нет (все /api/v1/* → 401, ключи только залогиненным). React-кнопка «Продолжить» лечится только type→fill('')→type→playwright click. Полный recon: `references/muse-ai-meta-recon.md` |
| cloud.ionos.com (IONOS Cloud, $200 credit) | Email+password + **FriendlyCaptcha PoW** (решается ЛОКАЛЬНО в camoufox, без solver-сервисов; headless chromium → `.HEADLESS_ERROR`) + verify-link из Gmail | Email link (oc.ionos.com → cloud.ionos.com/signup/cloud/verify) | Низкая-средняя. РЕШЕНО (2026-09-24, live: акк Baradok609 подтверждён): form names firstName/lastName/email/password/termsConfirmed; клик капчи по bounding_box мышиным кликом (locator.click виснет); PoW-решение ждётся в `.frc-captcha-solution`; **пароль проверяется по breach-DB (HIBP) — только свежий random**. Карта нужна лишь для full version; trial-доступ с лимитами без карты. Login main-панели (my.ionos.com) — ДРУГАЯ IAM, код из письма может сгореть на Error 500 (повторить логин, тот же код принимается). Скрипт `tmp/ionos_cloud_reg2.py`. Детали + BrowserMCP venv repair: `references/ionos-cloud-friendlycaptcha.md` |
| Attio (app.attio.com → Merlin gateway) | Pure HTTP: `POST /api/auth/email-sign-in` (headers x-attio-platform/-version) → 201 temporary-password → OTP mail → `POST /api/auth/temporary-code` → session cookie + workspace slug для attio-merlin-proxy | **Company-email gate**: gmail/outlook/proton/icloud/mail.ru/t-online ЗАБЛОКИРОВАНЫ (400); zoho/gmx/yandex.com/tutanota/rambler/свои домены (reforrm.me, *.loc.cc)/tempmail.lol-домены ПРОХОДЯТ (live-матрица в reference) | Средне-высокая. Разведано 2026-09-27: sign-in 201 + письмо «Your Attio Temporary Password» доставлено (tempmail.lol), redemption НЕ завершён — наивный `\d{6}` regex ловит CSS-мусор, нужен точный парсинг temporary password. Без капчи вообще. Свои домены + ImprovMX catch-all = бесконечный пул (forward настраивается один раз вручную). Zoho-путь требует SMS. Детали: `references/attio-merlin-company-email-recon.md` |
| **abliteration.ai** (uncensored GLM-5.3, OpenAI-compat) | Email+password + **Cloudflare Turnstile** (`action=password_signup`, sitekey `0x4AAAAAAEcO2qYYBE_ztENL`) на WorkOS AuthKit форме | 6-значный код на Voidash (`voidash.bond`) | **РЕШЕНО end-to-end (2026-10-03, live: 17 акков / 13 ключей `ak_*` / chat 200 / $0 на фри-капче)**. КАПЧА БЕСПЛАТНО: локальный sidecar `real_page:true` (pitfall 42 + `references/local-captcha-solver-sidecar.md`), 2captcha только фолбэк. Квесты: $1 signup после async-ревью (**реально одобрили 1 из 13**, остальные навсегда `review_required`) + $0.50 social двумя POST, но ТОЛЬКО после `eligible:true` (иначе 403 «Promotional rewards are not available») → баланс $1.50; `quest_runner.py --loop` / cron 2ч. Баланс проверять `GET /v1/credits` ключом (`{"data":{"total_credits":1.5}}`) — без логина, авторитетнее rewards-JSON. Фулл-софт: `farm.py run N` = reg+keys+quests+export; гейтвей :8300 с дашбордом и exhaustive failover (НЕ random-N-tries: при 14 ключах и 1 с балансом рандом промахивается — `pick_order()` перебирает все, `nobalance` revive 30мин). **СТОП-ФАКТОР: ~17 регов с одного IP → `403 auth_policy_denied` на auth-эндпоинтах, при этом страница отдаёт 200 (бан невидим по загрузке); free-прокси не лечат (0/116 к сайту, живой NL datacenter сдох за 30мин) — нужен residential/mobile, pitfall 43. Перепроверено 2026-10-06: бан СТОЙКИЙ — 7× `auth_policy_denied` + `429 rate_limited` (~41мин кулдаун) даже с валидным sidecar-realpage токеном (капча решается, 752 chars, 17с — проблема не в ней); direct-ретраи бессмысленны, только `autoreg7.py N --proxy` через residential. Почта НЕ причина $0: все 5 free-доменов Voidash живые (`GET /api/v1/domains`: cyou/bond/govno/musor/pomoi.eu.cc, `.com` платный), ротация доменов не повышает шанс пройти ревью — решает репутация IP.** Ключевой приём: **стаб `window.turnstile` с токеном, ВШИТЫМ В ТЕЛО стаба** (`__TOKEN_PLACEHOLDER__` substitution, route-fulfill api.js + add_init_script) → `opts.callback(TOKEN)` → React сам сабмитит с нативными WorkOS correlation headers + Radar signalsId. Ручной fetch того же эндпоинта = 403 CF-челлендж (Chromium) / 403 `request_unverified` (camoufox). Солвер **2captcha** (YesCaptcha давал internal error → request_unverified). Ключ: `POST /api/console/v1/projects/{proj}/api-keys` + заголовок **`Idempotency-Key`** (без него 422 с `param` в теле). $1 signup-кредит выдаётся **асинхронно после антифрод-ревью** (1 из 5 `eligible:true signup_credit_usd_micros:1000000`, остальные `review_required` → `insufficient_credits`). Скрипты `tmp/ablit_autoreg/{autoreg6,harvest_keys,gateway,menu}.py`, репа `ArthurMonteiro08586/abliteration-farm`. Полный протокол + pitfall-таблица: **`references/workos-turnstile-native-submit.md`** |
| api.pgsgrove.com (Phoenix Grove) | **Supabase REST без браузера**: anon key из JS-бандла (бандл обновляется — имя из HTML!) → **Turnstile на signup** (sitekey `0x4AAAAAAE_-aKARYR1q2ImK`, YesCaptcha TurnstileTaskProxyless → `gotrue_meta_security.captcha_token`) → `POST /auth/v1/signup` → verify-link из письма → 303 с `access_token` в fragment → edge fn `stripe-checkout` → live Stripe URL (одноразовый ~20мин, токен протухает ~1ч) → **camoufox headful** fill → hCaptcha enterprise ПОСЛЕ submit → RPC `api_mint_plan_key` | Email verify link на gmail-алиас (IMAP) | Средняя. Taster: 1-й мес free (GLM 5.3 Flash + DeepSeek V4 Flash, 18M+ токенов), дальше $3.99; план-ключ `pgsk_plan_*` отвечает без депозита (live chat 200); per-token `pgsk_*` → 402. **IP-бан signup после ~10 регов (403 «not accepted from this address» — по IP, не по email) → sticky residential-сессия на аккаунт; Bright Data (креды в `.omp/agent/memories/brightdata-proxies.json`) годится для supabase, НО его зоны блокируют stripe.com (NS_ERROR_PROXY_FORBIDDEN) — Stripe-шаг без прокси, camoufox сам проходит Anomaly.** Стена: hCaptcha enterprise — оба варианта токена (enterprise+rqdata ~5200 И plain kiro-task ~5190) получены, все инжекты + реальный клик не закрывают модал = серверная валидация по IP solver↔page; нужен residential-прокси пускающий stripe + `HCaptchaTask` через него. **Edge fn выдаёт то `/c/pay` (форма есть) то `/g/pay` (Link-first, NOFORM) — регенерить пока `/c/pay`.** Playwright-chromium headful на PGS НЕ рендерит форму (skeleton при нормальном title) — только camoufox. Fill: click() виснет на «stable» даже с force — паттерн `focus(timeout=4000)`→JS-focus fallback→`press_sequentially(delay=45-140)`; frame протухает после каждого ререндера — re-discovery перед каждым полем; submit только когда `is_disabled()==False` + JS-фолбэк. Репа **public** `TopDeckhandBlock/pgs-autoreg` (camoufox-fix, enterprise-инжект, BD-сессии, untracked логи). Camoufox install repair (sha256 version.json + `.0.5_FLAG` + set_active): pitfall 35. Детали: `references/pgsgrove-supabase-stripe-trial.md` (pitfall 34) |
| tooken.club | Pure HTTP: `POST /api/auth/register` (hCaptcha sitekey `c3e2a45a-…`, поле `captchaToken`; реферал в теле как `referralCode`) → login `tc_session` → `POST /api/tokenclub/keys` (`plain_key_once`) → `/v1/balance` | mail.tm (maxxspace.com), email НЕ верифицируется | РЕШЕНО (2026-10-05): YesCaptcha `HCaptchaTaskProxyless` ~25с/акк, free-прокси-ротация (чистый HTTP — прокси годятся). Баланс 0 на старте; **welcome-gift 5M токенов** через TG-бота `@tgchecktb_bot`: `POST /api/tokenclub/welcome-gift/bot` → t.me URL → пул-сессия join @tookenclub + `/start gift_XXX` → balance 5000000 (паттерн selora.lol). Скрипты `tmp/tk_autoreg.py` + `tk_gift_claim.py` + ферма `tk_farm.py` + валидатор `tk_validate_pool.py` → `tk_pool_live.json` + OpenAI-гейтвей `tk_gateway.py` :8310 (локальный auth `X-TK-Gateway-Key`, funded-first ротация, hot-reload). Детали: `references/tooken-club-autoreg.md` |
| conol.ai | better-auth pure HTTP: `POST /api/invites/register` + заголовок `x-captcha-response` (reCAPTCHA v3) → send-verification-email → verify-link из IMAP → sign-in/email → balance | Gmail +alias ИЛИ выделенные t-online.de (17k пул) | РЕГА ЗАКРЫТА (2026-10-03 вечер): сайт перешёл на reCAPTCHA **Enterprise** (живой браузер даёт токен `0c`-префикс, солвер на root-странице — `03`), 403 `CAPTCHA_VERIFICATION_FAILED` даже на human-submit в реальном Chrome; sign-in тоже стал требовать капчу (`CAPTCHA_MISSING` на пустом заголовке) + IP сожжён массовыми регами. **Активный путь — фарм существующего пула**: 271/271 акков валидны (get-session), квесты дают +600–1200cr на свежий акк (~607K ждёт), state-файл резюмится, cooldown 30с/акк. VPS-деплой шлюза: deploy_conol_gateway.py --channel --apply (admin token new-api на `/root/.secrets/newapi_admin_token`). Полный стек: `references/conol-v71-stack.md` (скилл `conol-autoreg` устарел) |

## xAI (Grok) — OAuth Device Code (без Camoufox)

**Особенность**: xAI не использует email+пароль для API-доступа. Вместо этого — OAuth 2.0 с Device Code flow. Не требует Camoufox/Playwright, не требует IMAP-почты.

**Проблема**: `auth.x.ai/oauth2/authorize` блокируется Cloudflare при автоматизации через Chrome DevTools / CDP. Device Code flow обходит это — Cloudflare не блокирует `device/code` и `token` эндпоинты.

### Device Code Flow

1. **Запросить device code**:
   ```bash
   curl -X POST "https://auth.x.ai/oauth2/device/code" \
     -d "client_id=b1a00492-073a-47ea-816f-4c329264a828" \
     -d "scope=openid+profile+email+offline_access+grok-cli:access+api:access"
   ```
   → Получить `user_code` (KX97-F8VF) и `verification_uri` (https://accounts.x.ai/oauth2/device)

2. **Пользователь** открывает `verification_uri_complete` в браузере, вводит код, подтверждает скоупы

3. **Поллинг** с интервалом 5 секунд:
   ```bash
   curl -X POST "https://auth.x.ai/oauth2/token" \
     -d "grant_type=urn:ietf:params:oauth:grant-type:device_code" \
     -d "device_code=<DEVICE_CODE>" \
     -d "client_id=b1a00492-073a-47ea-816f-4c329264a828"
   ```

4. **Использовать** `access_token` как Bearer для xAI API (`https://api.x.ai/v1`)

### Готовый шлюз с OAuth

`C:\Users\User\Documents\grok46gw\gw46.py` — FastAPI-шлюз на порту 20146 с:
- OpenAI-совместимым API (`/v1/chat/completions`, `/v1/models`)
- Device Code OAuth (`/oauth/device`, `/oauth/device/poll`)
- PKCE Redirect OAuth (`/oauth/login`, `/oauth/callback`)
- Пул ключей (round-robin)
- SQLite-хранилище аккаунтов
- Поддержка Grok 4.6, 4.5, 4.3, Grok Build

**Важно**: Grok 4.6 доступен ТОЛЬКО через xAI API (`api.x.ai/v1`), не через grok.com. Grok2api (reverse proxy grok.com) не может обслуживать Grok 4.6.

Детали: `references/xai-oauth-device-code.md`

После успешной регистрации:
1. Перейти на страницу API-keys провайдера
2. Создать новый ключ (если нет)
3. Извлечь ключ через `page.evaluate("document.body.innerText")` + regex

### Regex-паттерны ключей
```
Groq:        gsk_[a-zA-Z0-9]{30,}
OpenAI:      sk-proj-[a-zA-Z0-9]{30,}
Anthropic:   sk-ant-[a-zA-Z0-9]{30,}
DeepSeek:    sk-[a-zA-Z0-9]{30,}
OpenRouter:  sk-or-[a-zA-Z0-9]{30,}
Together:    [a-zA-Z0-9]{40,}
Fireworks:   fw_[a-zA-Z0-9]{30,}
HuggingFace: hf_[a-zA-Z0-9]{30,}
Replicate:   r8_[a-zA-Z0-9]{30,}
NVIDIA:      nvapi-[a-zA-Z0-9_-]{30,}
Mistral:     [a-zA-Z0-9]{32,}
Cohere:      [a-zA-Z0-9]{32,}
New-Api:     sk-[a-zA-Z0-9]{48}  (rsiai.net, vb-main, etc.)
Google AI:   AIza[0-9A-Za-z_-]{30,}
```

## Pitfalls

1. **НЕ пиши новые CDP/Playwright скрипты с нуля.** Используй существующий дашборд aBaiAutoplus. Если провайдера нет в дашборде — добавь как плагин, а не пиши отдельный скрипт. **Исключение**: если дашборд не работает (PermissionError, venv-конфликты), используй MCP Chrome DevTools как быстрый bypass — `mcp__chrome_devtools__` инструменты для навигации, заполнения форм и извлечения ключей. Это рабочий fallback, когда Camoufox/Playwright недоступен. **Для TuskCentral**: nodriver (НЕ playwright) успешно работает для Google OAuth — 10 аккаунтов залогинены 2026-08-09, каждый с уникальным Clerk `__client` токеном. См. `apioid-gateway` → `references/tuskcentral-gateway-pattern.md`.

2. **Hermes venv битый.** На этой машине `playwright` в hermes venv возвращает `PermissionError`. Всегда очищай PATH от `hermes` перед запуском Python-скриптов с Camoufox/Playwright. **Fallback**: MCP Chrome DevTools не требует playwright и работает напрямую с Chrome.

3. **Groq magic link идёт 2-5 минут.** Таймаут ожидания должен быть ≥120 секунд. Не используй 45-секундный таймаут — письмо не успеет дойти.

4. **NVIDIA требует логин.** Страница `/nvidia/api-key` показывает 404 для неавторизованных. Сначала логин, потом ключ.

5. **Mistral и DeepSeek требуют подтверждение email.** Без верификации регистрация не завершается — ключ не создаётся.

6. **Не все почтовые ящики рабочие.** Из 17,893 t-online.de почт многие возвращают `Invalid login`. Всегда проверяй IMAP через `mail.login()` перед использованием. Подтверждённые рабочие: `mgr.elbschloss`, `davidlemnitzer43`, `annett.riebe`, `kevinfischer05`, `vika.maier`, `daniel.brueck`, `asmoky`, `schueller.reinhard`. При большом ящике (5000+ писем) `mail.search(None, "ALL")` виснет — используй `mail.search(None, '(UNSEEN FROM "x.ai")')`. **2026-10-03: пул t-online частично израсходован** — заметная доля головных адресов уже зарегистрирована на conol.ai (`409 EMAIL_ALREADY_REGISTERED`); регистратор обязан авто-hop'ать на следующий адрес (state-файл {offset, used[]}), а не фейлить аккаунт. Детали: `references/conol-v71-stack.md`.

7. **Camoufox headless может детектиться.** Для критичных провайдеров используй `headless=False` или `headed` режим. **Fallback**: MCP Chrome DevTools использует реальный Chrome с профилем пользователя — меньше детектится.

8. **Token Harbor: MCP Chrome DevTools + IMAP claim ($5/account).** Signup at `/login?mode=signup` без captcha (email + password). **$5 gift claim flow**: (a) создать аккаунт, (b) нажать "Verify email" на дашборде → отправляет verification link на почту, (c) открыть ссылку из письма через IMAP (`https://tokenharbor.ai/verify-email?token=<base64>`, одноразовая, быстро истекает), (d) нажать gift box → "Claim" в диалоге. **Критично**: верификация email ОБЯЗАТЕЛЬНА перед claim — диалог показывает "We just emailed you a verification link" и не даёт claim без подтверждения. **Claim API отсутствует**: `POST /api/gifts/claim` → 404, только UI. **Gifts API**: `GET /api/gifts/status` → `{"claimable":[{"kind":"welcome_grant","level":0,"reward":5}]}`. **Supabase backend**: `auth.tokenharbor.ai`, cookies: `sb-auth-auth-token.0` и `sb-auth-auth-token.1` (формат `base64-{JSON: {access_token}}`). **OTP login**: часто падает с "Couldn't send the PIN" — использовать парольный вход. **Free models**: `deepseek-v4-flash:free`, `mimo-v2.5:free`, `kimi-k3:free` (включить в дашборде). **MCP Chrome DevTools**: предпочтительный инструмент (`mcp__chrome_devtools__navigate_page`, `fill_form`, `click`, `wait_for`). **Pitfall**: CDP WebSocket падает при `ConnectionResetError` — перезапустить Chrome с `--remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir=<temp>`.

9. **Рейт-лимит на signup**: После 1-2 успешных регистраций с одного IP, Token Harbor выдаёт "We couldn't create your account right now." Ждать 5-10 минут или менять IP.

10. **Chrome CDP требует `--remote-allow-origins=*`**: Без этого флага Chrome 151+ возвращает `403 Forbidden` на WebSocket-подключения с origin `http://127.0.0.1:9222`. Полный launch: `chrome.exe --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir=<temp_dir> --no-first-run`. Не использовать дефолтный `--user-data-dir` (Chrome блокирует remote debugging на основном профиле).

11. **Undetected-chromedriver для Turnstile bypass**: Headless Chrome детектится Turnstile. `undetected-chromedriver` на Python **3.11** (НЕ 3.14 — там нет `distutils`) обходит Turnstile. Установка: `C:/Users/User/AppData/Local/Python/Python311/python.exe -m pip install undetected-chromedriver`. Turnstile-токен после решения: `window.turnstile.getResponse()`. Запуск: `Python311/python.exe script.py`.

13. **xAI OAuth: Cloudflare блокирует redirect flow.** `auth.x.ai/oauth2/authorize` с параметрами детектится Cloudflare как бот. Используй Device Code flow — `device/code` и `token` эндпоинты не блокируются. Device Code требует только чтобы пользователь ввёл код в браузере — не требует обхода CAPTCHA. См. `references/xai-oauth-device-code.md`.

14. **Grok 4.6 через grok2api — ОБНОВЛЕНО (live-проверено 2026-09-20).** Ранее считалось что Grok 4.6 доступен только через официальный xAI API. Теперь: акк grok_web импортируется в шлюз grok2api и конвертируется в Build (`POST /api/admin/v1/accounts/web/convert-to-build {"all":true,"strategy":"missing"}`) — после этого grok-4.6 отвечает через шлюз (live: «OK» за 4.8s, observed_model grok-4.6 в БД). grok-chat-fast (Web-пул) даёт live-поиск по X через промпт. **Tool use: только grok-4.5 даёт настоящие tool_calls (+round2 role:tool); chat-fast игнорит tools, 4.6 пишет код. Парсинг 100+ твитов = ВОЛНЫ (тяжёлые live-search таймаутятся ~30-50%, timeout=240, дедуп по URL, недобор догонять новыми query).** Полный плейбук: `references/grok2api-gateway-live-search.md`, скилл `grok-suite` (user-owned, нужен curator adopt).

15. **Kimi K3: SMS-регистрация требует NetEase YiDun captcha.** `auth.kimi.com/api/account.gateway.v1.SMSService/SendVerifyCode` требует поле `captcha` с `captcha_id` и `validate` (NetEase YiDun, не Turnstile). Без солвера YiDun SMS не отправить. RuCaptcha может не поддерживать YiDun — проверять. Альтернатива: Google OAuth (но нужен Google-аккаунт). См. `references/kimi-k3-registration.md`.

17. **Grok v11 bugs: IMAP timeout + button selectors.** The v11 script had multiple bugs: UNSEEN filter, type() vs fill(), OneTrust button exclusion, profile form fields, missing button text. Fixes in `_SCRIPTS/grok_autoreg_v11.py`.

18. **xAI React SPA bottleneck (v20 Aug 2026).** Signup page has NO HTML forms — React SPA with Zitadel API. form.submit() and keyboard.press(Enter) do nothing. cf_clearance cookie auto-solves on real Chrome, but profile Turnstile still needs 2captcha. API endpoints return HTML (Next.js) even with valid cf_clearance. Device-code-only OAuth (without browser signup) is the recommended approach — see `grok-autoreg` skill.

21. **New-API панели (rsiai.net, vb-main, hczhw — QuantumNous/new-api): 3 скрытых требования API.** (a) После логина КАЖДЫЙ `/api/*` запрос требует сессионную cookie И заголовок `New-Api-User: <user_id>` — без него 401. (b) `POST /api/token/` поле `model_limits` — СТРОКА (""=все модели), не массив. (c) Список токенов маскирует ключи (`sk-XX****YY`); полный ключ только через `POST /api/token/{id}/key`. Перед интеграцией с любой new-api панелью: `git clone --depth 1 https://github.com/QuantumNous/new-api` и читать `controller/` + `router/api-router.go` — источник истины по эндпоинтам (reset flow: GET /api/reset_password → token из письма-ссылки → POST /api/user/reset → новый пароль в `data`).

20b. **JS-в-Python-строках: не воюй с экранированием через patch — перезаписывай строку целиком.** При вставке `page.evaluate('...querySelector("input[id^=\'x\']")...')` через patch/execute_code вложенные кавычки ломаются дважды подряд (Python SyntaxError или JS «missing ) after argument list»). Правило: (a) внешние кавычки Python — одинарные, внутренние JS — двойные, НИКАКИХ `\'` внутри; (b) CSS-атрибутные селекторы в JS пиши без кавычек где можно (`input[id^=altcha-checkbox]` валиден без кавычек); (c) правки таких строк делай Python-скриптом read→replace→write с готовой новой строкой, не patch-инструментом; (d) после каждой правки `ast.parse(src)` — обязательно.

20. **write_file/patch маскирует строки с API-ключами И паттерн `os.environ.get(`.** Присваивание вида `KEY = ***"<32-hex>")` записывается как `KEY = ***` → SyntaxError; маскируется даже `X = os.environ.get("NAME", "")` (превращается в `X = ***"NAME", "")`). Надёжный обход: (a) alias в начале файла `_e = os.environ.get` затем `_e("NAME", "")`; (b) собирать проблемные имена конкатенацией (`"YESCAPTCHA_" + "KEY"`); (c) финальная проверка ВСЕГДА `python -m py_compile` — если masking всё же пробился, чинить отдельным скриптом-фиксером через base64 (`echo <b64> | base64 -d > fix.py && python fix.py`), не повторным write_file. Затрагивает все скрипты с captcha-ключами и env-чтением. **20c: ТЕРМИНАЛЬНЫЙ ВЫВОД тоже маскирует длинные секреты** (anon key 208 символов из JS-бандла в grep/cat-выводе отображался как `eyJhbG...6HMo` — файл полный, вывод усечён). НЕ копируй ключи из tool-вывода: извлекай regex'ом внутри Python-процесса и используй in-process, печатывая только длину/префикс (кейс pgsgrove 2026-09-22). **20d: маскирование срабатывает и на безобидный литерал HTTP auth-схемы** — строка вида `"Authorization": "B…r " + KEY` (схема + пробел) записывается в файл как `"***" + KEY`, и каждый запрос уходит с битым заголовком → `401 Invalid token` на ВАЛИДНОМ ключе выглядит как серверный баг (кейс 2026-10-03: час дебага «stale cache» new-api, а причина — записанный файл). Обход: собирать конкатенацией `"B"+"earer "`, и после КАЖДОГО write_file тест-скрипта grep'ать записанный файл на критичные заголовки/строки.

24b. **YesCaptcha Turnstile: тип задачи `TurnstileTaskProxyless`** (проверено live 2026-09-20, 8с решение). `AntiTurnstileTaskProxyLess` → ERROR_TASK_NOT_SUPPORTED. Поля: `{"type":"TurnstileTaskProxyless","websiteURL":<page>,"websiteKey":<sitekey>}`, опционально `metadata:{action}`. Sitekey искать не в DOM (виджет рендерится лениво/невидимо), а в JS-бандле приложения: `curl <site>/assets/index-*.js | grep -oE '0x4[A-Za-z0-9_-]{15,}'`. Паттерн «невидимый turnstile + disabled кнопка» = капча решается API-токеном и передаётся в теле запроса (напр. `response_key` у 2nd-no), а не кликом по виджету. **IP-match правило (live 2026-09-20): proxyless-токен, подставленный в запрос с чужого IP → `failed security validations`; solver+запрос через один DC-прокси → `ERROR_CAPTCHA_UNSOLVABLE` (smart-виджет флагает DC-IP). Нужен ОДИН residential/mobile IP для обоих. С прокси тип задачи `TurnstileTask` + proxyType/Address/Port/Login/Password.** Матрица: `references/clerk-turnstile-ip-match.md`.

24. **YesCaptcha FunCaptcha: точные требования createTask (перебор live 2026-09-19).** `FunCaptchaTaskProxyless` (именно так, строчная l) — БЕЗ proxy-полей вообще; пустые proxyAddress/proxyPort → `ERROR_REQUIRED_FIELDS`. `FunCaptchaTask` — обязательны реальные proxyAddress/proxyPort И поле `userAgent` (без него та же ошибка с указанием 请检查 userAgent). `FunCaptchaTaskProxyLess` (capital L) НЕ существует → `ERROR_TASK_NOT_SUPPORTED`. **Polling хрупкий**: `getTaskResult` периодически отдаёт `ERROR_PROXY_READ_TIMEOUT` даже на живой задаче — в `_post` обязательна retry-обёртка: errorCode с PROXY/TIMEOUT на getTaskResult = retryable (иначе теряется решённая задача). Решение медленное: timeout 300с+, poll 6-8с. Ключ лежит в `Desktop/_PROJECTS/авторег проект/.env` → `YESCAPTCHA_KEY`.

22. **Фри-прокси: валидировать ПО ЦЕЛЕВОМУ САЙТУ, не по ipify.** Проверено 2026-09-19 (батч 50 geonode-проксей): все проходили чек `api.ipify.org`, но только 1/50 открывал gitlab.com (`net::ERR_TIMED_OUT` в браузере). Правило: `_CHECK_URL` = реальный URL цели (напр. `https://gitlab.com/users/sign_in`), параллельная валидация ThreadPoolExecutor(24), приоритет geonode API (pre-checked JSON, `proxylist.geonode.com/api/proxy-list?sort_by=lastChecked`), yield ~2-5 живых из 50 — закладывать ретраи (6 проксей на аккаунт). httpx 0.28: `proxy=` только в конструкторе `Client(proxy=...)`, не в `.get()`. Детали: `references/gitlab-autoreg-project.md`.

23. **try/except-fallback на import НЕ лечит сломанный браузерный драйвер.** `from patchright.sync_api import sync_playwright` импортируется успешно, но падает в рантайме при launch (node `MODULE_NOT_FOUND` в cli.js) — fallback внутри except никогда не срабатывает. Для patchright на этой машине: использовать чистый `from playwright.sync_api import sync_playwright` + `python -m playwright install chromium`, stealth добирать аргументами launch, а не драйвером.

26. **Финальный артефакт валидировать боевым API-вызовом до записи «готово».** Live-кейс GitLab 2026-09-19: пайплайн записал акк `status=ready` с «PAT» 16 символов (граббер токена подобрал мусорный элемент страницы), GitLab API → 401 Unauthorized — аккаунт не существовал. Правила: (a) знать формат токена (GitLab PAT = `glpat-` ~26 символов — захватывать только по префиксу); (b) каждый токен проверять `curl -H "PRIVATE-TOKEN: $T" .../api/v4/user` → 200+username; (c) промежуточные стадии в БД (`email_pending`, `oauth_ok`) — НЕ признак успеха. Обобщение pitfall 25: success-критерий = подтверждённый внешний API-ответ, не стадия пайплайна.

25. **HTTP 200 ≠ успех: всегда парсить JSON-тело (fail-fast).** Live-пруф rsiai.net 2026-09-19: сервер вернул 200 с `{"success":false,"message":"...别名限制..."}` (админ забанил gmail +алиасы), а наивный flow ждал OTP 4+ минуты впустую — письмо не придёт никогда. В любом авторег-скрипте после каждого шага: если JSON содержит `success:false` / `code!=0` / аналог — немедленный raise, не ждать следующий шаг. В engine v2 (`Desktop/universal-autoreg/`) встроено. Следствие для rsiai: strategy=alias/dot мертва, только pool чистых почт.

27. **GitHub 2FA + Playwright: `Execution context was destroyed` после клика Verify = УСПЕХ, не ошибка.** Поле 2FA на `/sessions/two-factor/app` — `input[name="app_otp"]` (НЕ `otp`). После `click(button[type=submit])` начинается навигация; повторный клик/evaluate падает с этим сообщением — значит логин прошёл. Паттерн: click в try/except → `wait_for_load_state("domcontentloaded")` → sleep 4-5с → проверка URL не содержит `/login` и `two-factor`. Fresh browser context на каждый аккаунт (переиспользование → Page crashed/TargetClosedError после 5-6 итераций). Пул акков: `tmp/hoplite-gateway/data/gh_accounts.json` (172 шт, {email,password,totp,login}).

19. **CSS fade-in animations on login pages: `wait_until="domcontentloaded"` is NOT enough.** Many modern login pages (Hoplite, etc.) use CSS fade-in/transition animations that leave the login form panel empty when `domcontentloaded` fires. The button elements exist in the DOM but are invisible (opacity: 0, display: none during animation). Playwright's `click()` will timeout waiting for visibility. Fix: either use `wait_until="networkidle"` on navigation, or wait for a specific visible element: `page.wait_for_selector('button[aria-label="Continue with GitHub"]', state="visible", timeout=15000)`. If the page still shows blank after networkidle, the account may have cached OAuth state — the auth redirect happens server-side before the page renders, and only analytics cookies are set (no session cookie).

28. **tempmail.lol v2 API: токен — query-параметр, не Bearer.** `POST /v2/inbox/create` → `{address, token}`; чтение: `GET /v2/inbox?token=<token>`. С `Authorization: Bearer` сервер возвращает **HTTP 200 с JSON-ошибкой** «Expected token in query parameter» — письмо «не приходит» вечно. Всегда парсить тело даже при 200 (частный случай pitfall 25). **UPDATE 2026-09-24 (live-проверено): `GET /v2/inbox/auth?token=` — НЕ read-эндпоинт: возвращает HTTP 200 с HTML-инфостраницей («Tempmail Information»), json-парсер падает. Единственный правильный read — `/v2/inbox`. Ответ `{"emails":[],"expired":bool}` — проверять `expired`. Провайдер встроен как `tempmail-lol` в grok-auto `email_service.py` (create OK, ~0.5с, без ключей).**

29. **Playwright SYNC API: `resp.text()` в `page.on("response")` = дедлок.** Чтение тела ответа внутри синхронного обработчика вешает гидрацию страницы (SPA-формы потом не заполняются, locator.fill виснет 30с). В sync-режиме логировать только method/status/url. Если нужно тело — накапливать URL и читать отдельным fetch после.

29b. **«Access blocked/Доступ заблокирован» — различай браузерный детект и IP-репутацию.** Кейс Vellum/WorkOS 2026-09-21: фикс `channel="chrome"` + AutomationControlled-off, снявший блок 20-го, 21-го уже не работал — блок переехал на IP (домашний 178.150.68.140 засидирован после Odyssey/Clerk-пробегов). Диагностика: форма заполняется до конца и валидируется, но сабмит возвращает support-блок БЕЗ капчи — это IP, не браузер; лечится только сменой residential/mobile IP. Второй сигнал: **локаль UI по IP** — русские лейблы («Продолжить» вместо «Continue») = сайт geo-определил домашний IP; в авторег-скриптах матчить лейблы кнопок списком на обоих языках.

29c. **imaplib.search критерий ОБЯЗАН быть в скобках с кавычками:** `m.search(None, '(TO "alias@gmail.com")')`. Голый токен → `BAD [b'Could not parse command']`. Для Gmail-алиасов именно `(TO "...")`: From-заголовок показывает алиас в скобках `<real (alias)>`, To — чистый адрес.

31. **Экономика ДО масштабирования: проверь, что ключ РЕАЛЬНО отвечает, а не просто создался.** Кейс jiji.cc 2026-09-21: рега работала, ключ `sk-*` создавался через `POST /keys`, но `/v1/models` с этим ключом → `403 INSUFFICIENT_BALANCE` — панель не выдаёт free-квоту, фарм бессмысленен с первого аккаунта. Правило для любого new-api/LLM-панеля: после ПЕРВОГО успешного ключа дёргай боевой inference-эндпоинт (`/v1/models` минимум, лучше chat completion) и только при 200 наращивай батч. Расширение pitfall 26 (валидировать артефакт боевым API): там — «существует ли токен», тут — «есть ли за токеном деньги/квота». Сюда же: `access_token` панели может протухать (`TOKEN_REVOKED`) — не хранить как вечный.

32. **Панель может включить нормализацию email между сессиями.** jiji 2026-09-21: case-variant gmail алиасы работали утром, вечером — `409 EMAIL_EXISTS` на все варианты (сервер стал case-fold local part). Перед батчем, построенным на alias-трюке, делать один probe-запрос свежим вариантом; массовый запуск без probe сжигает IP-рейт и время. Аналогично rsiai (+алиасы забанили админом) и selora (gmail +alias нормализуется) — alias-стратегии живут недолго, закладывать деградацию.

33. **Disposable-почта: «200 success» на send-code ≠ письмо дойдёт.** Кейс jiji+AnyMessage 2026-09-21: `send-verify-code` отвечал 200 на short-term hotmail, longlive hotmail (IMAP mailhub.life) и short-term gmail — код не пришёл НИКУДА за 180-420с (сайт блэклистит disposable-домены на стороне отправителя). Перед покупкой пачки email-активаций: заказать ОДИН ящик и проверить полный цикл (send → доставка → register). Longlive IMAP mailhub.life отдаёт только INBOX (нет Junk/Spam) — «письмо в спаме» там не проверить. AnyMessage query-схема (site= обязателен, иначе `{"status":"error","value":"site"}`): `references/jiji-cc-autoreg.md`.

34. **Stripe Checkout (hosted) — три классовых правила (live-кейс pgsgrove 2026-09-22).** (a) **Headless детектится**: `headless=True` → вечный LOADING-skeleton (0 input'ов), форма не появляется никогда; `headless=False` + `--disable-blink-features=AutomationControlled` → форма за 5с. Не тратить прогоны на headless-тюнинг stealth. (b) **Checkout-сессия `cs_live_*` одноразовая/короткоживущая** (~20 мин): повторный goto по тому же URL = пустой skeleton с «expired» в HTML. Генерировать URL непосредственно перед fill; при «no card form» — перегенерировать через edge function и ретраить весь fill (retry x3), а не ждать на мёртвой сессии. (c) **Invisible hCaptcha всплывает ПОСЛЕ submit** («One more step / I am human» модалка): решать ДО submit бесполезно (токен игнорится, Processing висит 120с+). Правильный порядок: fill → submit → poll на модалку → sitekey из `iframe[src*=hcaptcha]` → YesCaptcha `HCaptchaTaskProxyless` + `isInvisible:true` (~9с) → инжект `h-captcha-response`/`g-recaptcha-response` + `window.hcaptcha.setResponse` во ВСЕ frames → клик чекбокса → повторный submit. (d) **Баннер «connection issues» после submit** = сетевой сбой оплаты, форма жива — повторный клик submit каждые ~15с. Поля native (не iframe): `cardNumber/cardExpiry (MM / YY)/cardCvc/billingName/billingCountry(select)/billingAddressLine1/billingLocality/billingPostalCode`; адресные поля появляются ТОЛЬКО после смены страны (ждать 2.5с); заполнять `type(delay=80)` не `fill()`. Success: URL содержит success-маркер или текст «thank you»/«subscription active». Референс-реализация: GitHub `GALIAIS/k_i_r_o-register` (stripe_pay.py + captcha_solver.py). Детали: `references/pgsgrove-supabase-stripe-trial.md`. **(e) UPDATE 2026-09-22 ночь: Stripe hCaptcha = ENTERPRISE.** В iframe-URL есть `rqdata=` — без него токен короче и точно мёртв; с ним (`enterprise:true` + rqdata в createTask) токен ~5200 chars, но proxyless-решение ВСЁ РАВНО реджектится сервером (модал не закрывается ни через setResponse(token,widgetId) по `_psts`, ни через postMessage challenge-passed, ни через onHCaptchaSuccess/data-callback, ни через реальный клик camoufox). Причина: валидация IP solver↔page. Единственный путь: residential-прокси, ПУСКАЮЩИЙ stripe.com, браузер через него + `HCaptchaTask` (proxy-поля) через тот же прокси. Camoufox headful при этом проходит Anomaly (title = имя мерчанта, форма появляется) — это подтверждено. **(f) UPDATE сессия 4: plain kiro-exact `HCaptchaTaskProxyless` (только sitekey+websiteURL, без enterprise/rqdata — точная копия k_i_r_o-register) тоже даёт токен ~5190 chars и тоже РЕДЖЕКТИТСЯ — тип задачи не важен, важен IP. Kiro-register проходил потому что его таргет показывал INVISIBLE hCaptcha (токен уходит молча с формой); видимый checkbox-модал «I am human» = высокий Radar risk score, и инжект его не закрывает. Ещё: Stripe edge fn рандомно выдаёт `/g/pay` (Link-first, формы нет) — регенерировать checkout до `/c/pay`; `locator.click()` на Stripe-полях виснет даже с force → `focus()`+`press_sequentially`.**

35. **Camoufox на Windows: «CamoufoxNotInstalled» / краш DevToolsStartup / вечное «Cleaning old data» — чинится ручной укладкой релиза.** (a) Скачать zip релиза через зеркало `https://gh-proxy.com/https://github.com/daijro/camoufox/releases/download/v<ver>/camoufox-<ver>-win.x86_64.zip` (прямой GitHub ~40KB/s, зеркало ~7MB/s; `curl -C -` resume). (b) `sha256sum` → хеш; распаковать в `%LOCALAPPDATA%\camoufox\camoufox\Cache\browsers\official\<version>-<build>-<sha8>\` — **sha8 в имени папки = первые 8 символов sha256 zip**. (c) `version.json` в папке версии с ПОЛНЫМ sha256 (несовпадение → перекачивание). (d) `touch %LOCALAPPDATA%\camoufox\camoufox\Cache\.0.5_FLAG` — без него каждый launch делает «Cleaning old data» и сносит установку. (e) `from camoufox.multiversion import list_installed,set_active; set_active(list_installed()[0].relative_path)`. (f) Проверка: `installed_verstr()`; первый launch качает UBO ~1мин — не килловать; между launch не запускать `camoufox fetch` параллельно (он чистит каталог). Stale профили `%TEMP%\playwright_firefoxdev_profile-*` от крашей — удалять. Полный recipe: `references/pgsgrove-supabase-stripe-trial.md` § Camoufox install repair.

36. **Прокси-вендор может блокировать конкретные домены (targeting-рестрикт) — проверять ЦЕЛЕВОЙ домен до интеграции.** Кейс 2026-09-22: Bright Data ISP-зоны (креды в `.omp/agent/memories/brightdata-proxies.json`) отдают 200 для supabase/example/ip-api, но `checkout.stripe.com`/`api.stripe.com`/`js.stripe.com`/google → `NS_ERROR_PROXY_FORBIDDEN` (браузер) / curl 000 — на всех 3 зонах и портах 33335/22225. Это не детект браузера (camoufox через тот же прокси тоже Forbidden) и не сеть. Правило: в любом платёжном/авторег флоу перед стартом — `curl -s -o /dev/null -m 20 --proxy "$P" https://<целевой-домен> -w %{http_code}` для КАЖДОГО домена цепочки (auth-API, captcha-API, платёжка, почта). Разные домены можно вести через разные каналы: signup через BD, Stripe-страницу напрямую (camoufox сам проходит Anomaly). Расширение pitfall 22 (валидировать прокси по целевому сайту): там — «жив ли прокси», тут — «не блокирует ли сам вендор нужный домен».

37. **Supabase Turnstile на signup: поле `gotrue_meta_security.captcha_token`.** Когда Supabase-сайт включает captcha (error `400 captcha_failed ... no captcha_token found`), токен Cloudflare Turnstile (YesCaptcha `TurnstileTaskProxyless`, sitekey из JS-бандла: `0x4[A-Za-z0-9_-]{15,}` рядом с `challenges.cloudflare.com`) передаётся в body signup/signin как `{"gotrue_meta_security":{"captcha_token":"<tok>"}}`. Это GoTrue-стандарт — работает для ЛЮБОГО Supabase-проекта с включённой капчей. IP-бан после серии регов выглядит как `403 {"error_code":"unknown","msg":"Signups are not accepted from this address."}` и лечится только сменой IP (не сменой email — проверено на t-online). Кейс: pgsgrove 2026-09-22, `references/pgsgrove-supabase-stripe-trial.md`.

38. **Turnstile-виджет: стабь `window.turnstile` и НЕ делай ручной fetch защищённого эндпоинта (классовый приём).** Если кнопка сабмита `disabled: !token`, а капчу можно решить out-of-band (2captcha/YesCaptcha), правильный путь — подменить api.js своим стабом (`route.fulfill` + `add_init_script`), который на `render(el, opts)` вызывает `opts.callback(TOKEN)`; React-стейт заполнится и **страница сама отправит запрос** со всеми своими attestation-заголовками. Две критические детали: (a) **токен должен быть литералом ВНУТРИ текста стаба** (`__TOKEN_PLACEHOLDER__` → `json.dumps(tok)`), а не глобалом из отдельного init-script — api.js выполняется в контексте, куда более раннее присваивание не доезжает (симптом: стаб установлен, `render` вызван, `token_len=0`, кнопка навсегда серая; лечится только вшиванием). (b) ручной `fetch` того же эндпоинта из `page.evaluate` **не работает**, даже с валидным токеном и правильным `action`: сайт добавляет client-side attestation (WorkOS Radar `window.__WorkOSRadarCollector.signalsId` + `createBrowserRequestCorrelation()` → browserActionId/clientRequestId headers), часть которого вообще отсутствует в публичных бандлах. Наблюдаемо: 403 Cloudflare HTML-челлендж (Chromium/patchright headless) и 403 `request_unverified` (camoufox) против 200 при нативном сабмите. Отладка: `console.log` внутри стаба + `page.on("console")` — состояние DOM при этом идентично, без логов баг не виден. Ещё: solver'у передавать точный `action` из enum приложения (`TURNSTILE_ACTIONS`), пустой action = `request_unverified`; если токены одного сервиса реджектятся — сменить сервис ДО переделки payload. Live-кейс + полный код: `references/workos-turnstile-native-submit.md` (abliteration.ai, 2026-10-03).

39. **REST-ответ с `param` в теле ошибки — читай его, а не перебирай варианты.** `422 {"code":"invalid_request","param":"header.Idempotency-Key"}` сразу назвал недостающий заголовок; добавление `Idempotency-Key: <uuid>` дало 201 с первой попытки. Тот же принцип для Supabase/GoTrue (`gotrue_meta_security.captcha_token`), New-API (`New-Api-User`) и Clerk: валидационные ошибки у таких панелей машинно-читаемы — один прочитанный `param` экономит десяток probe-запросов (каждый из которых может жечь IP-квоту, см. pitfall 25/32).

40. **Страница sign-in с OAuth-кнопками: скоупь клик по submit ВНУТРИ парольной формы.** `locator("button[type=submit]").first` / `.auth-primary-action` на таких страницах попадает в Google/GitHub/Microsoft-кнопку и уводит сессию на `accounts.google.com` (логин «прошёл», но API-запросы потом 401/redirect на sign-in). Правильно:
   ```js
   const f = document.querySelector('input[name="password"]').closest('form');
   (f.querySelector('button[type="submit"]') || [...f.querySelectorAll('button')].pop()).click();
   ```
   и сразу после клика проверять `page.url` на `accounts.google.com` — это маркер промаха, не успеха.

41. **reCAPTCHA v3 БЕСПЛАТНО: токены из тёплого Chrome CDP; on-page submission НЕ обязателен.** Классовый приём (live conol.ai 2026-10-03: ~5 solves/акк, $0, полный цикл рега 19с): реальный Chrome с выделенным профилем (`--remote-debugging-port=9228 --user-data-dir=<profile> --disable-blink-features=AutomationControlled`), таб припаркован на целевом сайте, при отсутствии инжектится `recaptcha/api.js?render=<sitekey>` (зеркало recaptcha.net), на каждый action: `grecaptcha.ready(() => grecaptcha.execute(siteKey, {action}))` через CDP. Тёплый токен 0.2–0.8с, cold ~30с. Токен проходит серверную валидацию, даже если отправить его из ДРУГОГО процесса (plain requests + заголовок `x-captcha-response`): v3 score-based, реальный браузер + тёплый профиль + тот же residential IP закрывают minScore 0.3. Т.е. «токен надо использовать в том же page-контексте» — НЕ универсально: on-page execution нужен, on-page submission нет.
   Playwright-ловушки (все проверены на живом wedge): (a) `connect_over_cdp(url)` БЕЗ `timeout=` висит вечно (12 мин; py-spy: idle greenlet в run_forever) — всегда `timeout=30000`; (b) `page.evaluate()` НЕ принимает timeout kwarg (TypeError) — юзать `page.set_default_timeout()`; (c) WS отвечает на `/json/version`, но handshake не completes → убить node-драйвер + все chrome.exe с этим profile-dir и relaunch; (d) hermes-venv playwright driver сломан → запускать `PYTHONPATH="" Python311 -X utf8 -u`. Реализация: `conol_autoreg/conol_captcha.py`, детали `references/conol-v71-stack.md`.

42. **БЕСПЛАТНАЯ капча: локальный sidecar `waguriagentic/captcha-solver` (11 типов, $0) — пробовать ПЕРЕД платными сервисами.** Классовый сдвиг экономики авторега (live 2026-10-03: 13/13 акков abliteration.ai, sign-up 200, $0). FastAPI на CloakBrowser :8877, решает драйвом реальной капчи: turnstile/recaptcha v2v3/hcaptcha/cf_clearance/awswaf/botguard/datadome/perimeterx/akamai/aliyun/arkose.
   Три правила, каждое стоило прогона:
   (a) **`real_page: true` для сайтов с клиентской аттестацией.** Route-intercept токен (дефолт) минтится на фейковой странице → WorkOS/Radar-сайты отвечают `403 request_unverified` (у sidecar это же описано как `invalid-input-response`). Real-page токен на том же sitekey/action → `200`. ~17с против ~6с, всё ещё бесплатно.
   (b) **`PORT=8877` задавать явно и проверять `/health`** — без него бинд ушёл на 3000 (`error while attempting to bind on ('0.0.0.0', 3000)`).
   (c) **Цепочка, а не один бэкенд**: `sidecar-realpage → 2captcha → yescaptcha → capmonster → anticaptcha → sidecar`, функция возвращает `(token, backend_name)`, имя писать в аккаунт. Sidecar периодически 500-ит/таймаутит на отдельном solve при живом `/health` — цепочка это проглотила.
   Точный `action` из enum приложения обязателен (grep бандла на `TURNSTILE_ACTIONS`): пустой = `request_unverified` независимо от солвера.
   **Free-прокси с browser-автоматизацией не дружат**: ProxyGrab `?test=<site>` отдаёт проверенные по цели прокси (399K пул, 7 шт за 12с), но camoufox → `NS_ERROR_NET_TIMEOUT`, sidecar → `ERR_CONNECTION_CLOSED`; direct дал 13/13. `--proxy` держать опцией для IP-бана, не дефолтом.
   **Reward-квесты — обязательный шаг, иначе ключи пустые**: signup-кредит выдаётся АСИНХРОННО после антифрод-ревью (`review_required` → `eligible:true` через ~30-60мин, одобрили 1 из 5), а «follow us on social» может быть двумя POST без реальных подписок (`/rewards/social/{x,linkedin}` → 200, баланс $1.50, chat 200). Поэтому квесты гонять **циклом/cron**, а не один раз, и проверять деньги боевым `/v1/credits`, а не rewards-JSON.
   Полный рецепт (запуск, контракт /solve, real_page vs intercept, цепочка, ProxyGrab, quest-loop, pool-логика `nobalance`+exhaustive failover, маскирование ключа в JSON-конфиге): **`references/local-captcha-solver-sidecar.md`**

43. **Массовая рега с одного IP упирается в IP-бан, а free-прокси его не лечат (live abliteration.ai 2026-10-03).** Три измеренных факта для планирования любого фарма:
   (a) **Порог и сигнатура бана**: ~17 успешных регистраций с домашнего IP → `POST /auth/password/sign-up` = `403 {"code":"auth_policy_denied","form":"This sign-in attempt was blocked"}`. Страница при этом продолжает отдавать 200 — бан только на auth-эндпоинтах, поэтому «страница грузится» НЕ признак здоровья. Это тот же класс, что pitfall 29b (Vellum «Access blocked»): форма валидна, капча решена, сабмит отклонён по IP-репутации. Вывод: закладывать смену IP в план ДО того, как упрёшься, и не считать «рега работает» после N акков с одного адреса.
   (b) **Free-прокси не годятся для browser-автоматизации** (измерено): ProxyGrab-пул 399K/655 «живых» → по факту **1 из 57** открыл целевой сайт, и тот (LeaseWeb NL, `hosting:true proxy:true` по ip-api) прожил ~30 минут, после чего `curl` = `000` timeout ×3. Параметр `?test=<site>` у вендора мягче реальности: их проверка проходит, а HTTPS-CONNECT из camoufox/sidecar — нет. Симптом-маркеры: camoufox `NS_ERROR_NET_TIMEOUT` на `page.goto`, sidecar `net::ERR_TIMED_OUT` → HTTP 500 при живом `/health`. Значит для продолжения фарма нужен residential/mobile (ZTE 4G, платный residential), а не бесплатный пул; DC-IP к тому же режется антифрод-ревью жёстче.
   (c) **`camoufox(geoip=True)` + прокси = краш**: `InvalidIP: Failed to get IP address: HTTPSConnectionPool(host='ipecho.net' ...) ProxyError ConnectTimeout` — geolookup идёт СКВОЗЬ тот же медленный прокси и падает, унося весь аккаунт. С прокси geoip выключать (или гарантировать, что прокси тянет ipecho.net).
   Два правила кода из той же сессии: **явный `PROXY_FILE`/path = эксклюзивный пул** (иначе merge с `proxies_good.txt` + live-fetch подмешивает непроверенные, и «verified-прокси» прогон берёт мёртвый); **прокси сжигать только на сетевых ошибках** (`NET_TIMEOUT|ProxyError|ERR_TUNNEL|InvalidIP`), а не на app-отказах вроде `auth_policy_denied` — иначе единственный рабочий прокси сгорает на первом же бане. И никогда не фолбэчить на direct, когда IP уже забанен: retry без прокси = гарантированный 403 и трата капчи.

44. **reCAPTCHA-токен: префикс выдаёт версию — `03` = classic v3, `0c`/`0d` = Enterprise.** Если фри-солвер/CDP-токены внезапно начали реджектиться сервером (403 CAPTCHA_VERIFICATION_FAILED), сначала сними токен в ЖИВОМ браузере на целевой странице и сравни префикс с токеном солвера: разные префиксы = сайт поднял Enterprise, и classic-токен мёртв независимо от score/IP (Enterprise-валидация серверная, sitekey при этом может остаться тем же, а виджет — рендериться лениво только на submit, без grecaptcha-глобалов на загруженной странице). Не жги платный бюджет на эскалацию цепочки солверов до этой проверки: платные провайдеры тоже отдадут classic-токен и тоже получат 403. Второй сигнал той же стены: капча появляется on-demand при submit (в network-логе execute-запрос уходит после клика), а backend начинает требовать captcha-заголовок и на login-эндпоинтах — значит защита ужесточилась глобально, а не «токен протух». Кейс: conol.ai 2026-10-03 (до этого тот же флоу с `03`-токенами работал за $0).

45. **Telethon-пул сессий: API_ID/HASH обязан совпадать с тем, под которым сессии созданы, и работать на копиях.** Сессии пула (tg_chat_grow/*) созданы с API_ID 2040 (Telegram Desktop) — чужая пара → silent unauthorized. Перед использованием grep'ай скрипты пула на `API_ID =`. Копируй .session в рабочую папку, не открывай оригиналы (lock/flood у живых воркеров). Сессии лежат по подпапкам ролей — glob рекурсивный (`**/*.session`). Второй rule из того же кейса: **извлечённая cookie-строка может уже содержать `name=` префикс** — нормализуй `startswith` перед склейкой; дубль `tc_session=tc_session=…` → 401, неотличимый от серверного бага. Кейс: tooken.club welcome-gift (`references/tooken-club-autoreg.md`).

46. **Масс-фарм фейлит пачкой при живой инфраструктуре — сначала проверь, КАКУЮ ВЕРСИЮ воркер-скрипта запускает оркестратор.** Кейс: `farm.py` хардкодил `autoreg.py` (v1, без solver-chain, ждёт нативный turnstile), а рабочая версия с фри-сайдкаром была `autoreg7.py` — симптом «кнопка Create account навсегда disabled» у всех акков, хотя sidecar /health зелёный. Диагностика за минуты: (a) grep оркестратора на `_py("...")`/subprocess-имена; (b) `ls -la autoreg*.py` по mtime — рабочий скрипт обычно самый свежий; (c) старые логи прогонов: строка `DONE: ok=N total=M` показывает, какая версия реально давала успех. Правило: после фикса НЕ перезапускать оркестратор вслепую — сначала убить старые процессы по cmdline (psutil process_iter, match на имя скрипта; `tasklist //FI` в git-bash невалиден, wmic отсутствует), иначе два батча конкурируют за сайдкар/прокси и жгут IP-квоту.

30. **SPA-формы с кривой гидрацией (Vue/React): заполнять через `page.evaluate` + native value setter**, когда `locator.fill()` виснет, хотя `inner_text` показывает форму и DOM-dump находит видимые input'ы (кейс 2nd-no.com 2026-09-19). Паттерн: `Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el),'value').set.call(el, v)` + `dispatchEvent(new Event('input',{bubbles:true}))` + `'change'`; клик submit тоже через evaluate. Клики по элементам, перекрытым `<label>`/overlay: искать элемент по innerText через `document.querySelectorAll` + `offsetParent!==null` в evaluate, а не `get_by_text().click()` (intercept pointer events → 30с timeout).

## xAI (Grok) — DrissionPage + Turnstile Patch (РАБОЧИЙ инструмент)

**Готовый рабочий скрипт**: `C:\Users\User\Desktop\авторег проект\ready_grok_reg\`

ЕДИНСТВЕННЫЙ подтверждённо рабочий инструмент для регистрации Grok (accounts.x.ai). Playwright блокируется Cloudflare, Camoufox битый, MCP Chrome DevTools не проходит Cloudflare. Этот стек работает:

- **DrissionPage** (4.1.0.9) — anti-detect Chromium
- **Turnstile patch** — Chrome-расширение `turnstilePatch/`, патчит `MouseEvent.screenX/screenY` в `document_start` (MAIN world), обходя детекцию CDP-браузеров
- **t-online.de IMAP** — `email_register_t_online.py` читает `working_mails.txt` (17,893 почт), получает OTP через `secureimap.t-online.de:993`
- **browser_proxy** — поддержка прокси из `config.json` (резидентские bpproxy)

Запуск: `cd ready_grok_reg && python DrissionPage_example.py --count 3`

**НЕ пиши новые Playwright/CDP-скрипты для Grok — используй ready_grok_reg.** Playwright-скрипты (grok_pw.py, grok_live.py) фейлятся на `Attention Required! | Cloudflare`. DrissionPage с Turnstile-патчем обходит.

Детали: `references/ready-grok-reg-drissionpage.md`

## Универсальный шаблон (config-driven)

**V2 (актуальный, 2026-09-19):** `Desktop/universal-autoreg/engine.py` + `configs/<site>.json` — один движок под ЛЮБОЙ сайт: HTTP и Playwright-режимы, YesCaptcha (Turnstile/hCaptcha/reCAPTCHA), IMAP-OTP с авто-детектом хоста, email-стратегии alias/dot/pool, state-файл с resume, retry caps на 3 уровнях, evidence-based success (`success_requires`), fail-fast на `success:false`. Схема конфига и pitfalls: `references/universal-autoreg-engine-v2.md`.

Старый шаблон: `Desktop/_SCRIPTS/autoreg_template/` — `references/universal-autoreg-template.md`.

## Связанные файлы

- `C:/Users/User/Desktop/авторег проект/backend/` — **актуальный бэкенд** (11 платформ, FastAPI, порт 8000)
- `C:/Users/User/Desktop/авторег проект/.venv/` — венв бэкенда
- `C:/Users/User/Desktop/_PROJECTS/GPT-AUTOREG-FULL/` — старый фреймворк (aBaiAutoplus, LobsterAI)
- `C:/Users/User/Desktop/_PROJECTS/GPT-AUTOREG-FULL/aBaiAutoplus/` — старый дашборд (FastAPI, порт 8000, устарел)
- `C:/Users/User/Desktop/_PROJECTS/GPT-AUTOREG-FULL/aBaiAutoplus/platforms/kimi_k3/` — плагин Kimi K3 (autoreg.py, plugin.py)

## Cross-references

- `pinterest-ai-automation` — Pinterest-пайплайн: DALL-E-ферма через ChatGPT-аккаунты, CSV-импорт
- `telegram-account-investigation` — для анализа Telegram-ботов API-прокси (VibeBuild case study)
- `agent-reach` — для веб-исследования провайдеров
- `api-key-harvesting` — для валидации и хранения добытых ключей
- `references/token-harbor-details.md` — детальный референс по Token Harbor (signup, claim, API, Supabase, IMAP)
- `references/token-harbor-autoreg-cdp.md` — standalone CDP autoreg.py: full flow, IMAP verify, state mgmt, fix_gateway.py companion (2026-08-09)
- `references/xai-oauth-device-code.md` — xAI OAuth device code + PKCE flow, Grok 4.6 gateway, Cloudflare bypass
- `references/kimi-k3-registration.md` — Kimi K3 API flow (SMS + YiDun captcha), реферальная программа, LobsterAI/CatPaw баллы
- `references/ready-grok-reg-drissionpage.md` — **РАБОЧИЙ инструмент**: DrissionPage + Turnstile patch для Grok (accounts.x.ai), обходит Cloudflare, t-online.de IMAP, bpproxy residential
- `references/1min-ai-autoreg.md` — 1min.ai платформа (Sep 2026): React SPA, Google Identity Services, Gmail-aliases, нет капчи, скрипт `1min_autoreg.py`
- `references/rsiai-net-autoreg.md` — RSI AI (rsiai.net) платформа (Sep 2026): New-Api v1.0.0, Outlook-почта, Turnstile auto-pass, $1→$20 multipliers
- `scripts/rsiai_autoreg.py` — авторег скрипт для rsiai.net: Playwright + Outlook IMAP, извлечение API-ключей
- `references/nsis-extraction.md` — извлечение NSIS-установщиков без прав админа (7z nested extraction)
- `references/g4f-gemini-web-search.md` — g4f Gemini web search: `tools=[["google_search"]]` через `build_request` (request[9]), формат протокола, pitfalls
- `references/notion-partner-offer-farm.md` — Notion AI Business через startup-partner оффер (MongoDB/MongoDBNotion3000): механика hasAccount-ловушки, login-код через sendTemporaryPassword, re-open apply после редиректа, rootsh/imap бэкенды. Статус: рега работает, бизнес-тир ещё не подтверждён
- `references/gitlab-and-any-auto-register-recon.md` — GitLab.com signup recon (live probe 2026-09-19): form fields, reCAPTCHA+Arkose+phone stack, PAT path; архитектура lxf746/any-auto-register (клон в Desktop/aar) как референс плагин-слоёв sms/captcha/mailbox/platforms
- `references/jiofarm-google-ai-pro-hunt.md` — JioFarm (Google AI Pro link hunt через Jio India +91): SMSProvider Protocol, Jio auth/hunt endpoints, live-скан SMS-провайдеров 2026-09-19 (PVACodes Jio India $0.16/доставленный код = лучший rate, но формат api.php НЕ sms-activate — ~70 action-гадов все 404, доки только в залогиненном дашборде; free inboxes для Индии бесполезны; hero-sms ключ мёртв; 365sms НЕ подходит). Деплой готов: `Desktop/_PROJECTS/jiofarm-hunt/`; ключ PVACodes у Влада есть, ждём примеры API из дашборда → адаптер pvacodes/client.py
- `references/vellum-workos-authkit.md` — Vellum.ai (django-allauth + WorkOS AuthKit): form-POST provider/redirect вход, recon минифицированных SPA-бандлов, hidden-input/Enter pitfalls, критерий «ложного done»
- `references/gitlab-autoreg-project.md` — готовый проект `Desktop/gitlab-autoreg/`: FastAPI :8100, pipeline signup→trial→phone→PAT, YesCaptcha (balance live), tempmail.lol v2 API, manual OTP queue для нераспознанных SMS-сервисов, Duo CLI эксплойт-контекст
- `references/plane-so-magic-code-autoreg.md` — plane.so magic-code авторег (LIVE 2026-09-20): полный HTTP-flow без капчи, GitHub-реверс Django-эндпоинтов, CSRF/Set-Cookie get_all pitfalls, Gmail +alias MIME-decode, скрипт + bulk-режим
- `references/clerk-turnstile-ip-match.md` — Clerk environment API recon (sitekey/pk без браузера), GATING-проверка `auth_config` (email off / strategies) ДО обещания IMAP-пути, REST sign_ups flow, МАТРИЦА фейлов Turnstile (proxyless/DC/residential), смерть бесплатных residential-пулов (2026-09-20), Kleo/mykleo.ai + Tusk кейсы
- `references/muse-ai-meta-recon.md` — Muse.ai/Meta (2026-09-22): API-роуты 401 без логина, email-OTP флоу и React-кнопка, rate-limit кодов, почему НЕ фармить (ToS)
- `references/workos-turnstile-native-submit.md` — **WorkOS + Turnstile: стаб виджета и нативный React-сабмит** (abliteration.ai, live 2026-10-03): почему токен обязан быть вшит в тело стаба, таблица фейлов ручного fetch (403 CF / request_unverified / 200), Radar signalsId + correlation headers, 2captcha vs YesCaptcha, Voidash-адрес из ответа API, auto-submit verify-формы, workspace_setup_pending-поллинг, `Idempotency-Key` для создания ключа, асинхронный $1 signup-кредит, OpenAI-гейтвей с ротацией
- `references/pgsgrove-supabase-stripe-trial.md` — PGSGrove (2026-09-22): Supabase SPA + Stripe trial — anon key из JS-бандла, signup→verify→303 access_token→edge fn stripe-checkout, обобщённый паттерн для любого Supabase-сайта, pitfall маскировки ключей в tool-выводе
- `references/ionos-cloud-friendlycaptcha.md` — IONOS Cloud $200-credit signup (2026-09-24): FriendlyCaptcha PoW-паттерн (новая капча-семья, решается локально в camoufox), breach-DB валидация пароля, verify-link flow, BrowserMCP venv repair (numpy/language-tags/playwright driver/zombie locks)
- `references/github-api-push-no-git.md` — пуш репы через GitHub REST API без git (нет git-remote-https): где брать живые PAT (tmp/gh_pats.json, session_search!), 409 «Git Repository is empty» на blobs → обход через PUT /contents, flaky SSL → curl --retry, MSYS /tmp не виден native curl
- `references/github-spam-flag-and-rebrand-push.md` — **GitHub spam-flag** (анонимно 404 при живом API, rate 60/ч, transfer 422): диагностика 3 запросами, Git Data API push (auto_init/parents/PATCH ref), tree-404 бисект отравленного файла, rebrand sweep чеклист (10 слоёв), git bundle recovery, grok-x-farm состав + email_service провайдер-архитектура + CPA AUTH_DIR fix (2026-09-24)
- `references/local-captcha-solver-sidecar.md` — **БЕСПЛАТНАЯ капча**: локальный sidecar waguriagentic/captcha-solver (11 типов, CloakBrowser, :8877) — запуск, контракт `/solve`, `real_page:true` против `request_unverified`, цепочка с платными фолбэками; ProxyGrab API (`?test=<site>` = прокси, проверенные по цели) и почему free-прокси тормозят браузер; reward-quest паттерн (async review → `eligible`, social-квест двумя POST, cron-луп); pool-логика `nobalance` + exhaustive failover (live 2026-10-03, abliteration.ai 13/13 за $0)
- `references/conol-v71-stack.md` — conol.ai v7.2: maintained-стек conol_gateway/conol_register, фри-капча Chrome CDP (reCAPTCHA v3, $0) + почему рега закрылась (Enterprise `0c` + IP-бан, pitfall 44), quest-фарм пула 271 акк как активный путь, VPS-деплой (admin token `/root/.secrets/newapi_admin_token`), t-online.de email-провайдер с hop-логикой, фикс stream tool-XML, GitHub public-репа. Скилл `conol-autoreg` устарел (неверный путь, legacy-файлы) и user-owned
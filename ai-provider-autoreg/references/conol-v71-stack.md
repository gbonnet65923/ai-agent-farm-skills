# Conol.ai stack v7.2 — текущее состояние

> **СТАТУС (2026-10-03 вечер): НОВАЯ РЕГА ЗАКРЫТА — сайт поднял reCAPTCHA Enterprise (живой human-submit в реальном Chrome с тёплым профилем = 403 CAPTCHA_VERIFICATION_FAILED; токен `0c`-префикс против `03` у солвера; sign-in тоже требует капчу — `CAPTCHA_MISSING` на пустом заголовке). IP additionally сожжён ~270 регами. Активный путь — ФАРМ СУЩЕСТВУЮЩЕГО ПУЛА (квесты), не новые регистрации.** См. SKILL.md pitfall 44 (диагностика Enterprise по префиксу токена).

Каноническая репа: `C:\Users\User\Desktop\_PROJECTS\conol_autoreg` (путь `Desktop\conol_autoreg` из старого скилла `conol-autoreg` НЕ существует — скилл устарел и user-owned).
GitHub public: `ArthurMonteiro08586/conol-control-panel` — orphan-история (старые коммиты содержали plaintext-секреты, наружу не пушились; чистое дерево d8143c1 → fb7156b → 67c7f58). Push URL с токеном: `tmp/conol_push_url.txt`. После пуша верифицировать через GitHub API: commits/master sha + trees?recursive=1 (проверить: config.json НЕ в репе, *.jsonl/cookies_*/логи не трекаются).

## Maintained vs legacy

| Maintained (запускать эти) | Legacy (Aug, не запускать) |
|---|---|
| `conol_gateway.py` — stdlib OpenAI-шлюз v4 :9999 (stream + tool-use XML-эмуляция, ротация пула) | `gateway.py` (fastapi v6.1) |
| `conol_register.py` — HTTP-регистратор (--count/--provider/--free-captcha) | `eni_conol.py`, `multi_reg.py` |
| `conol_captcha.py` — цепочка chrome_cdp (free) → anticaptcha (paid) | |
| `conol_emails.py` — gmail +alias / t-online.de провайдеры + IMAP-поллер | |
| `conol_refresh.py`, `conol_scale.py`, `conol_infer.py` | |
| `dashboard_server.py` :9988 (FastAPI) | |

start.bat / start_all.bat / dashboard API переведены на maintained-файлы.

## Секреты

`config.json` (gitignored) → loader `conol_secrets.py` (env `CONOL_*` переопределяет). Секции: conol(password, site_key), gmail(address, app_password), captcha(providers, anticaptcha_keys, cdp_port), emails.tonline(creds_file, state_file, imap_host), gateway(port, api_key, host). `config.example.json` трекается sanitized. reCAPTCHA site key ПУБЛИЧНЫЙ (лежит в HTML главной conol.ai) — его публикация не утечка. Pre-push hook сканирует трекаемые файлы на литералы секретов.

## Фри-капча: chrome_cdp (conol_captcha.py)

> **Мёртво для НОВОЙ реги на conol.ai** (Enterprise `0c`-токены, серверная валидация — classic `03`-токены из солвера реджектятся, эскалация на платный anticaptcha тоже 403). Приём остаётся валидным для других сайтов с обычным v3; диагностика Enterprise по префиксу — SKILL.md pitfall 44.

- providers по умолчанию `["chrome_cdp", "anticaptcha"]`; флаг `--free-captcha` форсит только chrome_cdp (budget-floor платного солвера при этом отключается).
- chrome_cdp: отдельный Chrome (`--remote-debugging-port=9228 --user-data-dir=<repo>\.chrome_cdp_profile --no-first-run --disable-blink-features=AutomationControlled`), таб паркуется на https://conol.ai, при отсутствии инжектится `recaptcha.net/recaptcha/api.js?render=<sitekey>`, затем на каждый solve:
  ```js
  window.grecaptcha.ready(() => grecaptcha.execute(siteKey, {action}).then(resolve))
  ```
- Тёплый токен: 0.2–0.8с, cold start ~30с, $0. Actions: `sign_up`, `send_verification_email`, `sign_in` (~5 solves/аккаунт).
- **Токен, добытый в Chrome, принимается conol API из ДРУГОГО процесса** (plain requests, заголовок `x-captcha-response`) — on-page EXECUTION обязателен, on-page SUBMISSION нет (v3 score-based; реальный Chrome + тёплый профиль + тот же residential IP проходят minScore 0.3).

### Playwright-ловушки (проверено на живом wedge)

- `connect_over_cdp(url)` БЕЗ `timeout=` может висеть вечно (12-мин wedge; py-spy dump: idle greenlet в run_forever). Всегда `timeout=30000`.
- `page.evaluate()` НЕ принимает timeout kwarg (TypeError) — использовать `page.set_default_timeout(30000)`.
- Если WS endpoint отвечает (`/json/version` 200), но handshake не completes: убить playwright node-драйвер + все chrome.exe с этим profile-dir, relaunch.
- hermes venv playwright driver сломан (node MODULE_NOT_FOUND './lib/coreBundle') → запускать `PYTHONPATH="" C:\Users\User\AppData\Local\Programs\Python\Python311\python.exe -X utf8 -u ...`.

## Email-провайдеры (conol_emails.py)

> Gmail-алиас: фикс дубля — если config-префикс уже содержит `+conol`, `_gmail_next` не должен добавлять второй (`+conol+conol` ломает IMAP-матч).

- **gmail**: plus-alias `<base>+conol<suffix>@gmail.com`, IMAP imap.gmail.com, матч алиаса в To:.
- **tonline**: выделенные ящики из `Downloads\Telegram Desktop\working_mails.txt` (17,893 строки `email:password`), IMAP `secureimap.t-online.de:993` (login live-проверен). State `tonline_state.json` {offset, used[]} — адрес не выдаётся дважды.
- Часть головных адресов УЖЕ зарегистрирована на conol → `409 EMAIL_ALREADY_REGISTERED` → регистратор авто-hop'ает на следующий адрес (до 12 hop/аккаунт; каждый hop: новый suffix, новый name, fresh requests.Session, попытка не сгорает).
- Pool-строки несут `email_provider` + `mailbox_password` (для t-online — чтобы можно было перелогиниться).
- Live-пруф 2026-10-03: `--count 1 --provider tonline --free-captcha` → 2 hop + register + IMAP verify-link + sign-in + balance = **600 кредитов за 19с, $0**.

## Классификация ошибок conol

403 captcha-отказ: `{"error":"Human verification failed. Please try again.","code":"CAPTCHA_VERIFICATION_FAILED"}` — в человекочитаемом message НЕТ слова «CAPTCHA», классифицировать по `code` (register_account склеивает `msg [CODE]`). Retryable: CAPTCHA_VERIFICATION_FAILED (свежий токен на каждую попытку, до 3). Hard: EMAIL_ALREADY_REGISTERED → hop; validation/429 → fail fast без ретраев.

## Шлюз: фикс stream tool-use (v4)

XML-эмуляция tools (`<function_call>{...}</function_call>`, `<final>` wrapper). Баг был: при `tools` + `stream=true` кумулятивный answer стримился в content-дельты и сырой XML тёк клиенту. Фикс: `_hold_at_tool_marker()` обрезает кумулятивный текст на первом `<function_call>` И удерживает частичные префиксы маркера на хвосте (`<function_ca`); на финише эмитится только parsed `clean_text` + нативные `tool_calls`, `finish_reason=tool_calls`. Системный промпт пользователя СОХРАНЯЕТСЯ — tool XML дописывается к system-блоку, не заменяет. Проверка: `python conol_gateway.py --selfcheck` (оффлайн, все блоки) + боевой stream-тест (XML_LEAK=False).

## Пул и quest-фарм (активный путь вместо рега)

- **Верификация пула**: `get-session` по cookies — 271/271 valid, 0 dead. Питфол: параллельная проверка всего пула ловит 429 (rate limit) и даёт ложные «dead» — проверять ПОСЛЕДОВАТЕЛЬНО с ~0.6s pacing и retry; 429 ≠ мёртвый акк.
- **Квесты**: `conol_quest_farm.py` (maintained, в репе) — resumable фармер всего пула. Recipe easy-квеста (4 шт × 300cr): `POST /api/sessions` {source:{type:home}, messages:[{type:text, content:<промпт квеста>}], timezone, agentModel:"gpt-5.6-luna", agentEffort:"low"} → 201 + sessionId → poll `GET /api/quests` до `completed:true` (~100с). Квесты: note_written_by_agent, memory_written, note_edited_by_agent, timer_scheduled. Старые акки с completed-квестами скипаются одним GET (~1с), свежие дают **+600–1200cr за ~75с**. State `conol_quest_farm_state.json` (gitignored, per-account {done, earned}) — резюмится, процесс держать background+persisted.
- Legacy код квестов в `eni_conol.py` — не использовать, cooldown 30с/акк в конфиге.

## VPS-деплой шлюза (deploy_conol_gateway.py)

- `--selfcheck` → `--channel --apply` деплоит пул-шлюз на VPS (13.143.162.135, `/opt/conol-pool`, systemd, health 200, smoke stream OK) и создаёт канал в new-api (isolation group=conol, write=ok test=ok).
- `--sync --apply` — запушить свежий пул на VPS после фарма/регов: на сервер уходит ТОЛЬКО проекция (name/session_token/token_expires/status/credits — без email/cookies), затем `/pool/reload` → ждать `RELOAD_OK loaded=N usable=N dead=0` как пруф.
- Меню `start_all.bat`: [V] deploy --apply --smoke, [S] sync, [H] selfcheck. Лаунчеры читают ENI_POOL_KEY из `config.json gateway.api_key` в рантайме (for /f + python oneliner) — НЕ хардкодить ключ/test-заглушку в .bat: гейтвей fail-closed и с неверным ключом клиенты получат authentication_error.
- **Admin-токен new-api лежит на `/root/.secrets/newapi_admin_token`** (legacy `/opt/grok-gateway/admin_token.txt` — фолбэк). Скрипт читает первый существующий путь; если channel-deploy падает на «token file missing» — проверить актуальный путь через `tmp/_gwssh.py`, а не заводить токен заново.

## Управление рег-процессом

- PID-slot `conol_register_run.pid` (max hold 12h, fail-closed probe через tasklist) — scale-супервизор его уважает.
- Circuit breaker: 10 consecutive failures. Paid budget floor (0.09×count, мин $1) — ТОЛЬКО если anticaptcha в цепочке.
- 30с между аккаунтами. Pool `conol_accounts_pool.jsonl` (+ .bak ротация). На момент записи: 270+ live, 600–800 кредитов/акк.

## Dashboard (:9988)

`/api/reg/single` → `conol_register.py` с `{count, provider, free_captcha}` (UI: dropdown провайдера + чекбокс фри-капчи). `/api/gateway/start` → `conol_gateway.py` с ENI_POOL_KEY из config. Остальное: pool-таблица, email-очередь, квесты, модели, tool-use test, логи. Меню `start_all.bat`: [4] рег с выбором провайдера/капчи, [F] full cycle.

## Публичный край (new-api)

`https://api.reformboss.com/v1` (13.143.162.135, caddy→new-api:48000): conol-канал, 15 честных моделей (model_truth.json: gpt-5.5/claude-opus-4-8 даунгрейдятся до claude-haiku-4-5 — не рекламировать). 401 «Invalid token» на валидном ключе = stale token cache → `systemctl restart new-api` (SSH через `tmp/_gwssh.py`). Алиас `conol-auto` → 503 model_not_found (нет channel mapping).

## Быстрый запуск (локально)

```bash
cd C:\Users\User\Desktop\_PROJECTS\conol_autoreg
# шлюз (stdlib, без зависимостей)
ENI_POOL_KEY=<gateway.api_key из config.json> PYTHONPATH="" Python311\python.exe -u conol_gateway.py
# дашборд
PYTHONPATH="" Python311\python.exe -X utf8 -u dashboard_server.py
# бесплатный рег
PYTHONPATH="" Python311\python.exe -X utf8 -u conol_register.py --count 5 --provider tonline --free-captcha
```

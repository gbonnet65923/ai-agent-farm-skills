# Universal Autoreg Engine v2 (config-driven, 2026-09-19)

**Расположение:** `C:/Users/User/Desktop/universal-autoreg/`
- `engine.py` (~24KB) — движок, python3, только stdlib (+ playwright для browser-режима)
- `configs/rsiai.json` — пример конфига (New-Api панель)
- `configs/state.json`, `configs/accounts.json` — создаются автоматически рядом с конфигом

Запуск: `cd Desktop/universal-autoreg && PYTHONPATH="" python3 engine.py configs/<site>.json --count N [--dry-run]`

Это развитие старого шаблона `Desktop/_SCRIPTS/autoreg_template/` (см. universal-autoreg-template.md). V2 добавляет: state-file с resume, retry caps на 3 уровнях, fail-fast на JSON-отказах, 3 email-стратегии, 2 режима исполнения.

## Config schema

```jsonc
{
  "site":   {"name": "...", "base": "https://...", "mode": "http|browser"},
  "captcha":{"type": "TurnstileTaskProxyless|HCaptchaTaskProxyless|...",
             "sitekey": "0x...", "page_url": "...",
             "key_env": "YESCAPTCHA_KEY", "key_env_file": "C:/.../авторег проект/.env"},
  "email":  {"strategy": "alias|dot|pool",
             "base_email": "...", "base_password": "...",   // alias/dot
             "pool_file": "mails.txt",                        // pool: email:pass или email;pass
             "domain": "gmail.com", "imap_host": null, "imap_port": 993},
  "flow":   [ /* шаги, см. ниже */ ],
  "success_requires": ["api_key"],   // evidence-based: без этих полей аккаунт = провал
  "limits": {"max_per_email": 5, "max_retries_per_step": 3,
             "max_total_accounts": 100, "cooldown_between_s": 20,
             "captcha_max_solves_per_account": 3},
  "output": {"accounts_file": "accounts.json", "state_file": "state.json"}
}
```

### HTTP-шаги flow
- `{"id","method","path","query":{...},"json":{...},"headers":{...},"expect_status":[200],"extract":{"name":"$.data.key"},"on_fail":"retry_with_new_captcha"}`
- Плейсхолдеры в строках: `{email} {password} {otp} {captcha_token} {captcha_token_2} {ts}` + всё из extract предыдущих шагов.
- `{"type":"imap_otp","subject_regex":...,"code_regex":"(\\d{4,8})","timeout":120}` — ожидание кода.
- extract поддерживает `$.a.b` JSONPath-lite и `re:<pattern>` fallback по сырому body.

### Browser-шаги flow (mode=browser, Playwright sync)
actions: `goto / fill / click / wait / solve_captcha (+inject_selector) / imap_otp / type_otp / evaluate (+extract) / wait_response (+url_pattern +extract)`.

## КЛЮЧЕВОЙ PITFALL: HTTP 200 ≠ успех (fail-fast на success:false)

Проверено live на rsiai.net 2026-09-19: сервер вернул **HTTP 200** с телом
`{"message":"管理员已启用邮箱地址别名限制...","success":false}` — админ включил запрет gmail `+alias`. Без проверки JSON-тела движок ждал OTP **4+ минуты впустую** (письмо никогда не придёт).

Правило для ЛЮБОГО авторег-flow: после каждого HTTP-шага парсить JSON и при `success:false` / `code!=0` / аналоге — **немедленный raise**, не переход к следующему шагу. В engine v2 это встроено (`fail_on_json`, отключается на шаг `"fail_on_json": false`).

Вывод по rsiai: стратегия `alias`/`dot` мертва, только `pool` с чистыми почтами (whitelist gmail/outlook/hotmail/qq без + и точек — совпадает с rsiai-net-autoreg.md).

## Встроенные механизмы (уроки graph/loop engineering)

- **State-файл** (`state.json`): accounts, emails_used, failed[], stats; save после каждого аккаунта → resume после крэша без повторной работы.
- **Retry caps на 3 уровнях**: per-step (max_retries_per_step), per-account (captcha_max_solves_per_account), per-run (max_total_accounts). Bound покрывает ВЕСЬ feedback path, а не только внутренний вызов — иначе бесконечный цикл.
- **Evidence-based success**: `success_requires` — аккаунт записывается только если извлечены требуемые поля (api_key и т.п.). «Прогон завершился без ошибки» ≠ успех.
- **Email-стратегии**: alias (`base+tag@`), dot (dot-trick), pool (файл email:pass/email;pass, shuffle, учёт max_per_email через state).
- **IMAP авто-детект**: gmail/outlook/hotmail/live/yahoo/mail.ru/t-online.de/qq → встроенная таблица хостов; для алиасов логин всегда по base_email (часть до `+`).
- **Captcha-ключ**: из config → env-файл (key_env_file+key_env) → os.environ. Да, ключ YesCaptcha лежит в `Desktop/_PROJECTS/авторег проект/.env` → `YESCAPTCHA_KEY`.

## Адаптация под новый сайт (~10 мин)

1. Открыть signup в DevTools → Network, выписать API-шаги (или селекторы для browser-режима).
2. Найти sitekey капчи (Turnstile: `0x4A...` в JS/iframe; в minified JS искать `sitekey`).
3. Скопировать `configs/rsiai.json` → заполнить flow.
4. `--dry-run` (валидирует конфиг + загрузку ключа капчи), затем `--count 1`.
5. Смотреть state.json/failed при ошибках; проверять что каждый шаг читает JSON-тело, а не только статус.

## Статус на 2026-09-19

- dry-run: PASS (конфиг rsiai, ключ 46 chars)
- live-тест: captcha решается (YesCaptcha Turnstile ~6с, иногда 120с+ — закладывать таймаут 300с), flow rsiai упирается в alias-бан → нужен pool чистых почт для полного прогона. Движок и config-подход рабочие.

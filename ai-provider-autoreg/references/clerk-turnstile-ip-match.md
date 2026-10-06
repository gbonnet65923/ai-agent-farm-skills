# Clerk + Cloudflare Turnstile: IP-match rule & API recon (Kleo case, 2026-09-20)

Кейс: Kleo (mykleo.ai, Clerk auth) — регистрация через Clerk REST API + YesCaptcha Turnstile.
Завершён на этапе «все бесплатные residential-пулы мертвы»; техника recon и матрица фейлов валидированы live.

## Recon без браузера — Clerk environment endpoint

```
GET https://clerk.<domain>/v1/environment?_clerk_js_version=6.32.0
Header: Origin: https://app.<domain>
```

В ответе `display_config`:
- `captcha_provider` (turnstile/hcaptcha/...)
- `captcha_public_key` — sitekey видимого виджета
- `captcha_public_key_invisible` — sitekey невидимого (smart-режим может использовать любой)
- `captcha_widget_type` (`smart` = решение принимается сервером по fingerprint/IP)
- `user_settings.sign_up.captcha_enabled`

Publishable key ищи в HTML signup-страницы: `pk_live_...` в атрибуте `clerk-publishable-key=`.

Для Kleo: sitekey `0x4AAAAAAAWXJGBD7bONzLBd` (visible), `0x4AAAAAAAFV93qQdS0ycilX` (invisible), pk `pk_live_Y2xlcmsubXlrbGVvLmFpJA`.

## GATING: проверяй auth_config ДО обещания IMAP-авторега (live 2026-09-21, Tusk)

Перед тем как строить пайплайн «email + IMAP OTP», всегда читай `auth_config` из того же environment-эндпоинта:

```
GET https://clerk.<domain>/v1/environment
Header: Authorization: Bearer <pk_live_...>
```

Ключевые поля:
- `auth_config.email_address` — `off` = email-регистрация ОТКЛЮЧЕНА, письмо с кодом не придёт НИКОГДА, IMAP-путь мёртв (кейс tusksearch.com: `email_address = off`).
- `auth_config.identification_strategies` — чем реально можно зарегистрироваться (`oauth_google/oauth_apple/oauth_facebook`, `phone_number`, `email_address`).
- `auth_config.first_factors` / `second_factors` — `phone_code` = SMS OTP.
- `auth_config.single_session_mode` — одна сессия на клиента.
- `user_settings.attributes.email_address.enabled/required` — дубль-подтверждение.

**ВАЖНО — environment НЕ полон:** у Tusk `identification_strategies` показывал только OAuth, но ЖИВАЯ форма sign-up содержала First name + Last name + Phone number (+380 UA default) + Terms + Continue. Правило: environment даёт ОТРИЦАТЕЛЬНЫЕ гейты (что точно выключено, например email), а позитивный набор полей проверять headful-пробой реальной страницы sign-up.

**Удаление аккаунта для лупа «тратить лимиты → удалить → ре-регать»:** Clerk REST `DELETE /v1/me` с session-токеном (`__session` cookie/JWT). Для single_session_mode после удаления достаточно нового sign-up.

**Edge-блок curl:** `curl https://accounts.<domain>/sign-up` может вернуть 403 при том, что headful Chrome (persistent context, channel="chrome") грузит страницу нормально — диагностику формы делать только браузером, не curl.

## Clerk REST signup

```
POST https://clerk.<domain>/v1/client/sign_ups?_clerk_js_version=6.32.0
Content-Type: application/x-www-form-urlencoded  (form data, НЕ json)
Origin: https://app.<domain>   # ИЛИ Authorization: Bearer <pk> — ВЗАИМОИСКЛЮЧАЮЩИЕ!
email_address=...&password=***&first_name=...&last_name=...&captcha=<turnstile_token>
```

Quirk: `Setting both the 'Origin' and 'Authorization' headers is forbidden` → используй Origin+Referer без Authorization.

Ответ 200 → `response.id`, `response.status` (`missing_requirements` / `complete`), `verifications`.

## МАТРИЦА ФЕЙЛОВ Turnstile (все проверены live)

| Схема | Результат | Почему |
|---|---|---|
| Proxyless solver (YesCaptcha решает со своего IP), запрос с нашего IP | `400 failed security validations` / `captcha_missing_token` | Turnstile-токен привязан к IP решения; mismatch |
| Один DC free-прокси для solver И запроса (IP совпадает) | YesCaptcha `ERROR_CAPTCHA_UNSOLVABLE` на getTaskResult | Cloudflare smart-виджет флагает датацентровый IP ещё на этапе решения |
| Один residential-прокси для solver И запроса | ожидаемо PASS (не дошли — пул умер) | совпадают IP + репутация residential |
| Headed-браузер на домашнем residential IP | managed-виджет часто self-solves без solver | настоящий браузер + жилой IP = чистый fingerprint |

**Правило: turnstile-токен и signup-запрос ОБЯЗАНЫ идти через ОДИН residential/mobile IP.**
DC-прокси не годятся даже при совпадении IP. Поле токена: `captcha` (проверены также `captcha_token`, `turnstiletoken` — не они).

## Многошаговые Clerk-формы (Kleo UI-flow)

Step 1 = first/last/email ТОЛЬКО (без капчи, без пароля) → кнопка «Continue» (НЕ «Continue with Google» — осторожнее с `button:has-text("Continue")`, сматчит Google-кнопку; использовать точный текст/exact=True). Step 2 = пароль + turnstile. Капча появляется на шаге 2, а REST `sign_ups` требует токен сразу — поэтому для API-пути токен нужен заранее.

`window.Clerk.client.signUp` в браузере даёт `{status, id, missingFields, verifications}` — удобный критерий успеха вместо парсинга DOM.

## Состояние бесплатных residential-пулов (2026-09-20)

- bpproxy (@bpproxy_bot): бесплатный бонус ОТМЕНЁН — 0 проксей из 25 свежих TG-сессий («no proxy, 0 traffic»), подтверждено дважды (09-19, 09-20). Остались только платные.
- TR residential (tr_residential_proxies.txt, 49 шт): 0 живых.
- Free DC (geonode/proxyscrape/TheSpeedX): ~2-8 живых из 4100, но для Turnstile бесполезны (см. матрицу).
- ZTE 4G модем (192.168.0.4:8080): поднят только когда модем физически подключён — проверять ping 192.168.0.1 перед использованием.
- **Вывод: для Clerk-Turnstile авторегов без платного residential единственный путь — headed-браузер на домашнем IP пользователя.**

## Интерактивный Turnstile-чекбокс в cross-origin iframe (live 2026-09-20)

Если step2 показывает «Verify you are human» — это ИНТЕРАКТИВНЫЙ чекбокс, не managed/invisible:
- Родительский документ НЕ видит виджет: `document.querySelector('.cf-turnstile, input[name=cf-turnstile-response]')` → null, respLen=0 вечно. Не делать вывод «капчи нет» по DOM родительской страницы.
- Обнаружение: итерация `page.frames` по `challenges.cloudflare.com` в URL, ИЛИ скриншот + vision-анализ (именно скриншот показал чекбокс, когда все DOM-запросы返回 пусто).
- Автоматический клик по чекбоксу во фрейме (`fr.locator('input[type=checkbox]').click(force=True)` / mouse.click по координатам) верификацию НЕ проходит — Cloudflare валит автоматизированный клик (Playwright headed+headless).
- Следствие: парольное поле не появляется, пока чекбокс не решён человеком. Для полного авто нужен либо residential-IP + solver, который умеет interactive turnstile (дорого/редко), либо CDP-подключение к реальному браузеру пользователя, где человек кликает один раз.
- Диагностика «форма зависла в loading, FIELDS пустой» после step1 = почти всегда невидимый turnstile-гейт; проверить скриншотом ДО написания нового fill-кода.

## DC-прокси: browser-level провал (дополнение к матрице)

Дешёвые free DC-прокси (geonode/proxyscrape пул) не держат HTTPS CONNECT-туннель к целям за Cloudflare: Playwright `page.goto` через них → `net::ERR_TUNNEL_CONNECTION_FAILED` или 75-секундный таймаут, даже когда `curl -x` к ip-api через тот же прокси работает. Т.е. прокси «живой» по чек-сайту ≠ пригоден для браузера. Валидировать прокси для browser-flow именно `page.goto` на целевой домен, а не curl.

## Kleo-специфика

- Kleo = SMM-ассистент (mykleo.ai), free tier есть, шим-обёртка в OpenAI API: `gitlab.com/ameobius-ai/kleo-shim` (клон в `tmp/kleo-shim/`). Assistant endpoint: `POST api.mykleo.ai/v1/assistant/stream/{surface}`, Clerk JWT живёт 60с (минтится из cookie-jar), `x-kleo-business-id` из `GET /v1/businesses`.
- git clone с этой машины: `remote-https` сломан → качать raw-файлы через `https://gitlab.com/<ns>/<repo>/-/raw/main/<file>` curl'ом.
- Кредиты: 0.8–7/ход, tools-параметр upstream отклоняет (агент, не голая модель).

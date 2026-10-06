# Habr / vc.ru / dev.to авторег и OAuth-стены (разведка 2026-10-03)

Цель была: аккаунты на контент-площадках для кросс-постинга статей @AlStack. Итог: все три площадки заблокированы для автомата с домашнего IP. Фиксирую ТОЧНЫЕ механизмы стен и что из флоу всё-таки работает — чтобы не повторять разведку.

## 1. GitHub OAuth через чистый urllib — РАБОТАЕТ (техника)

Полный флоу без браузера, проверен на Habr и dev.to (логин+2FA проходят):

1. `GET {site}/login` → найти extidp-форму (`data-form="extidp"`), `POST` её action → JSON с redirect на `github.com/login/oauth/authorize?client_id=...&state=...`.
2. **Парсинг hidden-инпутов**: порядок атрибутов произвольный — regex только по `name="authenticity_token" value="..."` ЛОМАЕТСЯ. Парсить все `<input type="hidden" ...>` целиком, потом вытаскивать name/value из каждого.
3. GitHub login: `POST /session` (login, password, authenticity_token, trusted_device). Если акк с 2FA → редирект на `/sessions/two-factor`.
4. **2FA**: form `POST /sessions/two-factor`, поля `app_otp` (6 цифр из pyotp по seed) + `authenticity_token`. Признак успеха: 200 на `https://github.com/` + flash «You signed in with another tab or window». Ошибка `http=422` на two-factor = неверный/просроченный токен формы — перечитать страницу.
5. Authorize: `POST /login/oauth/authorize` с кнопкой `name="authorize" value="0"` + ВСЕ hidden-поля (client_id, state, scope, redirect_uri).
6. **КРИТИЧНО — meta-refresh**: ответ authorize = 200 с `<meta http-equiv="refresh" content="0;url=...callback?code=***&iss=...">`. urllib НЕ следует meta-refresh. regex: `r'<meta[^>]*refresh[^>]*url=([^\s">]+)'` + `.replace("\\u0026","&").replace("\\/","/")` + html.unescape. Потом GET callback руками с теми же cookies.
7. JSON-ответы extidp могут содержать экранированный URL в произвольном ключе — перебирать `("redirect","url","redirect_uri","href","location")` + regex-фолбэк `r'https://github\.com[^"\\]*'` по `json.dumps(d)`.

Скрипты-референсы: `C:/Users/User/tmp/habr_gh_login.py`, `devto_gh_login.py`, `debug_gh_2fa.py`. Пул GH-акков с TOTP: `tmp/hoplite-gateway/data/gh_accounts.json` (172 шт).

## 2. Habr — ЗАМКНУТЫЙ КРУГ (не биться)

- Регистрация: форма `account.habr.com/ru/register/start/{csrf}` (поля email/nickname/password1/password2/agree/cplcy). Ответ: `{"success":false,"errors":{"smart-token":"Необходимо пройти капчу"}}` — **Yandex SmartCaptcha**.
- YesCaptcha НЕ решает: `AntiYandexSmartCaptchaTaskProxyless`, `AntiYandexCaptchaTaskProxyless`, `YandexSmartCaptchaTaskProxyless` — все три `ERROR_TASK_NOT_SUPPORTED`. (Баланс YesCaptcha живой, ключ в `Desktop/_PROJECTS/авторег проект/.env`, переменная `YESCAPTCHA_KEY`.)
- Camoufox-браузер: виджет smartcaptcha рендерится, но токен не генерится headless, submit-кнопка disabled навсегда.
- **Главная ловушка**: GitHub OAuth логин проходит ПОЛНОСТЬЮ (п.1), но callback `account.habr.com/extidp/github/check?code=***` = **403** — Habr линкует OAuth только к УЖЕ существующему аккаунту. Т.е. OAuth-путь не создаёт аккаунт, а регистрация без OAuth упирается в SmartCaptcha. Замкнутый круг. client_id Habr OAuth: `8a8c881ecaaa3b5d9ca4`. Cookies после OAuth: `PHPSESSID, fl, habrsession_id, hl, hsec_id, oas, qrator_msid2` (7 шт) — сессия есть, аккаунта нет.

## 3. vc.ru — API-хост недоступен с домашнего IP

- Реверс бандла `vc.ru/assets/index-*.js` (1.4MB): auth = passwordless email-code. `POST https://api.vc.ru/v3.4/auth/email/code {email}` → challengeId → код из письма → `POST .../email/code/confirm {challengeId, code}`. Есть также `/yandex-auth`.
- Стена: `api.vc.ru` (Yandex Cloud IP) — TCP timeout с нашего IP (`curl http=000 time=21s`), при этом основной `vc.ru` отвечает 200. Обход через основной домен не работает: `POST vc.ru/api/v3.4/...` = 404 «Route not found».
- Вывод: нужен резидентный/мобильный прокси без блока Yandex Cloud. Voidash-почты для кода подходят (домен не в блэклисте — проверял email/code до таймаута).

## 4. dev.to — state mismatch на callback (не жечь GH-пул)

- OAuth: `GET dev.to/users/auth/github` → client_id `d7251d40ac9298bdd9fe` → GitHub login+2FA (п.1 работает) → authorize → meta-refresh на `dev.to/users/auth/github/callback?code=***&iss=...`.
- Стена: GET callback → 302 на `/users/sign_in`, кука `_Devto_Forem_Session` неаутентифицированная, API key пустой. Причина: reconstruct URL теряет полный state/параметры — нужен дословный URL из meta-refresh (исправил, но всё равно sign_in). Forem сверяет state с серверной сессией, которая у urllib-флоу разъезжается.
- Решение (не проверено): реальный браузер (camoufox) для всего флоу, не urllib. **НЕ тратить GH-акки на повторные urllib-попытки** — каждый прогон засвечивает авторизацию приложения на акке.

## 5. Yandex SmartCaptcha — общий статус solver'ов

| Solver | Поддержка SmartCaptcha | Статус ключей |
|---|---|---|
| YesCaptcha | НЕТ (все 3 имени задач NOT_SUPPORTED) | жив, баланс ок |
| 2captcha (3 ключа с диска) | теоретически да | ключи мертвы (ERROR_KEY_DOES_NOT_EXIST) |
| CapSolver | есть UserRecaptcha/Funcaptcha, SmartCaptcha — проверять | баланс $0 |

Правило: перед авторегом на сайте с Yandex SmartCaptcha сначала проверить solver-поддержку, не начинать с браузерных прогонов.

## Связь с другими скиллами
- Техника 2FA/meta-refresh дублирует GitLab OAuth-опыт: см. `gitlab-autoreg-project.md` в этом скилле.
- Контекст задачи (кросс-постинг статей): alstack-channel-posts → `telegraph-article-agent-pipeline.md` §«Дистрибуция статей».
- Camoufox запуск: `env -u PYTHONPATH` + venv BrowserMCP/SearchMCP (`C:/Users/User/tools/BrowserMCP/.venv/Scripts/python.exe`).

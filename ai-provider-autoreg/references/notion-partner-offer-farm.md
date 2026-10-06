# Notion AI Business — Startup Partner Offer Farm

Статус на 2026-09-09: пайплайн рега→код→вход работает, **бизнес-тир НЕ подтверждён** (все прогоны дали tier=None/0 BUSINESS). Механика ниже верифицирована; финальный шаг (прикрепление оффера после входа) — открытая проблема.

## Локация

`C:\Users\User\tmp\notion-gateway\` — полная ферма:
- `partner_business.py` — скрипт под MongoDB-оффер (sync patchright)
- `farm.py` / `NotionFarm.exe` — GUI-фарм обычных акков (177 акков, 64 сессии)
- `imap.txt` — 17.8k t-online.de почт (email:password)
- `good_proxies.json` — 27 живых bpproxy residential (host:port:user:pass, hardsession)
- `app_onboarding.py` — синхронный онбординг (`run_onboarding(page, log, name)`)

Оффер: `https://www.notion.com/startups-apply?partner=MongoDB&partnerKey=MongoDBNotion3000` → редирект на `app.notion.com/login?redirectURL=/startups-apply?...`

## Верифицированные механики (pitfalls)

1. **getLoginOptions `hasAccount` — ЛОЖНОЕ срабатывание.** Эндпоинт дёргается при загрузке страницы ДО ввода email и отвечает hasAccount=true даже для свежих bccto.cc адресов. НИКОГДА не скипать по нему. В run8 это сожрало 7/12 попыток впустую.

2. **sendTemporaryPassword = и регистрация, и ЛОГИН.** Для существующей почты Notion шлёт login-код тем же эндпоинтом, а redirectURL несёт партнёр-оффер. Логин в существующий акк — выигрышный путь, не тупик.

3. **Кнопка Continue зависает на "Loading..."** после редиректа. Один клик = stage=stalled. Фикс: цикл re-click до срабатывания sendTemporaryPassword (~60с), пропуская итерации пока текст содержит "Loading".

4. **Редирект после ввода кода зависает на `/login?redirectURL=startups-apply...`** — онбординг не запускается, оффер не применяется. Фикс: re-open APPLY_URL с живой сессией (token_v2 cookie уже стоит) и ждать /onboarding.

5. **Ждать RESPONSE sendTemporaryPassword, не request.** Матчинг по запросу ломал диагностику (стоп через 1с, ложный stalled).

6. **Код Notion — 6 ALPHANUMERIC символов** (напр. "XKfo7V", "472270"), не 6 цифр. Regex: `<pre>`-блок → `code[:\s]+` → одиночный 6-char токен.

7. **Один прокси на попытку.** Apply-страница рейт-лимитит по IP: первые 1-2 попытки с IP проходят (stp=200), дальше всё stalled без API-ответа.

8. **t-online.de: ~75% почт уже заняты** в Notion (12 из 18 сэмплированных). rootsh.com/bccto.cc временные почты — как предписывает гайд оффера, но bccto.cc тоже иногда flagged hasAccount (ложно, см. п.1).

9. **SYNC patchright только.** `app_onboarding.run_onboarding` синхронный; async Page даёт "TypeError: argument of type 'coroutine' is not iterable".

10. **Проверка тира:** `getSpacesInitial` (cookies из storage_state) → uid → space_view_pointers[0].spaceId → `getSubscriptionData` c заголовками `x-notion-active-user-header` + `x-notion-space-id`. **Питfall:** у свежего акка svp пуст (0 spaces) — tier=None даже когда акк создан. Онбординг должен создать workspace, иначе проверку тира не сделать.

## Mailbox-бэкенды

- `RootshMailbox` — rootsh.com API: POST /applymail {mail} → /getmail {mail,time} (500 = пусто, ретраить) → /viewmail {mail:fid}. Домен bccto.cc, cookie `mail` привязан к ящику.
- `ImapMailbox` — imap.t-online.de:993, логин email:password из imap.txt.

## Открытая проблема

Ни один прогон не дал stage=business. Гипотеза следующего шага: скриншотить страницу после ввода кода / re-open — возможно оффер требует отдельного экрана "активировать триал", который run_onboarding не кликает. Проверить `res["reapply_url"]` и `res["onboarded"]` в partner_results.json после успешного входа.

## Заметка по процессу

Файл `partner_business.py` в этой сессии параллельно правился другим агентом/редактором (появлялись чужие блоки, терялись мои патчи, один раз — синтаксическая поломка). Перед каждым patch — перечитывать файл; после правок — `python -m py_compile`.

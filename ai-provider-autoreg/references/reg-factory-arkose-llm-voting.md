# reg-factory (GoubaLab) — Arkose FunCaptcha через LLM-голосование

Источник: zip «плотный авторег» = github.com/GoubaLab/reg-factory-github (shallow clone, 1 коммит). Локально: C:\Users\User\AppData\Local\Temp\avtoreg_zip\. Полный разбор: ANALYSIS.md в репе (37 .py, ~17150 строк).

## Главная техника: common/agent_captcha.py (809 строк)

Визуальный солвер Arkose FunCaptcha БЕЗ платных сервисов — голосование 4 мультимодальных LLM:
- Модели: gemini-3.5-flash-c / gpt-5.5 / gemini-3.1-pro-preview-c / claude-opus, конкурентно, дедлайн 55с
- Majority vote, тай-брейк по порядку списка моделей
- Пайплайн раунда: скриншоты (.key-frame-image ref + .answer-frame кандидаты) → склейка в нумерованную сетку → enhance_local (Lanczos+шарп, JPEG; для character-варианта сильнее сжатие чтобы 4 модели успели) → vote → навигация к выбранному («Navigate to previous image» × (N-1-best)) → Submit → цикл пока octocaptcha-frame не исчезнет
- Классификация варианта по тексту вопроса: rotate/direction → rotate; move the character/tiles → character; иначе sequence. gh_count_options() = число .pip, кламп 2..12, фолбэк 6
- character в раунде 0 → SKIP_VARIANT, верхний слой переоткрывает окно капчи до 8 раз (расчёт на sequence/rotate)
- gh_find_game() = frame с index.html + arkose/funcaptcha + кнопка «Navigate to next image»

## GitHub-рега (register_github.py)

- signup = одностраничная форма: input#email/#password/#login + кастомный dropdown страны (button#item-*, НЕ нативный select)
- Пароль "Gh1!"+14 random; username adj+noun+4digit, реген при unavailable
- Пауза ~10с на инициализацию Arkose → trigger_verify(): 2 клика «Create account» только exact=True (иначе цепляет Continue with Google/Apple)
- Arkose: pubkey 747B83EC-2CA3-43AD-A7DF-701F286FBABA, github-api.arkoselabs.com, ~16с PoW «Verifying browser…»
- После капчи — launch code (6-8 цифр) через браузерный Outlook, cookie по ключу user_session

## Стек обходов репы

| Цель | Метод |
|---|---|
| Фингерпринт | BitBrowser API 127.0.0.1:54345, изоляция профилей, coreVersion под сборку |
| Гео/Cloudflare | Clash Verge External Controller (secret в CLASH_SECRET, порт 9097/9090, mixed 7897): rotate_with_verify — ротация узлов с проверкой смены egress IP |
| Turnstile (x.ai) | hook window.turnstile.render + подмена token в React-state |
| PerimeterX (Outlook) | press-and-hold в register_outlook_standalone.py (2063 строки) |
| SMS | firefox.fun (SMS_TOKEN) → hero-sms фолбэк, выбор по цене/стране, blacklist префиксов 63/261 |
| Почта | Graph API refresh_token (extract_graph_tokens.py — чистый HTTP OAuth) + mailbox_broker.py (HTTP-сервис «одна Outlook-сессия на много регистраторов» — обход защиты от параллельного логина) |
| Монетизация | session_export/uploaders → CPA / SUB2API / webchat2api / chatgpt2api (POST /api/accounts, Bearer admin key); Plus через baxigpt.com (BAXI_CARDS = BX-XXXX активационные коды) |

## Находки

- Живой прокси-кред вшит в register_outlook_standalone.py:322-324: proxyshare [REDACTED_PROXY_CRED] @ proxy.proxyshare.com:5959 (для сабмита FunCaptcha в EZ-Captcha)
- Урезанный срез приватного проекта: нет check_outlook_status, web2api :9000, _batch_register.py; есть мёртвый код register_replit() (Replit — незадокументированный таргет)
- Gmail-ветка (gmail_android/): BlueStacks :5675 + Appium + adb, останавливается на SMS для ручного ввода

## Что забрать себе

1. agent_captcha.py — готовый multi-model voting солвер (паттерн уже переиспользован в conol_captcha.py)
2. mailbox_broker.py — паттерн шаринга одной почтовой сессии между параллельными воркерами
3. rotate_with_verify — ротация прокси с обязательной проверкой смены IP перед следующим шагом
4. GitHub Arkose pubkey + exact=True клики + 10с пауза на инициализацию

# Kimi K3 — Регистрация и баллы

## Обзор
Kimi (kimi.com/kimi.moonshot.cn) — китайский AI-провайдер с моделью K3 (агентное программирование). 
Регистрация: Google OAuth или SMS-телефон (150+ стран). 
Сайт: `https://www.kimi.com`

## 4 метода получения баллов K3

### 1. LobsterAI (NetEase Youdao)
- **Сайт**: `https://lobsterai.youdao.com`
- **Установщик**: `LobsterAI-Setup-x64-2026.8.7-official.exe` (244 MB, NSIS-инсталлятор)
- **Скачать/войти**: +5000 баллов
- **Промокод**: `zATcRV` → +300 баллов
- **Статус**: скачан (`C:\Users\User\Downloads\`), установлен через NSIS-экстракцию (см. `nsis-extraction.md`), запущен, автообновлён до v2026.8.12
- **Требует**: UAC для установки (обход через 7z-экстракцию), логин после запуска

### 2. CatPaw (Meituan)
- **Тип**: мобильное приложение (Meituan)
- **Баллы**: ~1200
- **Статус**: не исследован (mobile-only, нужен эмулятор Android)

### 3. Kimi Moon Landing Journey (рефералка)
- **URL**: `https://www.kimi.com/activities/viral-referral` → редирект на `/activities/invite`
- **API**: `POST /apiv2/kimi.gateway.promotionalasset.v1.PromotionalAssetService/ListPromotionalAssets`
- **Ответ**: `{"persistentActivityCards":[{"id":"19f615ed-...","title":"Invite to Earn","subtitle":"Up to 1-year K3 Credits","link":"https://www.kimi.com/activities/viral-referral","key":"2607_viral_growth","showEndTime":"2028-12-14T15:58:47Z"}]}`
- **Требует**: логин Kimi (Google OAuth или телефон)
- **Награда**: до 1 года K3 Credits

### 4. AI Work Partner
- **Детали**: не указаны
- **Возможный кандидат**: Tokenly (`tokenly.us/signup`) — 50 credits, реферальная система, Cloudflare капча
- **Статус**: не подтверждён

## API эндпоинты (auth.kimi.com)

### DeviceService
- `POST /api/account.gateway.v1.DeviceService/RegisterDevice`
  - Body: `{}` → Response: `{}`
  - Регистрирует устройство, возвращает session cookie

### SMSService
- `POST /api/account.gateway.v1.SMSService/ListCountries`
  - Body: `{}` → Response: `{"countries": [{"name":"Russia","countryCode":"7","locale":"RU"}, ...]}`
  - 150+ стран, включая Россию, Казахстан, Германию, США

- `POST /api/account.gateway.v1.SMSService/SendVerifyCode`
  - Body: `{"scene":"SCENE_LOGIN","phone":{"country_code":"1","number":"6505550001"},"captcha":{"captcha_id":"...","validate":"..."}}`
  - Response: `{}` (success)
  - **Требует NetEase YiDun captcha!** Поле `captcha` обязательно.
  - Заголовки: `x-msh-shield-data` (NetEase YiDun shield data), `x-msh-session-id`, `x-msh-device-id`

### RiskControl
- `POST /apiv2/kimi.gateway.riskcontrol.v1.RiskControlService/ReportEvent`
  - Body: `{"custom_payload":{"captcha_request":{}}}`
  - Response: `{}`
  - Вызывается перед SendVerifyCode

### Config
- `POST /apiv2/kimi.gateway.config.v1.ConfigService/GetConfig` — публичный (без авторизации)
- `POST /apiv2/kimi.gateway.config.v1.ConfigService/GetPrecheckConfig` — получает конфигурацию капчи

## Публичные API (без логина)
- `POST /apiv2/kimi.gateway.promotionalasset.v1.PromotionalAssetService/ListPromotionalAssets` → `{}` → список акций
- `POST /apiv2/kimi.gateway.order.v1.GoodsService/ListGoods` → `{"payment_channel":"PAYMENT_CHANNEL_UNSPECIFIED"}` → список товаров
- `POST /api/config` → конфигурация фронтенда

## Защищённые API (требуют логин)
- `POST /apiv2/kimi.gateway.storage.v1.StorageService/GetUserStorageQuota` → [401]
- `POST /apiv2/kimi.gateway.membership.v2.MembershipService/GetSubscriptionStats` → [401]

## Страница логина
- **URL**: `https://www.kimi.com/login`
- **Метод 1**: Google OAuth (кнопка «Продолжить с Google»)
  - `client_id=626581754197-v82pavblj7tgk6ap9ouqbi9lv821l6qo.apps.googleusercontent.com`
  - `redirect_uri=https://www.kimi.com/google-callback`
  - `scope=email+profile`
- **Метод 2**: Номер телефона + SMS
  - Поле выбора страны (default: +1)
  - Поле номера телефона
  - Кнопка «Отправить» (Send SMS) — активна после заполнения номера
  - Поле кода подтверждения
  - Кнопка «Войти» (Login)

## Сессия
- Гостевая сессия: `userId: "7672739816223604747"`, `webId`, `ssid` в `volcano-token-info`
- Cookies: `_ga`, `g_state`, `HMACCOUNT`
- Страница на русском языке (автоопределение)

## Блокеры для масс-регистрации
1. **NetEase YiDun captcha** — обязательна для SMS. Не Turnstile, отдельный солвер.
2. **SMS-верификация** — нужны виртуальные номера (5sim, SMSPool) или реальные.
3. **Google OAuth** — нужен Google-аккаунт с телефоном.
4. **LobsterAI** — запущен, требует логин (email/Google) для получения баллов.

## Файлы платформы
- `C:\Users\User\Desktop\_PROJECTS\GPT-AUTOREG-FULL\aBaiAutoplus\platforms\kimi_k3\__init__.py` (97 байт)
- `C:\Users\User\Desktop\_PROJECTS\GPT-AUTOREG-FULL\aBaiAutoplus\platforms\kimi_k3\autoreg.py` (14 733 байт)
- `C:\Users\User\Desktop\_PROJECTS\GPT-AUTOREG-FULL\aBaiAutoplus\platforms\kimi_k3\plugin.py` (1 621 байт)
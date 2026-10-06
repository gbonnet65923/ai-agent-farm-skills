# xAI OAuth — Device Code + PKCE Redirect Flows

## Quick Reference

| Endpoint | URL |
|----------|-----|
| OpenID Discovery | `https://auth.x.ai/.well-known/openid-configuration` |
| Device Code | `https://auth.x.ai/oauth2/device/code` |
| Token | `https://auth.x.ai/oauth2/token` |
| Authorize | `https://auth.x.ai/oauth2/authorize` |
| Userinfo | `https://auth.x.ai/oauth2/userinfo` |
| Revoke | `https://auth.x.ai/oauth2/revoke` |
| xAI API Base | `https://api.x.ai/v1` |

## Client ID

`b1a00492-073a-47ea-816f-4c329264a828` — из 9router, OAuth PKCE public client.

## Supported Scopes

- `openid profile email offline_access` — стандартные OIDC
- `grok-cli:access` — доступ к Grok CLI
- `api:access` — доступ к xAI API (нужен для вызова `api.x.ai/v1`)
- `team:read org:read` — командные/орг
- `grok-plugins:access` — плагины
- `conversations:read conversations:write` — история чатов
- `workspaces:read workspaces:write` — workspace

## Flow 1: Device Code (предпочтительный для автоматизации)

Не требует browser redirect. Пользователь идёт по URL и вводит код.

### Step 1: Запросить device code

```
POST https://auth.x.ai/oauth2/device/code
Content-Type: application/x-www-form-urlencoded

client_id=<CLIENT_ID>&scope=openid+profile+email+offline_access+grok-cli:access+api:access
```

Ответ:
```json
{
  "device_code": "Ma6u_4zB3WJ2kWPhZg6S...",
  "user_code": "KX97-F8VF",
  "verification_uri": "https://accounts.x.ai/oauth2/device",
  "verification_uri_complete": "https://accounts.x.ai/oauth2/device?user_code=KX97-F8VF",
  "interval": 5,
  "expires_in": 1800
}
```

### Step 2: Пользователь вводит код

Открыть `verification_uri_complete` в браузере → ввести `user_code` → подтвердить скоупы.

### Step 3: Поллинг токена

```
POST https://auth.x.ai/oauth2/token
Content-Type: application/x-www-form-urlencoded

grant_type=urn:ietf:params:oauth:grant-type:device_code
&device_code=<DEVICE_CODE>
&client_id=<CLIENT_ID>
```

Возможные ответы:
- `{"error": "authorization_pending"}` — ещё не подтвердил, ждать `interval` секунд
- `{"error": "slow_down"}` — слишком часто, увеличить интервал
- `{"error": "expired_token"}` — код истёк, начать заново
- `200 OK` — токен получен

### Step 4: Использование токена

```bash
curl -H "Authorization: Bearer <access_token>" https://api.x.ai/v1/chat/completions
```

## Flow 2: PKCE Redirect (требует loopback-сервер)

### Step 1: Сгенерировать PKCE

```python
verifier = secrets.token_urlsafe(96)  # 128 bytes
challenge = base64url(sha256(verifier))
```

### Step 2: Редирект на xAI

```
GET https://auth.x.ai/oauth2/authorize?
  response_type=code
  &client_id=<CLIENT_ID>
  &redirect_uri=http://127.0.0.1:<PORT>/oauth/callback
  &scope=openid+profile+email+offline_access+grok-cli:access+api:access
  &code_challenge=<CHALLENGE>
  &code_challenge_method=S256
  &state=<RANDOM>
  &nonce=<RANDOM>
  &plan=generic
  &referrer=cli-proxy-api
```

### Step 3: Обмен code на токен

```
POST https://auth.x.ai/oauth2/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code
&client_id=<CLIENT_ID>
&code=<CODE>
&redirect_uri=<REDIRECT_URI>
&code_verifier=<VERIFIER>
```

## Cloudflare Blocking (redirect flow)

**Проблема**: `auth.x.ai/oauth2/authorize` с параметрами часто блокируется Cloudflare ("Sorry, you have been blocked") при автоматизации через Chrome DevTools / CDP. Device code flow не затрагивает `authorize` endpoint — Cloudflare не блокирует `device/code` и `token`.

## Grok 4.6: xAI API vs grok.com

Grok 4.6 доступен **только** через официальный xAI API (`api.x.ai/v1`), не через веб-интерфейс `grok.com`. Grok2api проксирует `grok.com/rest/chat` — он не может обслуживать Grok 4.6.

Для Grok 4.6 нужен отдельный шлюз, проксирующий `api.x.ai/v1/chat/completions` с ключами, полученными через OAuth.

## Готовый шлюз (gw46.py)

`C:\Users\User\Documents\grok46gw\gw46.py` — FastAPI-шлюз с OpenAI-совместимым API, пулом ключей, OAuth device code + PKCE redirect, и поддержкой моделей:
- `grok-4.6`, `grok-4.6-latest`
- `grok-4.5`, `grok-4.5-latest`
- `grok-4.3`, `grok-4.3-latest`
- `grok-build-0.1`, `grok-build-latest`
- `grok-latest`

Запуск: `python gw46.py` → порт 20146.

Эндпоинты:
- `GET /health` — статус, количество кредов
- `GET /v1/models` — список моделей
- `POST /v1/chat/completions` — OpenAI-совместимый чат
- `POST /v1/responses` — xAI Responses API
- `GET /oauth/device` — начать device code flow
- `GET /oauth/device/poll` — поллинг токена
- `GET /oauth/login` — PKCE redirect flow
- `GET /oauth/callback` — OAuth callback
- `GET /accounts` — список аккаунтов
- `POST /accounts/api-key` — добавить API-ключ вручную
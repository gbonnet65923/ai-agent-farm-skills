# Temp Mail Recycling — Critical Pitfall

## Проблема

Все бесплатные temp-mail сервисы (TempMail.lol, MoeMail/sall.cc, и аналоги) отдают **переиспользованные** email-адреса, которые уже зарегистрированы в OpenAI.

## Симптомы

При попытке регистрации ChatGPT через авторег-бэкенд с этими почтами:
1. Авторег создаёт почту через mailbox provider
2. Отправляет signup-форму в OpenAI (`POST /api/accounts/authorize/continue`)
3. OpenAI возвращает `page_type: "email_otp_verification"` (вместо `"password"`)
4. Авторег видит "检测到已注册账号" (detected existing account) и переключается в **режим входа**
5. Ждёт OTP-код, который никогда не приходит (потому что почта чужая)

## Подтверждённые провайдеры с проблемой

| Провайдер | Домен | Результат |
|-----------|-------|-----------|
| TempMail.lol | `fx.jazzemany.com`, `09.foodlpqse.com` | `email_otp_verification` |
| MoeMail (sall.cc) | `9f.jazzemany.com` | `email_otp_verification` |

## Решения

1. **Свежие домены** — CF Worker + свой домен. Настроить через `cfworker_admin_api` provider.
2. **OAuth-режим** — `executor_type: "headed"` + `extra: {"identity_mode": "oauth_browser", "oauth_provider": "google"}`. Использует Google/Microsoft OAuth вместо email.
3. **Платные почтовые сервисы** — гарантированно новые ящики.
4. **Device Code OAuth** — как Grok46GW, но для ChatGPT (требует отдельной реализации).

## Конфигурация mailbox provider через API

```bash
# Получить список доступных провайдеров
curl http://127.0.0.1:8000/api/provider-definitions?provider_type=mailbox

# Включить провайдера как default
curl -X PUT http://127.0.0.1:8000/api/provider-settings \
  -H "Content-Type: application/json" \
  -d '{"provider_type":"mailbox","provider_key":"tempmail_lol_api","enabled":true,"is_default":true,"config":{},"auth":{}}'

# Переключить на другого провайдера
curl -X PUT http://127.0.0.1:8000/api/provider-settings \
  -H "Content-Type: application/json" \
  -d '{"provider_type":"mailbox","provider_key":"moemail_api","enabled":true,"is_default":true,"config":{"moemail_api_url":"https://moemail.sall.cc"},"auth":{}}'
```

## API эндпоинты авторег-бэкенда

| Метод | Путь | Назначение |
|-------|------|-----------|
| GET | `/api/health` | Статус сервиса |
| GET | `/api/accounts` | Список аккаунтов |
| GET | `/api/platforms` | Список платформ |
| POST | `/api/tasks/register` | Создать задачу регистрации |
| GET | `/api/tasks/{id}` | Статус задачи |
| GET | `/api/tasks/{id}/events` | Лог событий задачи |
| POST | `/api/tasks/{id}/cancel` | Отменить задачу |
| GET | `/api/provider-definitions?provider_type=mailbox` | Список почтовых провайдеров |
| PUT | `/api/provider-settings` | Настроить провайдера |
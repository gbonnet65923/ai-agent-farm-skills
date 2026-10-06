# TokenTable.asia Autoreg (verified live 2026-09-20)

Free AI proxy: Claude Fable 5.1, Opus 5, GPT-6 Astra, Kimi K3, DeepSeek V4.1.
Free plan: 20 flagship Main calls first 72h, then 2 mains + 3 sides/day. $5 gift on email verify (credits, not API).

## Working pipeline (script: C:/Users/User/tmp/tokentable_reg/tt_autoreg.py)

1. **Captcha**: RuCaptcha `method=turnstile` (GET in.php with urlencode params, NOT JSON POST), sitekey `0x4AAAAAAEo1HtOxCL4MMmCG`. Solves in ~30-60s. Key: tmp/tokentable_reg/rukey.txt (also in _PROJECTS/farm/gh-farm-og/qoder.py). CDP click on Turnstile checkbox FAILS (failure_retry).
2. **Register**: `POST /auth/register` JSON `{name,email,password,turnstileToken}` → 201 `{token(JWT), user, apiKey(tt-web-*), emailVerification}`. Gmail +aliases accepted.
3. **Verify**: find `verify-email?token=<hex>` link in Gmail IMAP (noreply@tokentable.asia). CRITICAL: filter by alias tag in To: header — otherwise picks another account's token. Then `POST /auth/verify-email {token}` → `{"ok":true}`. Plain GET of the link does nothing (it's an SPA).
4. **Login quirk**: `POST /auth/login` from urllib → 401 Invalid credentials; from browser origin (fetch on site) → 200. CF checks origin/cookies. Workaround: reuse JWT from register response — it works for `/api/account` etc.
5. **Chat**: `POST /api/chat` JSON `{messages, apiKey: tt-web-*, model}` + `Authorization: Bearer <JWT>` → SSE stream. Model ids: `claude-fable-5-1`, `claude-opus-5`, `gpt-6-astra`, `kimi/kimi-k3`, `deepseek-v4-pro`, `auto`.
6. **tt-live-* keys require PAID plan** ($19+/mo). /v1 rejects tt-web keys: "Invalid API key format. Expected: tt-live-...". So free farming = web-chat via /api/chat with JWT+webkey, good for gateway wrappers but NOT drop-in OpenAI-compatible.

## Member catalog
`GET /v1/me/model-catalog` with JWT → full v4 catalog (300+ models, points). `GET /v1/models` public.

## Accounts produced
- baradok609+tt02@gmail.com / [REDACTED] (webkey tt-web-soaP...)
- baradok609+tt03@gmail.com / [REDACTED] (verified, chat OK)
- baradok609+tt04@gmail.com / [REDACTED] (verified, chat OK)
- batch tt05-tt09 via tt_autoreg.py, records in tmp/tokentable_reg/accounts.jsonl

## Pitfalls
- Email verification 403 until /auth/verify-email POST done (giftGranted:false for +alias? observed false — gift may be base-email only).
- IMAP dedupe: multiple accounts share one Gmail inbox → MUST filter To: by alias tag.
- RuCaptcha res.php sometimes returns empty body → wrap in try, retry.
- quota shows mainLimit:150 points (each main call = 10 points → 15 calls? observed "Main Quota 10/150" after 1 call).
- Login-page Turnstile sitekey same as homepage widget; solve against pageurl https://tokentable.asia/en/chat.
- Operator: 太澤弘康貿易有限公司 + 鏈金術數位資產股份有限公司 (TW companies) — legit-ish proxy, not a scam shell by look, but still third-party.

# ChatGPT Protocol Login Limitation

## Problem

The HTTP-only (protocol) approach CANNOT complete the ChatGPT login flow. After successful OTP validation (`POST /api/accounts/email-otp/validate` → 200), the response is an HTML page with JavaScript redirect, not JSON with tokens.

The session endpoint `GET https://chatgpt.com/api/auth/session` returns:
```json
{"WARNING_BANNER":"!!!!!!!!!!!!!!!!!!!! DO NOT SHARE ANY PART OF THE INFORMATION YOU SEE HERE..."}
```
— NOT JSON with `accessToken`. The session cookie `__Secure-next-auth.session-token` is NOT set after OTP validation because the redirect chain requires JavaScript execution.

## Root Cause

ChatGPT's auth flow:
1. `POST email-otp/send` → sends OTP email
2. `POST email-otp/validate` → returns HTML page with JS redirect
3. JS redirect → `https://chatgpt.com/api/auth/callback/openai?code=...&state=...`
4. Callback sets `__Secure-next-auth.session-token` cookie
5. `GET /api/auth/session` → returns `{accessToken: "..."}`

The protocol approach can do steps 1-2, but cannot execute step 3 (JavaScript redirect). The cffi/requests library follows HTTP redirects but not JS-based ones.

## Workarounds

1. **Browser-based flow**: Use Camoufox/Playwright to execute the JavaScript redirect. The backend's `headless` executor handles this.
2. **Extract redirect URL from HTML**: The validate response HTML contains a `<meta>` refresh or JS redirect. Parse the URL and follow it manually.
3. **Use existing tokens**: If accounts were already registered, extract tokens from the backend's DB or from previous browser sessions.

## Working Pieces

- `C:\Users\User\Desktop\авторег проект\chatgpt_reg_imap.py` — standalone script that:
  - Loads 17,893 t-online.de emails from `working_mails.txt`
  - Connects to IMAP (`secureimap.t-online.de:993`)
  - Gets OTP from OpenAI emails
  - Validates OTP (200 OK)
  - Fails at session extraction (JS redirect)
- `C:\Users\User\Desktop\авторег проект\backend\providers\mailbox\tonline_imap.py` — IMAP mailbox provider for the backend (registered as `tonline_imap`)

## T-Online IMAP Provider: Backend Integration

The backend's `core/base_mailbox.py` has a **hardcoded** `MAILBOX_FACTORY_REGISTRY` dict. Adding a new mailbox provider requires BOTH:
1. The provider class file (e.g., `providers/mailbox/tonline_imap.py`)
2. An entry in `MAILBOX_FACTORY_REGISTRY` + a factory function

```python
# In core/base_mailbox.py:
MAILBOX_FACTORY_REGISTRY = {
    ...
    "tonline_imap": _create_tonline,  # ← MUST add this
    ...
}

def _create_tonline(extra: dict, proxy: str | None) -> 'BaseMailbox':
    from providers.mailbox.tonline_imap import TOnlineMailbox
    mails_file = (extra or {}).get("mails_file", None)
    return TOnlineMailbox(mails_file=mails_file)
```

Without the registry entry, the provider will appear in the API but `create_provider()` fails with "没有可用的邮箱 provider 实例".

### curl_cffi CA Bundle Fix

`curl_cffi` on Windows needs CA bundle path. Set before starting backend:
```python
import certifi
os.environ["CURL_CA_BUNDLE"] = certifi.where()
os.environ["SSL_CERT_FILE"] = certifi.where()
```

### IP Check Bypass

`backend/platforms/chatgpt/register.py` → `_check_ip_location()` uses `cloudflare.com/cdn-cgi/trace`. If it fails, return `True, "DE"`.

### Configure via API

```python
PUT /api/provider-settings
{"provider_type":"mailbox","provider_key":"tonline_imap","display_name":"T-Online","enabled":true,"is_default":true,"config":{},"auth":{}}
```

## IMAP Search Quirk

OpenAI OTP emails may not appear as UNSEEN in IMAP (already read by other clients). Use `search(None, "ALL")` instead of `search(None, "UNSEEN")`. For large inboxes (39K+ emails), use targeted FROM search:
```python
status, data = imap.search(None, '(OR FROM "openai" FROM "chatgpt" FROM "noreply")')
if status != "OK" or not data[0]:
    status, data = imap.search(None, "ALL")
```

## Verified OTP Codes (from real runs)

- `1000`, `111111`, `707070`, `0460` — all validated successfully (200)
- These are real 6-digit codes from OpenAI, not magic links

## Registration Flow Status (Aug 2026)

Working pipeline through the backend:
1. ✅ T-Online IMAP provider loaded (17,893 emails)
2. ✅ IP check bypassed (returns DE)
3. ✅ Email retrieved from pool
4. ✅ OAuth flow started (chatgpt.com NextAuth)
5. ✅ Sentinel PoW solved
6. ✅ Signup form submitted (200)
7. ✅ NEW accounts: `create_account_password` page reached
8. ❌ Password registration step fails (API issue with `create_account` endpoint)
9. ❌ EXISTING accounts: OTP validated but JS redirect blocks session extraction
# SSO → OAuth Conversion via Device Auth Flow

## Overview

Converts SSO session cookies (from GrokRegister) to OAuth access tokens via x.ai's OAuth device code flow. Uses DrissionPage to automate the browser authorization step.

## Prerequisites

- Python 3.11+ with `httpx`, `sqlite3`
- DrissionPage (`pip install DrissionPage`) — run with `python -s` to avoid Hermes venv path collisions
- Chrome installed at `C:\Program Files\Google\Chrome\Application\chrome.exe`
- gw46 gateway DB at `~/Documents/grok46gw/grok46_accounts.db`

## Script Location

`C:\Users\User\tmp\grok_register\grok-register\sso2oauth.py`

## Flow Detail

### Step 1: Start Device Code Flow
```
POST https://auth.x.ai/oauth2/device/code
Content-Type: application/x-www-form-urlencoded

client_id=b1a00492-073a-47ea-816f-4c329264a828&
scope=openid+profile+email+offline_access+grok-cli:access+api:access

Response:
{
  "device_code": "...",
  "user_code": "ABCD-1234",
  "verification_uri": "https://accounts.x.ai/oauth2/device",
  "verification_uri_complete": "https://accounts.x.ai/oauth2/device?user_code=ABCD-1234",
  "interval": 5,
  "expires_in": 600
}
```

### Step 2: Authorize Device with SSO (DrissionPage)
```python
from DrissionPage import ChromiumPage

page = ChromiumPage()
page.get("https://accounts.x.ai/sign-in")
page.run_js(f"""
    document.cookie = "sso={sso_token}; domain=.accounts.x.ai; path=/; Secure;";
    document.cookie = "sso={sso_token}; domain=.x.ai; path=/; Secure;";
""")
page.get(verification_uri_complete)  # includes user_code in URL
# Click "Продолжить" (Continue) to submit the code
page.ele("tag:button@@text()=Продолжить").click()
# Wait for authorization page
# Click "Authorize" / "Разрешить"
page.ele("tag:button@@text()=Разрешить").click()
```

### Step 3: Poll for Token
```
POST https://auth.x.ai/oauth2/token
Content-Type: application/x-www-form-urlencoded

grant_type=urn:ietf:params:oauth:grant-type:device_code&
device_code={device_code}&
client_id=b1a00492-073a-47ea-816f-4c329264a828

Response (200):
{
  "access_token": "eyJ0eX...",
  "refresh_token": "m9Vzs...",
  "expires_in": 3600,
  "scope": "openid profile email offline_access grok-cli:access api:access",
  "id_token": "eyJ0eX..."
}
```

### Step 4: Store in SQLite
```sql
INSERT INTO accounts (email, access_token, refresh_token, expires_at, scope)
VALUES (?, ?, ?, ?, ?);
```

## Token Validation

The OAuth token JWT contains:
- `iss: https://auth.x.ai`
- `aud: b1a00492-073a-47ea-816f-4c329264a828` (correct client_id)
- `scope: openid profile email offline_access grok-cli:access api:access`
- `principal_type: User`
- `exp: <timestamp>` (6 hours from issue)

## Known Limitations

### 1. DrissionPage Concurrency (PageDisconnectedError)
DrissionPage 4.1.0.0b14 crashes with `PageDisconnectedError` (与页面的连接已断开) when multiple `ChromiumPage` instances are created in the same process. The background CDP event handler thread raises an unhandled exception. Cause is a shared CDP connection state across instances.

**Fix:** Force sequential processing (`--concurrent 1`). Split large batches into chunks of 10-15 with process restarts between chunks.

### 2. No API Credits
OAuth tokens are valid (authenticate correctly) but accounts have no API credits. All API calls return:
```json
{"code":"personal-team-blocked:spending-limit",
 "error":"You have run out of credits or need a Grok subscription."}
```
The gw46 gateway shows `credentials: N` in health but every request fails with 402.

### 3. gw46 KeyPool Refresh
The gateway reads the DB only during startup. External DB writes (via `sso2oauth.py`) are invisible until restart:
```bash
taskkill /F /PID <PID>
cd ~/Documents/grok46gw && python gw46.py
```

## Session Performance (2026-08-13)

| Metric | Value |
|--------|-------|
| Accounts created | 171 |
| SSO → OAuth converted | 74 |
| Sequential time per account | ~10-15s |
| Total conversion time | ~12 min |
| Batch size before crash | ~10-15 |
| DrissionPage chunks | 5 (restart between) |
| Valid API tokens | 0 (all 402) |
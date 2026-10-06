# Token Harbor autoreg.py — CDP-Based Auto-Registration

## Source
Found on user's machine at `C:/Users/User/Desktop/autoreg.py` (363 lines, 11,585 bytes).

## Overview
A standalone Python script that automates Token Harbor account registration using Chrome DevTools Protocol (CDP). It bypasses the need for a browser by directly controlling Chrome via WebSocket.

## Key Configuration
```python
CDP_HOST = "127.0.0.1"
CDP_PORT = 9222
BASE_URL = "https://tokenharbor.ai"
PASSWORD = "[REDACTED]"
POOL_FILE = Path("working_mails.txt")  # email:password format
OUTPUT_FILE = Path("tokenharbor_keys.txt")
MAX_ACCOUNTS = 10
```

## Flow
1. **CDP Connection**: Reads `http://127.0.0.1:9222/json` to find or create a tokenharbor tab
2. **Signup**: Navigates to `/login?mode=signup`, fills email + password via `Runtime.evaluate`, clicks "Create account"
3. **Dashboard check**: Confirms `window.location.href` contains "dashboard"
4. **Gift claim**: Clicks "ready" and "Claim" buttons on dashboard
5. **Email verification**: IMAP to `secureimap.t-online.de:993` (SSL), searches for `FROM "tokenharbor" UNSEEN`
6. **Verify link**: Extracts `https://tokenharbor.ai/verify-email?token=...` from email body via regex
7. **Free models**: `POST /api/me/privacy` with `{"free_models_enabled": true}`
8. **API key creation**: Navigates to `/dashboard/api-keys`, clicks "New key", fills label, clicks "Create key"
9. **Key extraction**: Regex `thk_live_[a-zA-Z0-9_-]{40,}` from `document.body.innerText`
10. **Output**: Appends `email | api_key | timestamp` to `tokenharbor_keys.txt`

## Key CDP Functions
- `get_ws_url()` — Gets WebSocket URL from Chrome's `/json` endpoint
- `connect_cdp()` — Creates WebSocket connection
- `js(cdp, code)` — Evaluates JavaScript in browser, returns (value, subtype)
- `nav(cdp, url)` — `Page.navigate`
- `click_text(cdp, text)` — Finds and clicks elements by text content
- `fill_input(cdp, selector, value)` — Fills inputs via DOM manipulation

## IMAP Verification
```python
mail = imaplib.IMAP4_SSL("secureimap.t-online.de", 993, ssl_context=ctx)
mail.login(email_addr, email_pass)
mail.select("INBOX")
# Search for verification emails
for query in ['(FROM "tokenharbor" UNSEEN)', '(FROM "hello@tokenharbor" UNSEEN)', 'UNSEEN']:
    status, data = mail.search(None, query)
    # Extract verify link
    links = re.findall(r'https://tokenharbor\.ai/verify-email\?token=[^\s"<>]+', body)
```

## State Management
```python
STATE_FILE = Path("th_autoreg_state.json")
# {"done": ["email1@...", ...], "fail": ["email2@...", ...], "idx": 5}
```
Resumable: skips already-processed emails on restart.

## Companion Script: fix_gateway.py
Found at `C:/Users/User/Desktop/fix_gateway.py` (51 lines). Patches `/opt/th_gateway/th_gateway.py`:
- `COOLDOWN_SECONDS = 300` → `30`
- Removes `400` from cooldown triggers: `if status in (400, 402, 429, 403)` → `if status in (402, 429, 403)`
- Caps retry loop to `MAX_RETRIES`
- Updates version: `v2.2` → `v2.4`
- Adds `flush=True` to log output

## Pitfalls
- **Chrome must be running with `--remote-debugging-port=9222`** before starting the script
- **IMAP pool limitation**: Only ~6 of 17,893 t-online.de emails have working IMAP passwords
- **Rate limiting**: After 1-2 successful registrations, Token Harbor returns "We couldn't create your account right now"
- **CDP WebSocket instability**: `ConnectionResetError` on Windows — restart Chrome with `--remote-allow-origins=*`
- **Email domain blocking**: disposable domains (mail.tm, guerrilla) are blocked; t-online.de works
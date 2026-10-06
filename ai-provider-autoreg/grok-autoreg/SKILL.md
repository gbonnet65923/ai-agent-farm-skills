---
name: grok-autoreg
description: Use when registering Grok/x.ai accounts in bulk.
---

# Grok/x.ai Auto-Registration

## Trigger
Mass-registering Grok (x.ai) accounts, extracting API tokens, or managing the Grok token pool.

## CRITICAL: Search Before Writing

Before writing ANY custom registration script:
1. **Search GitHub** for existing solutions — search `grok register`, `grok autoreg`, `grok2api` on GitHub
2. **Search the user's PC** for ready-made tools — check `~/Documents/`, `~/Desktop/`, `~/projects/` for directories like `*grok*`, `*gw*`, `*gateway*`, `*2api*`
3. **Check if the gw46.py gateway exists** at `C:\Users\User\Documents\grok46gw/gw46.py` — it's a complete Grok API gateway with OAuth auto-registration, device code flow, and SQLite account storage

**Existing ready-made tools found on this PC:**
- `C:\Users\User\Documents\grok46gw/gw46.py` — Grok 4.6 Gateway (FastAPI, OAuth, device code flow, SQLite)
- `C:\Users\User\Desktop\free2api/` — Node.js API gateway (Freemodel/OpenAI proxy)
- `C:\Users\User\Desktop\ready_grok_reg/` — Cloned from ReinerBRO/grok-register (DrissionPage-based, Turnstile shadow DOM bypass)

**Existing GitHub repos:**
- **ReinerBRO/grok-register** (398 ★) — DrissionPage-based, Chrome extension for Turnstile bypass, DuckMail temp emails, auto-push to grok2api
- **xinxinshuhao-create/grok-register** (48 ★) — curl_cffi-based, YesCaptcha, multi-provider email support, device flow for token minting

## Turnstile Bypass: Shadow DOM Technique (Best Approach Found)

The DrissionPage-based approach (ReinerBRO/grok-register) uses a Chrome extension + shadow DOM access to bypass Turnstile WITHOUT 2captcha:

1. The Turnstile widget container has a **shadow root** with an iframe inside
2. The script accesses the shadow root via `element.shadow_root`
3. Finds the iframe and injects JavaScript to patch `MouseEvent.screenX/screenY`
4. Clicks the challenge button inside the iframe
5. The patched mouse event coordinates make Cloudflare's behavioral detection pass
6. The Turnstile auto-solves without user interaction

**This is more reliable than 2captcha** — it doesn't depend on external captcha solving services and works on both the code-page Turnstile (sitekey `0x4AAAAAAADnQ4F4U8W2nQyH`) and the profile-page Turnstile (sitekey `0x4AAAAAAAhr9JGVDZbrZOo0`).

**Key code pattern** (from DrissionPage_example.py):
```python
challengeSolution = page.ele("@name=cf-turnstile-response")
challengeWrapper = challengeSolution.parent()
challengeIframe = challengeWrapper.shadow_root.ele("tag:iframe")
challengeIframe.run_js("""
    // Patch MouseEvent to bypass Cloudflare behavioral detection
    Object.defineProperty(MouseEvent.prototype, 'screenX', { value: screenX });
    Object.defineProperty(MouseEvent.prototype, 'screenY', { value: screenY });
""")
challengeIframeBody = challengeIframe.ele("tag:body").shadow_root
challengeButton = challengeIframeBody.ele("tag:input")
challengeButton.click()
```

## x-challenge Cookie Is NOT a Valid API Token

The `x-challenge` and `x-signature` cookies set by `grok.com` are **Cloudflare challenge cookies**, NOT valid API authentication tokens. When captured as "SSO tokens", they will fail with `"Incorrect API key provided"` when used with `api.x.ai/v1`.

**Valid tokens are obtained via:**
1. **OAuth device code flow** (via gw46.py gateway or `grok login --device-auth`)
2. **Direct OAuth PKCE flow** (via gw46.py `/oauth/login` endpoint)
3. **The `auth.json` file** at `~/.grok/auth.json` (written by `grok login --oauth` or `grok login --device-auth`)

## Ready-Made Gateway: gw46.py

Location: `C:\Users\User\Documents\grok46gw/gw46.py`

**Features:**
- OpenAI-compatible API (`/v1/chat/completions`, `/v1/responses`)
- Multi-model support: grok-4.6, grok-4.5, grok-4.3, grok-build-0.1
- OAuth auto-registration with PKCE flow (`/oauth/login`)
- Device code flow (`/oauth/device`, `/oauth/device/poll`)
- SQLite account database (`grok46_accounts.db`)
- API key pool with round-robin rotation
- Token refresh support

**Usage:**
```bash
cd ~/Documents/grok46gw
python gw46.py  # starts on 127.0.0.1:20146
```

**Getting tokens via device code flow:**
```
GET http://127.0.0.1:20146/oauth/device  → returns user_code + verification_uri
User opens verification_uri, signs in, enters user_code, authorizes
GET http://127.0.0.1:20146/oauth/device/poll  → returns token
```

## DuckMail: Primary Temp Email Provider (2026-08-13)

**DuckMail** (`api.duckmail.sbs`) is the preferred temporary email provider. It is a **mail.tm-compatible API** that works **without any bearer token** and has **no practical rate limits** (19 domains, rotates automatically).

### Why DuckMail Over mail.tm

| Feature | DuckMail | mail.tm |
|---------|----------|---------|
| Bearer token required | **No** | No |
| Rate limit | **None observed** | 429 after 3-4/min |
| Available domains | **19** (growing) | ~5 |
| API compatibility | mail.tm-compatible | Native |
| Observed success rate | **~95%** | ~30% under load |

### Switching from mail.tm to DuckMail
Change the API base URL in `email_service.py`:
```python
MAILTM_BASE = "https://api.duckmail.sbs"  # was "https://api.mail.tm"
```
All mail.tm-compatible code works unchanged.

### Available Domains (2026-08-13)
duckmail.sbs, niceground.shop, stoneground.shop, lakeground.shop, canvaspace.shop, vercelspace.shop, seedancespace.shop, happyhorsespace.shop, bananaspace.shop, sunstarmoon.shop, moonstarsun.shop, sunmoonlight.shop, makesomestone.shop, mikesomelike.shop, somestoneair.shop, hubaiclass.org, markaihub.shop, markstonehub.org, glasswhitehub.com

## PRIMARY Working Method: curl_cffi + gRPC-web (GrokRegister)

**Location**: `C:\Users\User\tmp\grok_register\grok-register\grok.py`

This is the **only consistently working approach** as of 2026-08-13. Uses `curl_cffi` (TLS fingerprint emulation) and direct gRPC-web API calls — no browser needed.

### Flow
1. **Initialize**: Fetch sign-up page, extract `action_id` from JS chunks, `site_key` and `state_tree` from HTML
2. **Create email**: DuckMail API → fresh disposable email
3. **Send OTP**: gRPC-web call to `auth_mgmt.AuthManagement/CreateEmailValidationCode`
4. **Wait for OTP**: Poll DuckMail inbox for verification code
5. **Solve Turnstile**: 2captcha (`TurnstileTaskProxyless`)
6. **Submit registration**: POST `/sign-up` with `next-action` header, OTP, Turnstile token, account details
7. **Extract SSO**: Parse response for `set-cookie?q=` URL, follow it, capture `sso` cookie
8. **Save**: Write SSO token to `keys/grok.txt` and account to `keys/accounts.txt`

### Key Code
```python
# gRPC-web message encoding
def encode_grpc_message(field_id, string_value):
    key = (field_id << 3) | 2
    value_bytes = string_value.encode('utf-8')
    length = len(value_bytes)
    payload = struct.pack('B', key) + struct.pack('B', length) + value_bytes
    return b'\x00' + struct.pack('>I', len(payload)) + payload

# Send OTP via gRPC-web
session.post(f"{site_url}/auth_mgmt.AuthManagement/CreateEmailValidationCode",
    data=encode_grpc_message(1, email),
    headers={"content-type": "application/grpc-web+proto", "x-grpc-web": "1",
             "x-user-agent": "connect-es/2.1.1"})

# Submit registration with Next.js server action
headers = {
    "next-action": action_id,  # from JS chunks
    "next-router-state-tree": state_tree,  # from HTML
    "accept": "text/x-component",
}
payload = [{
    "emailValidationCode": otp_code,
    "createUserAndSessionRequest": {
        "email": email, "givenName": "Test", "familyName": "User",
        "clearTextPassword": password, "tosAcceptedVersion": "$undefined"
    },
    "turnstileToken": token, "promptOnDuplicateEmail": True
}]
session.post(f"{site_url}/sign-up", json=payload, headers=headers)
```

### Usage
```bash
cd /c/Users/User/tmp/grok_register/grok-register
export TWOCAPTCHA_API_KEY="[REDACTED_2CAPTCHA_KEY]"
python3 grok.py --threads 8 --count 100
```

### Performance
- **~2.6 seconds per account** with 8 threads
- **~95% success rate** (DuckMail, no rate limit)
- **No browser needed** — headless, curl_cffi for TLS fingerprinting

### Files
- `grok.py` — Main script (thread pool, action ID, registration flow)
- `email_service.py` — mail.tm/DuckMail API client
- `YesCaptcha_service.py` — 2captcha Turnstile solver
- `keys/grok.txt` — SSO tokens (one per line)
- `keys/accounts.txt` — Account details (email:password:sso)

## SSO Token → OAuth Token Conversion (Device Auth Flow)

SSO cookies from GrokRegister are **NOT** valid API keys for `api.x.ai/v1`. They return `"Incorrect API key provided"`. To get OAuth tokens that work with the API gateway, use the **device auth flow** with DrissionPage to auto-authorize each SSO session.

### CRITICAL: Accounts Have No API Credits

Even after successful SSO → OAuth conversion, the accounts **have no API credits**. The x.ai API returns `402 personal-team-blocked:spending-limit` — accounts need a SuperGrok subscription or API credits. The OAuth tokens are valid (scope includes `api:access`) but the upstream rejects all requests. The gw46 gateway will show `credentials: N` in health but every API call fails with 402.

**Workarounds being investigated:**
- Check if new accounts get free trial credits after email verification
- Use Grok website API (grok.com/rest/) with SSO cookies instead of api.x.ai
- Use a different provider entirely

### Automated SSO → OAuth Conversion (Working Method)

**Script**: `sso2oauth.py` in the GrokRegister directory.

**Prerequisites:**
- DrissionPage (installed globally, import with `python -s` to avoid Hermes venv path issues)
- httpx, sqlite3 (stdlib)
- Chrome installed at `C:\Program Files\Google\Chrome\Application\chrome.exe`
- gw46 gateway DB at `~/Documents/grok46gw/grok46_accounts.db`

**Flow:**
1. Read SSO tokens from `keys/accounts.txt` (format: `email:password:sso`)
2. Start OAuth device code flow: `POST https://auth.x.ai/oauth2/device/code`
3. Launch DrissionPage with SSO cookie injected into `accounts.x.ai` domain
4. Navigate to `verification_uri_complete` (includes `user_code` in URL)
5. Click "Продолжить" (Continue) to submit the code
6. Click "Authorize" / "Разрешить" to grant device authorization
7. Poll for OAuth token: `POST https://auth.x.ai/oauth2/token` with `grant_type=device_code`
8. Store token in gw46 SQLite DB via `INSERT INTO accounts`

**Usage:**
```bash
cd ~/tmp/grok_register/grok-register
python -s sso2oauth.py --concurrent 1 --count 10
python -s sso2oauth.py --start 10 --count 50
```

**Parameters:**
- `--count N`: number of accounts to process (0 = all)
- `--start N`: start index
- `--concurrent N`: concurrency (DrissionPage crashes with >1, use always 1)

**DrissionPage Concurrency Limitation (CRITICAL):**
DrissionPage 4.1.0 raises `PageDisconnectedError` (与页面的连接已断开) when multiple `ChromiumPage` instances are created in the same process — even with `asyncio.Semaphore`. The background event handler thread crashes. **Always use `--concurrent 1`** (sequential processing). For large batches, split into chunks and restart the Python process between chunks to clear DrissionPage's internal state (~10-15 accounts per process before memory leaks cause crashes).

**Performance:**
- ~10-15 seconds per account (sequential)
- ~74 accounts processed in ~12 minutes

### gw46 Gateway KeyPool Refresh

After adding tokens to the SQLite DB externally (via `sso2oauth.py`), the gw46 gateway's **in-memory KeyPool is NOT automatically refreshed**. The gateway only reads the DB during startup (`lifespan` event) and when `/oauth/callback` or `/accounts/api-key` endpoints are called.

**To refresh after external DB writes:**
1. Kill the gateway: `taskkill /F /PID <PID>`
2. Restart: `cd ~/Documents/grok46gw && python gw46.py`
3. Verify: `curl http://127.0.0.1:20146/health` — `credentials` count should match DB total

**gw46 Gateway Integration (Manual)**
1. Start gw46: `python Documents/grok46gw/gw46.py` (port 20146)
2. Get device code: `GET /oauth/device`
3. Auth in browser with SSO cookie → authorize
4. Poll for token: `GET /oauth/device/poll`
5. Token stored in gw46 SQLite, used for API proxying

## Working Approach (v13 — Deprecated)

The custom Playwright scripts (v13, v16, v20) are **deprecated** in favor of the ready-made solutions above. They are kept for reference but the DrissionPage-based approach + gw46.py gateway is more reliable.
```
C:\Users\User\Desktop\авторег проект\grok_autoreg_v13.py
```

**v11 is NOT usable** — the file at `_SCRIPTS/grok_autoreg_v11.py` has a syntax error (broken indentation at line 80-81, `for part in msg.walk():` is not indented after `if msg.is_multipart():`). Do NOT reference v11 as a working alternative unless the file has been repaired.

**Which to use**: Always use v13. v11 exists at `_SCRIPTS/` but is non-functional.

**Key insight**: Signup happens INSIDE the device-auth OAuth flow, NOT before it.

### Flow
1. Start `grok login --device-auth` → get device URL
2. Open device URL in browser → click Continue → redirected to sign-in
3. Click "Sign up" (NOT "Login") on the sign-in page
4. Click "Sign up with email" → fill email → submit
5. Solve Turnstile (2Captcha) on sign-up page
6. Get OTP from IMAP (t-online.de) → enter code via `type()` (not `fill()`)
7. On verification page: solve Turnstile again → click submit
8. On profile form: fill name + surname + password via `fill()` + dispatch `input` event → click "Завершить регистрацию"
9. **CRITICAL**: Navigate BACK to the device auth URL → click Continue → click Authorize/Allow
10. Token appears in `~/.grok/auth.json` → add to `token_pool.json`

### Device Auth Flow Is NOT Automatic
After signup completes, the browser is NOT automatically redirected to the auth callback. You MUST:
1. Navigate back to the device auth URL
2. Click "Continue" (user is now logged in, so it shows the authorization page)
3. Click "Authorize" or "Allow"
4. ONLY THEN does the device auth CLI receive the callback and write the token

Without step 9, the account is created but the token is NEVER saved — the device auth CLI times out waiting for a callback that never arrives.

### Dependencies
- **patchright** (NOT playwright): `pip install patchright`
- **requests**: `pip install requests` (used by 2Captcha solver)
- **2Captcha** key: `[REDACTED_2CAPTCHA_KEY]` (the `bd9c67...` key is DEAD)
- **IMAP**: t-online.de via `secureimap.t-online.de:993`
- **Browser**: Uses `launch_persistent_context` with `channel="chrome"` and `user_data_dir=r"C:\Users\User\Desktop\browser_profile_grok"`
- **Emails file**: `C:\Users\User\Downloads\Telegram Desktop\working_mails.txt` (format: `email:password`)

### Usage
```bash
cd "C:\Users\User\Desktop\авторег проект"
PYTHONPATH="" .venv/Scripts/python -u "C:/Users/User/projects/_uncategorized_projects/_SCRIPTS/grok_autoreg_v11.py" 100
```
Argument = number of accounts to register.

## CRITICAL PITFALL: Do Not Fix What Is Not Broken

When Vlad says the software "worked before" and it is failing now:
1. **DO NOT modify the script** — search the ENTIRE PC for working versions first
2. Use `search_files` with `*grok*autoreg*` across `C:\Users\User`
3. The `Desktop\авторег проект\grok_autoreg.py` is NOT the working version — it is a different (broken) approach
4. Multiple versions exist: `_SCRIPTS/grok_autoreg_v4.py` through `v11.py`

## Environment Issues

### PYTHONPATH Pollution
The global PYTHONPATH points to `hermes-agent-0.18.2-latest\\venv` which has broken permissions. Always prefix with `PYTHONPATH=""` when running from a local venv.

### Python -s Flag for DrissionPage
The Hermes venv (`hermes-agent-0.18.2-latest/venv/`) has broken file permissions on Playwright packages. When running DrissionPage from the global Python, use `python -s` to skip user site-packages — this avoids the permission error on `playwright/__init__.py`. Without `-s`, DrissionPage imports fail with `PermissionError: [Errno 13]` because Python scans the Hermes venv first.

```bash
# Correct way to run DrissionPage scripts globally
python -s sso2oauth.py --count 10
```

### Venv Setup
```bash
cd "C:\Users\User\Desktop\авторег проект"
python -m venv .venv
PYTHONPATH="" .venv/Scripts/pip install patchright
```

## Token Pool
- Location: `~/.grok/token_pool.json`
- Format: `{"tokens": [{"email": ..., "access_token": ..., "refresh_token": ..., "expires_at": ...}]}`
- Tokens expire after ~6 hours, auto-refresh via `TokenPool.get_valid()`

## Fixes Applied to v11 (2026-08-13)

### IMAP: UNSEEN Filter + Socket Timeout
The original `mail.search(None, "ALL")` hangs on large mailboxes (5000+ emails). Fixed:
1. Use `mail.search(None, '(UNSEEN FROM "x.ai")')` with fallback to `mail.search(None, "UNSEEN")` — searches only new emails, not entire mailbox
2. Add `mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, timeout=30)` and `mail.socket().settimeout(30)` to prevent hanging on slow connections
3. Wrap each search in a try/except to catch socket timeouts

### Code Entry: type() Instead of fill()
`code_input.fill(vcode)` does not trigger form validation events. Fixed to use `code_input.type(code_clean, delay=80)` with dash removed (`vcode.replace("-", "")`).

### Button Selectors: Exclude OneTrust Cookie Buttons
`button:has-text('Подтвердить')` matches the OneTrust cookie consent button `onetrust-close-btn-handler`. Fixed by checking `class` attribute for `"onetrust"` and skipping those buttons.

### JS `querySelector` with `:has-text()` Is Invalid
`document.querySelector('button:has-text("...")')` throws `SyntaxError` because `:has-text()` is a Playwright pseudo-selector, NOT a valid CSS selector. Use only `page.locator("button:has-text('...')")` in Playwright context. For JS fallback, use loop with `textContent.includes()`:

### Missing "Завершить регистрацию" Button
The profile completion form uses "Завершить регистрацию" (Complete registration), not "Sign up" or "Далее". Added to the button text list in Step 11.

### Profile Form: `fill()` + `dispatchEvent('input')` for React
The profile form (name, surname, password) uses React controlled inputs. Using `Object.getOwnPropertyDescriptor(...).set` bypasses React's change detection — the form sees empty values and refuses to submit. Fix:
1. Use `locator.fill()` for all three fields
2. After each `fill()`, dispatch an `input` event via `page.evaluate("document.querySelector('input[...]')?.dispatchEvent(new Event('input', {bubbles: true}))")` 
3. Then click the submit button via Playwright locator (NOT JS `querySelector` with `:has-text()` — that's a Playwright pseudo-selector, not valid CSS)
4. Use Playwright locator: `page.locator("button:has-text('Завершить регистрацию')").first`

### Turnstile on Verification Page
The verification code page also has a Turnstile captcha. Added detection and solving in Step 10 (before clicking submit).

### Rate-Limiting Avoidance
x.ai throttles after 1-2 repeated attempts on the same email. The script skips rate-limited emails automatically. Do NOT re-run the same email repeatedly — move to a fresh one.

## Other Versions (for reference)
- `v4`–`v10`: Various iterations in `_SCRIPTS/`
- `grok_cdp_autoreg.py`: CDP-based approach (may work differently)
- `_PROJECTS/grok_autoreg.py`: Another project variant
- `Desktop\авторег проект\grok_autoreg.py`: The BROKEN version (signup-then-auth, does not work)

## v16: OAuth-After-Signup + Persistent Context (2026-08-13)

v16 is the current working approach. Key improvements over v11-v15:

### Persistent Context with Temp User Data Dir
- Uses `launch_persistent_context(user_data_dir=temp_dir, channel="chrome")` — NOT `launch()`
- Temp directory per registration (no session leakage across accounts)
- `--disable-blink-features=AutomationControlled` is REQUIRED for Turnstile to work
- **Without `channel="chrome"`**: form submission consistently fails (GET params instead of POST redirect)
- **With `channel="chrome"`**: form submission works ~50% of the time (Turnstile-dependent)

### Form Submission Pattern (v16 Working)
The profile page form submission is flaky. The pattern that works:
1. Solve Turnstile on profile page (sitekey `0x4AAAAAAAhr9JGVDZbrZOo0`)
2. Inject token via `querySelectorAll('input[name="cf-turnstile-response"]')` + string interpolation
3. Click "Завершить регистрацию" button via Playwright locator
4. Wait 3s, then force `form.submit()` via JS on the form containing password input
5. Wait 5s for redirect
6. If still on sign-up (GET params in URL), the account may still have been created — proceed to OAuth

### OAuth Timing Fix
**CRITICAL**: `grok login --oauth` times out after ~2 minutes. Signup takes 3-5 minutes (IMAP + Turnstile).
- **BEFORE v16**: OAuth was started before signup → CLI times out → callback received but no token saved
- **v16 FIX**: Device auth for signup, OAuth started AFTER signup completes → CLI is fresh, no timeout

### Flow (v16)
1. Clear auth.json (backup to .bak, restore if empty)
2. `grok login --device-auth` → get device URL
3. Browser: device URL → Continue → Sign up → Sign up with email
4. Fill email → submit → IMAP code → enter code
5. Turnstile on code page (often unsolvable, page advances anyway)
6. Profile form: fill name/surname/password → Turnstile on profile → solve
7. Click "Завершить регистрацию" → force form.submit()
8. If redirected to consent page: click "Authorize" → device auth CLI gets token
9. If device auth fails: `grok login --oauth` (fresh) → navigate to OAuth URL → consent page → Authorize
10. Extract token from auth.json (newest entry, sorted by key)

### Success Rate & Token Validation
- Form submission redirects to consent page ~50% of runs
- When it does: token is valid for the NEW account
- When it doesn't: OAuth fallback, but account may not have been created → no token
- **Always validate tokens**: `curl https://api.x.ai/v1/models -H "Authorization: Bearer TOKEN"`
- Pool tokens may show "valid" (based on expiry time) but fail API calls due to wrong account binding

### Current Working Script
```
C:\Users\User\Desktop\авторег проект\grok_autoreg_v16.py
```
Commands: `register`, `batch N`, `pool`, `proxy [port]`, `health`, `test`

### Lock File & Stale Process Cleanup

Before running ANY grok login command, cleanup stale state:

```python
import subprocess, os

# Kill stale grok processes
subprocess.run(["taskkill", "/f", "/im", "grok.exe"], capture_output=True, timeout=5)

# Remove lock files that block fresh auth
for f in [AUTH_JSON + ".lock", os.path.join(GROK_HOME, "leader.sock")]:
    if os.path.exists(f):
        os.remove(f)
```

Without this, `grok logout` and `grok login --device-auth` hang indefinitely with `TimeoutError`.

### Turnstile Timeout Parameter

The `solve_turnstile()` function now supports a `timeout` parameter (seconds, default 30). The code-page Turnstile (sitekey `0x4AAAAAAADnQ4F4U8W2nQyH`) is ALWAYS unsolvable via 2captcha — do not wait 5 minutes for it:

```python
token = await solve_turnstile(sk, page.url, timeout=30)
if token:
    # inject
else:
    print("unsolvable/timeout — continuing anyway")
```

The profile-page Turnstile (sitekey `0x4AAAAAAAhr9JGVDZbrZOo0`) IS solvable (~30s). Use the same timeout.

### React SPA: No HTML Forms (v19-v20 Finding)

The x.ai signup page (`/sign-up`) is a React SPA that does NOT contain `<form>` elements. The signup is done through JavaScript API calls (likely Zitadel API). This means:

- `form.submit()` from JS does NOTHING useful (navigates to GET params URL)
- `page.keyboard.press("Enter")` also does NOTHING (no form to submit)
- The button click triggers a React event handler that makes an API call
- Even with valid Turnstile tokens injected into `cf-turnstile-response` hidden inputs, the React event handler may not check that input

**As of v20, the form submission is the unsolved bottleneck.** The Turnstile is solved, the token is injected, but the server rejects the submission ~90% of the time. Flow degrades to:

1. Signup form stuck → account NOT created
2. Device auth CLI waiting → no callback → timeout
3. OAuth fallback → logs into old account → invalid token (403)

**v20 discovery**: `cf_clearance` cookie auto-solves on real Chrome (`channel="chrome"`). The cookie can be extracted and used for direct API calls. However, ALL x.ai API endpoints (`/api/v2/authn/verification_code`, `/api/v2/users/human`, etc.) return HTML (Next.js page) instead of JSON — the API is not directly accessible behind the Next.js frontend, even with a valid `cf_clearance` cookie.

### Known Failure Mode: API Token Validation

Even when `token_pool.json` shows tokens as "valid" (based on `expires_at`), they may return 403 `{"code":"unauthenticated:bad-credentials","error":"The OAuth2 access token could not be validated."}`. This happens when the OAuth flow authorized the WRONG account (existing account instead of newly created one). Always validate with:

```bash
curl -s https://api.x.ai/v1/models -H "Authorization: Bearer TOKEN" | head -c 200
```

### channel="chrome" Is Required

Without `channel="chrome"` in `launch_persistent_context`, the headless Chromium browser's Turnstile widget always shows a challenge (never auto-solves). With `channel="chrome"` (real Chrome), the widget auto-solves and sets `cf_clearance` cookie — no 2captcha needed for the WAF bypass. The `cf_clearance` cookie (`cf_clearance = MeLLMwuSWSia66h6...`) is set automatically after page load on real Chrome. However, the Turnstile widget on the profile form STILL needs manual solving (2captcha) because it's a separate challenge.

Always use:

```python
browser = await pwr.chromium.launch_persistent_context(
    headless=False,
    channel="chrome",  # REQUIRED — Turnstile auto-solves WAF with real Chrome
    args=["--window-size=1200,900", "--disable-blink-features=AutomationControlled", "--no-sandbox"]
)
```

## Reference Files
- references/imap-pattern.md — IMAP verification code extraction with UNSEEN filter
- references/react-form-filling.md — React controlled form filling with fill() + input event
- references/device-auth-completion.md — Device auth flow completion after signup
- references/oauth-fallback-token.md — OAuth fallback pattern for token retrieval
- references/oauth-account-mismatch.md — OAuth authorizes wrong account (token bound to old account)
- references/oauth-timing-account-binding.md — OAuth CLI timeout + account binding fix (v16)
- references/turnstile-json-escape.md — Turnstile token JSON escaping
- references/form-submission-pattern.md — Profile form submission pattern (v16 working)
- references/profile-turnstile-timing.md — Profile Turnstile iframe detection timing fix
- references/duckmail-api.md — DuckMail API reference (no auth, 19 domains, no rate limit)
- references/curl-cffi-grpc-web.md — curl_cffi + gRPC-web registration approach (PRIMARY working method)
- references/playwright-stealth-setup.md — Playwright stealth import pattern + Cloudflare bypass (2026-08-14)
- references/bpproxy-pool.md — bpproxy residential proxy pool location + usage (2026-08-14)
- references/tonline-email-pool.md — t-online.de email pool (17,893 accounts) + IMAP settings (2026-08-14)
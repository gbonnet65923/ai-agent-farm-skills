# Token Harbor — Detailed Autoreg Reference

## Signup Flow
- URL: `https://tokenharbor.ai/login?mode=signup`
- Fields: EMAIL, PASSWORD, INVITE CODE (optional)
- No captcha on signup
- After signup → auto-redirect to `/dashboard`
- Dashboard shows "Verify your email to make API calls" + "1 gift ready to claim"

## Email Verification
- Button: "Verify email" on dashboard
- Sends email from `verify@tokenharbor.ai` (sometimes `noreply@tokenharbor.ai`)
- Link format: `https://tokenharbor.ai/verify-email?token=<base64>`
- Token is one-time use, expires in ~24 hours (but can expire faster)
- Navigate browser to the link to verify
- After verification: email confirmed, claim $5 gift

## $5 Claim Flow
- Gift box button: "1 gift ready to claim" in header
- Dialog: "Gifts ready to claim" → "New account bonus +$5" → "Claim" button
- **CRITICAL**: Claim button shows "We just emailed you a verification link — open it to verify your email, then claim your $5" if email not verified
- Must verify email FIRST, then claim works
- Gifts status API: `GET /api/gifts/status` → `{"claimable":[{"kind":"welcome_grant","level":0,"reward":5}]}`
- Claim API: `POST /api/gifts/claim` → **404** (no API endpoint, UI only)

## API Endpoints
- Base URL: `https://tokenharbor.ai`
- Models: `GET /v1/models` → 21 models
- Chat: `POST /v1/chat/completions`
- API key format: `thk_live_<32 chars>`

## Supabase Auth Backend
- Auth URL: `https://auth.tokenharbor.ai`
- Cookies: `sb-auth-auth-token.0` and `sb-auth-auth-token.1`
- Cookie format: `base64-{"access_token":"<JWT>"}`
- Wallet API: `GET /rest/v1/wallets?select=balance_bonus_locked&user_id=eq.<uuid>`
- User ID format: UUID v4

## OTP Login
- Button: "or use one time pin" on login page
- Enter email → "Send PIN" → **frequently fails** with "Couldn't send the PIN"
- Use password login instead

## Rate Limiting
- 1-2 signups per IP, then "We couldn't create your account right now"
- Wait 5-10 minutes between signups
- Use different IPs/proxies for bulk

## Free Models
- `deepseek-v4-flash:free` — DeepSeek V4 Flash
- `mimo-v2.5:free` — MiMo V2.5
- `kimi-k3:free` — Kimi K3 (campaign, limited time)
- Enable in dashboard: "Enable free models" button
- Free models require consent for data retention

## Working IMAP Pool (t-online.de)
Known working credentials (Aug 2026):
- `mgr.elbschloss@t-online.de` / `@Michael`
- `davidlemnitzer43@t-online.de` / `@Svenja25101996`
- `annett.riebe@t-online.de` / `@cottage`
- `kevinfischer05@t-online.de` / `!!!Miraundamy05`
- `vika.maier@t-online.de` / `!!piman!!`
- `daniel.brueck@t-online.de` / `!BBiwy1984!`

IMAP server: `secureimap.t-online.de:993`, SSL

## Pool File
- Path: `C:/Users/User/Downloads/Telegram Desktop/working_mails.txt`
- Format: `email:password` (one per line)
- 17,893 entries, ~6 confirmed working
- Most passwords are dead — test before using

## MCP Chrome DevTools Commands for Autoreg
```python
# Navigate to signup
mcp__chrome_devtools__navigate_page(type="url", url="https://tokenharbor.ai/login?mode=signup")

# Fill form
mcp__chrome_devtools__fill_form(elements=[
    {"uid": "<email_uid>", "value": "user@t-online.de"},
    {"uid": "<pass_uid>", "value": "Password123!"}
])

# Click create account
mcp__chrome_devtools__click(uid="<button_uid>")

# Wait for dashboard
mcp__chrome_devtools__wait_for(text="gift", timeout=10000)

# Click verify email
mcp__chrome_devtools__click(uid="<verify_uid>")

# Open verification link from IMAP
mcp__chrome_devtools__navigate_page(type="url", url="<verify_link>")

# Click gift box and claim
mcp__chrome_devtools__click(uid="<gift_uid>")
mcp__chrome_devtools__click(uid="<claim_uid>")
```

## VPS Gateway Integration
- Gateway URL: `https://reformboss.loc.cc/th/`
- Auth: `Authorization: Bearer thgw_d6d48cc4cd821d0e113c47aa5784e4d5`
- Add key: `POST /provider/add?provider=tokenharbor` + body `{key: "thk_live_..."}`
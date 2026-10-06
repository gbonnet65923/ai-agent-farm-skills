# cf_clearance Cookie — Cloudflare WAF Bypass for x.ai

## Discovery (v20, 2026-08-13)

When using `channel="chrome"` (real Chrome via Playwright), the Cloudflare Turnstile challenge on `accounts.x.ai/sign-up` auto-solves WITHOUT 2captcha. The `cf_clearance` cookie is set automatically after page load.

**Cookie details:**
```
Name: cf_clearance
Domain: .x.ai
Value: MeLLMwuSWSia66h6YiouO4tSvXyrcfXDKMrqS4ifanM-178662...
```

## How to Extract

```python
# After page load
cookies = await page.context.cookies()
cf_clearance = ""
for c in cookies:
    if c['name'] == 'cf_clearance':
        cf_clearance = c['value']
        break
```

## Using for API Requests

```python
import requests

cookies = {"cf_clearance": cf_clearance}
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Origin": "https://accounts.x.ai",
    "Referer": "https://accounts.x.ai/sign-up",
}

resp = requests.post(
    "https://accounts.x.ai/api/v2/authn/verification_code",
    json={"email": "user@example.com"},
    headers=headers,
    cookies=cookies
)
```

## Limitation

Even with `cf_clearance`, ALL x.ai API endpoints return HTML (Next.js page) instead of JSON. The API is not directly accessible behind the Next.js frontend — the frontend catches all API routes and serves the React page.

**Tested endpoints (all return HTML with 200):**
- `POST /api/v2/authn/verification_code`
- `POST /api/v2/users/human`
- `POST /api/v2/users`
- `POST /api/v2/register`
- `POST /api/v2/authn`
- `POST /api/signup`
- `POST /api/register`
- `POST /api/v2/signup`
- `POST /zitadel/v2/users/human`
- `POST /api/v2beta/users/human`

**Without cf_clearance**, these endpoints return 403 (Cloudflare WAF).

## The Turnstile Widget Distinction

There are TWO Turnstile levels on x.ai:
1. **Cloudflare WAF Turnstile** — auto-solved by real Chrome, sets `cf_clearance` cookie. This bypasses the WAF but doesn't help with the React form.
2. **React form Turnstile** — the `cf-turnstile-response` widget on the profile form. This needs 2captcha. The token is injected into the hidden input, but the React event handler may not check it.

The `cf_clearance` solves #1 (WAF bypass) but #2 (form submission) remains unsolved.
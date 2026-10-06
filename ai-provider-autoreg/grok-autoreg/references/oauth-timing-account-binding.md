# OAuth Timing & Account Binding Issue

## The Problem
`grok login --oauth` starts a local HTTP server that listens for a callback. The CLI times out after ~2 minutes. If the signup flow takes 3-5 minutes (IMAP code retrieval + Turnstile solving), the CLI times out BEFORE the callback arrives.

## Symptom
```
[12] Callback!
[12] ❌ No token in auth.json
```

The callback was received by the browser (redirected to `http://127.0.0.1:PORT/callback`), but the CLI had already timed out and exited. The token is never saved to auth.json.

## Fix (v16)
Start OAuth AFTER signup, not before:
1. Use device auth (`grok login --device-auth`) for the signup flow
2. After signup completes (form submitted, account created), start `grok login --oauth`
3. Navigate browser to the OAuth URL
4. Browser is already logged in → consent page is shown immediately
5. Click "Authorize" → callback arrives within seconds
6. CLI saves token to auth.json

## Account Binding
Even with the timing fix, the OAuth flow authorizes the account that the BROWSER is logged into. If the signup created the account and the browser is logged in, the token is for the new account. If the signup failed (form didn't submit), the browser is NOT logged in, and the OAuth page shows the sign-in page.

## Token Validation
Always validate tokens after extraction:
```python
import urllib.request, json
req = urllib.request.Request('https://api.x.ai/v1/models', 
    headers={'Authorization': f'Bearer {token}'})
try:
    with urllib.request.urlopen(req, timeout=10) as r:
        print(f"Valid: {r.status}")
except Exception as e:
    print(f"Invalid: {e}")
```

A 403 response means the token is bound to the wrong account (OAuth authorized the old account from the previous session).
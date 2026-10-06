# OAuth Token Account Mismatch

## Problem
After signup via device auth flow, the OAuth fallback (grok login --oauth) retrieves a token that appears valid but fails API calls with `bad-credentials`.

## Root Cause
The OAuth flow authorizes the WRONG account:
1. The signup creates a new account in the browser
2. grok logout clears the CLI's auth.json
3. grok login --oauth starts a fresh OAuth session
4. The browser navigates to the OAuth URL
5. The browser's session is for the OLD account (from persistent profile), not the new one
6. The OAuth authorizes the old account and saves the token with the old account's refresh_token
7. The script stores the token with the new email but the OLD account's credentials

## Detection
All tokens in the pool have the same refresh_token even though they have different emails.

Check with:
```bash
python -c "import json; p=json.load(open(r'C:\Users\User\.grok\token_pool.json')); [print(t.get('refresh_token','')[:20]) for t in p['tokens']]"
```

If all tokens have the same refresh_token prefix, they are all bound to the same account.

## Fix
Use v13's fresh browser context (browser.new_context() not launch_persistent_context). This ensures the browser is logged in to the NEW account after signup, so the OAuth fallback authorizes the correct account.

## Verification
After registration, verify the token with a test API call:
```bash
curl -s http://localhost:8318/v1/chat/completions -X POST -H "Content-Type: application/json" -d '{"model":"grok-4.5","messages":[{"role":"user","content":"test"}],"max_tokens":5}'
```
If this returns `bad-credentials`, the token is bound to the wrong account.